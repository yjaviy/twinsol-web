<?php
// Formulario de contacto de www.twinsoldecor.com: entrega cada envío por correo al buzón de la empresa.
// Se ejecuta en el propio hosting de Arsys. No guarda copia de los envíos: solo un contador anónimo por
// dirección (hash con sal, una hora) para limitar el abuso. La IP no se incluye en el correo.
declare(strict_types=1);

$DESTINO          = 'info@twinsoldecor.com';
$REMITENTE        = 'info@twinsoldecor.com';   // debe ser una dirección del propio dominio para que Arsys lo acepte
$ASUNTO           = 'Solicitud de presupuesto desde la web';
$MAX_POR_HORA     = 5;
$SEGUNDOS_MINIMOS = 3;
$TELEFONO         = '+34 648 710 497';

umask(077);                                    // ficheros del contador solo legibles por este usuario
date_default_timezone_set('Europe/Madrid');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');

$quiereJson = (isset($_SERVER['HTTP_X_REQUESTED_WITH']) && $_SERVER['HTTP_X_REQUESTED_WITH'] === 'fetch')
    || (isset($_SERVER['HTTP_ACCEPT']) && strpos($_SERVER['HTTP_ACCEPT'], 'application/json') !== false);

function responder(bool $ok, string $mensaje, int $estado = 200): void
{
    global $quiereJson;
    http_response_code($estado);
    if ($quiereJson) {
        header('Content-Type: application/json; charset=UTF-8');
        echo json_encode(['ok' => $ok, 'mensaje' => $mensaje], JSON_UNESCAPED_UNICODE);
        exit;
    }
    // Sin JavaScript: página mínima con el resultado y vuelta a la web
    $titulo = $ok ? 'Solicitud recibida' : 'No se ha podido enviar';
    header('Content-Type: text/html; charset=UTF-8');
    echo '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        . '<meta name="robots" content="noindex"><title>' . $titulo . ' · TWINSOL DECOR</title>'
        . '<style>body{margin:0;min-height:100vh;display:grid;place-items:center;font:17px/1.55 system-ui,"Segoe UI",Roboto,Arial,sans-serif;background:#14181D;color:#EDEFF2}'
        . 'main{padding:32px 24px;max-width:36rem}h1{font-size:1.8rem;margin:0 0 12px}p{color:#C9CFD6}a{color:#F07A35}</style></head><body><main>'
        . '<h1>' . $titulo . '</h1><p>' . htmlspecialchars($mensaje, ENT_QUOTES, 'UTF-8') . '</p>'
        . '<p><a href="/#contacto">Volver a la web</a></p></main></body></html>';
    exit;
}

// Los campos de una línea pierden también los saltos de línea: nada de lo que vaya a una cabecera puede llevarlos
function campo(string $nombre, int $max, bool $multilinea = false): string
{
    $v = isset($_POST[$nombre]) && is_string($_POST[$nombre]) ? $_POST[$nombre] : '';
    $v = trim(str_replace($multilinea ? ["\r", "\0"] : ["\r", "\n", "\0"], '', $v));
    return function_exists('mb_substr') ? mb_substr($v, 0, $max, 'UTF-8') : substr($v, 0, $max);
}

// Contador de envíos de la última hora para una dirección (hash). Con el fichero bloqueado de principio a fin
// para que varios envíos simultáneos no lean todos "cero". Devuelve false si se supera el límite.
function contar(string $fich, int $ahora, int $max, bool $sumar): bool
{
    $fh = @fopen($fich, 'c+');
    if ($fh === false || !flock($fh, LOCK_EX)) {
        return true;                            // sin contador posible: no bloquear a nadie
    }
    $marcas = [];
    foreach (explode("\n", (string) stream_get_contents($fh)) as $l) {
        if ((int) $l > $ahora - 3600) {
            $marcas[] = (int) $l;
        }
    }
    $cabe = count($marcas) < $max;
    if ($sumar) {
        if ($cabe) {
            $marcas[] = $ahora;
        }
    } else {
        $k = array_search($ahora, $marcas, true);  // deshacer el apunte de un envío que no salió
        if ($k !== false) {
            array_splice($marcas, $k, 1);
        }
    }
    ftruncate($fh, 0);
    rewind($fh);
    fwrite($fh, implode("\n", $marcas) . "\n");
    fflush($fh);
    flock($fh, LOCK_UN);
    fclose($fh);
    return $cabe;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    responder(false, 'Método no permitido.', 405);
}

// Trampa para robots: un campo oculto que las personas no ven ni rellenan. Si llega con contenido, se
// responde como si todo hubiera ido bien y no se envía nada.
if (campo('web', 10) !== '') {
    responder(true, 'Solicitud recibida.');
}

// Segundos entre cargar la página y enviar, medidos por el JavaScript de la web (no la hora del visitante, que
// puede ir desajustada). Si no viene, se omite la comprobación para no bloquear a quien navega sin JavaScript.
$t = campo('t', 20);
if ($t !== '' && (int) $t < $SEGUNDOS_MINIMOS) {
    responder(false, 'El envío ha sido demasiado rápido. Inténtelo de nuevo.', 400);
}

$nombre   = campo('nombre', 120);
$empresa  = campo('empresa', 120);
$email    = campo('email', 200);
$telefono = campo('telefono', 40);
$linea    = campo('linea', 40);
$mensaje  = campo('mensaje', 4000, true);
$lectura  = isset($_POST['lectura_proteccion_datos']);

// filter_var admite partes locales entrecomilladas con barras y saltos; ningún correo real los lleva y en
// una cabecera Reply-To permitirían colar un Bcc
if ($nombre === '' || $mensaje === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)
    || strpbrk($email, " \t\r\n\"\\") !== false) {
    responder(false, 'Revise los campos: nombre, correo electrónico válido y mensaje son obligatorios.', 422);
}
if (!$lectura) {
    responder(false, 'Para enviar su solicitud debe confirmar que ha leído la información sobre protección de datos.', 422);
}

// Límite de envíos por dirección: contador anónimo (hash con sal) que caduca en una hora
$dir = __DIR__ . '/.envios';
if (!is_dir($dir)) {
    @mkdir($dir, 0700, true);
    @file_put_contents($dir . '/.htaccess', "<IfModule mod_authz_core.c>\nRequire all denied\n</IfModule>\n<IfModule !mod_authz_core.c>\nDeny from all\n</IfModule>\n");
}
if (!is_dir($dir) || !is_writable($dir)) {
    $dir = sys_get_temp_dir();
}
$sal = @file_get_contents($dir . '/.sal-twinsol');
if ($sal === false || $sal === '') {
    $sal = bin2hex(random_bytes(16));
    @file_put_contents($dir . '/.sal-twinsol', $sal);
}
$ahora = time();
// Si Arsys pusiera un proxy delante, REMOTE_ADDR sería el del proxy para todos (comprobar al desplegar; ver README)
$fich  = $dir . '/tw-' . hash('sha256', $sal . ($_SERVER['REMOTE_ADDR'] ?? ''));
if (!contar($fich, $ahora, $MAX_POR_HORA, true)) {
    responder(false, 'Ha enviado varias solicitudes en poco tiempo. Inténtelo más tarde o llame al ' . $TELEFONO . '.', 429);
}
// Limpieza ocasional de contadores caducados
if (random_int(1, 20) === 1) {
    foreach (glob($dir . '/tw-*') ?: [] as $f) {
        if (@filemtime($f) < $ahora - 3600) {
            @unlink($f);
        }
    }
}

$lineas = [
    'hormigon'       => 'Pavimentos de hormigón sin juntas de corte y alta tolerancia',
    'revestimientos' => 'Revestimientos continuos',
    'restauracion'   => 'Restauración de soleras',
];
$lineaTexto = $lineas[$linea] ?? ($linea !== '' ? $linea : 'sin especificar');

$cuerpo = implode("\r\n", [
    'Nueva solicitud desde www.twinsoldecor.com',
    '',
    'Nombre: ' . $nombre,
    'Empresa: ' . ($empresa !== '' ? $empresa : '-'),
    'Correo: ' . $email,
    'Teléfono: ' . ($telefono !== '' ? $telefono : '-'),
    'Línea de servicio: ' . $lineaTexto,
    '',
    'Mensaje:',
    $mensaje,
    '',
    'Casilla de lectura de la información sobre protección de datos: marcada.',
    'Fecha: ' . date('d/m/Y H:i'),
]);

// Asunto codificado (UTF-8); mb_encode_mimeheader lo pliega en líneas de 75 como manda la RFC 2047
$asuntoTexto = $ASUNTO . ' · ' . $nombre;
$asunto      = function_exists('mb_encode_mimeheader')
    ? mb_encode_mimeheader($asuntoTexto, 'UTF-8', 'B', "\r\n")
    : '=?UTF-8?B?' . base64_encode($asuntoTexto) . '?=';
$cabeceras = 'From: =?UTF-8?B?' . base64_encode('Web TWINSOL DECOR') . '?= <' . $REMITENTE . ">\r\n"
    . 'Reply-To: ' . $email . "\r\n"
    . "MIME-Version: 1.0\r\n"
    . "Content-Type: text/plain; charset=UTF-8\r\n"
    . "Content-Transfer-Encoding: 8bit\r\n"
    . "X-Mailer: formulario-twinsol";

$enviado = @mail($DESTINO, $asunto, $cuerpo, $cabeceras, '-f' . $REMITENTE);
if (!$enviado) {
    $enviado = @mail($DESTINO, $asunto, $cuerpo, $cabeceras);
}
if (!$enviado) {
    contar($fich, $ahora, $MAX_POR_HORA, false);   // un envío que no salió no cuenta
    responder(false, 'No se ha podido enviar el mensaje. Escríbanos a ' . $DESTINO . ' o llame al ' . $TELEFONO . '.', 500);
}
responder(true, 'Solicitud recibida. Le responderemos en el correo indicado.');
