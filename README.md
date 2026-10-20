# Twinsol Decor · web nueva

Propuesta de modernización de [twinsoldecor.com](https://www.twinsoldecor.com/) (hoy en Wix, diseño de 2012).
Web estática: un solo `index.html` con todo el CSS y JS dentro, y las fotos en `img/`. Sin dependencias, sin build.

## Ver la propuesta

- Abrir `index.html` en el navegador funciona tal cual (doble clic).
- Publicada en GitHub Pages (rama `main`). Cada push a `main` la actualiza en un minuto.
- **Índice para el cliente, con las cinco propuestas: https://yjaviy.github.io/twinsol-web/propuestas/**

| Propuesta | URL | Línea |
|---|---|---|
| Matriz (recomendada) | https://yjaviy.github.io/twinsol-web/matriz/ | La más cercana a la web del grupo: marino + naranja, foto recortada por el arco del logotipo |
| Arco | https://yjaviy.github.io/twinsol-web/arco/ | Mismo parentesco, composición clara y editorial con una gran curva por sección |
| Catálogo | https://yjaviy.github.io/twinsol-web/catalogo/ | Catálogo técnico: retícula, tablas de servicios y sistemas |
| Nave | https://yjaviy.github.io/twinsol-web/nave/ | La más visual: foto a sangre, portada oscura, titulares grandes |
| Planimetría | https://yjaviy.github.io/twinsol-web/ | Identidad independiente (anterior a la petición de parentesco con el grupo) |

El cliente pidió que la web se inspire en la de la matriz del grupo sin copiarla: las cuatro primeras comparten paleta y tono con ella, con hex, tipografías, textos, composición y motivo gráfico (el arco del logotipo de Twinsol) propios.

## Qué hay dentro

| Fichero | Qué es |
|---|---|
| `index.html` | Propuesta Planimetría: la página completa (cabecera, hero, servicios, sistemas, proceso, sectores, galería, empresa, calidad, contacto). |
| `img/` | 31 fotos reales de obra rescatadas del Wix actual, optimizadas (máx. 1600 px, ~5 MB en total), y los sellos de calidad. |
| `matriz/`, `arco/`, `catalogo/`, `nave/` | Las otras cuatro propuestas, cada una en su `index.html`, compartiendo `img/`. |
| `propuestas/` | Página índice con miniaturas para que el cliente compare. |
| `docs/` | Certificado UNE-EN ISO 14001:2015 de la empresa (ICDQ, n.º 1455/26, vigente hasta el 23/03/2029), enlazado desde el sello ICDQ y la cifra ISO 14001 de cada propuesta; se abre en pestaña nueva. |
| `favicon.svg` | Icono de pestaña (arco naranja del logo). |
| `.nojekyll` | Para que GitHub Pages sirva los ficheros tal cual. |

Todo el texto sale de la web actual; no hay cifras ni clientes inventados. Hay una contradicción que conviene confirmar con el cliente: los textos dicen "en proceso de certificación ISO 9001 / OHSAS 18001" pero los sellos AENOR e ICDQ de su web muestran ISO 9001 e ISO 14001:2015.

## Pasar a producción: hosting de Arsys (decidido el 20/10/2026)

La empresa ya paga en Arsys un **Hosting Avanzado Linux** para `twinsoldecor.com` (Apache + PHP, sFTP, SSL incluido) junto con el dominio y el correo, así que la web definitiva (`nave/`) se sirve desde ahí: sin coste nuevo, sin servidor a nombre del desarrollador y con el formulario entregando el correo desde el propio hosting. Ese hosting aloja también el buzón `info@`: **no se cancela nunca**.

```bash
python herramientas/empaquetar_arsys.py --http
```

Genera `dist-arsys/` (ignorado por git) con la web como raíz del dominio: `index.html` (rutas sin `../`, canónica `https://www.twinsoldecor.com/`, sin `noindex`), `img/`, `fonts/` (solo las de Nave), `docs/`, iconos, `formulario.php`, `.htaccess` (301 de las diez URL antiguas del Wix a su sección, caché, cabeceras, bloqueo de ficheros internos), `404.html`, `sitemap.xml` y `robots.txt`. Sin `--http` el `.htaccess` fuerza además `https://www.`: solo cuando Arsys haya emitido el certificado, si no la web entra en bucle.

`formulario.php` (fuente en `herramientas/arsys/`) recibe el formulario por POST, valida, descarta robots (campo trampa `web` y tiempo mínimo de 3 s con el campo `t`), limita a 5 envíos por hora y dirección con un contador anónimo en `.envios/` (hash con sal, nunca la IP en claro) y manda el correo a `info@twinsoldecor.com` con `Reply-To` del visitante. No guarda copia de los envíos ni incluye la IP en el correo. La web lo llama por `fetch`; en GitHub Pages, `localhost` o `file:` el envío se simula.

Subida por sFTP (credenciales en `.notas/arsys.env`, fuera de git: `ARSYS_HOST` = IP del hosting 217.76.130.116, porque `ftp.twinsoldecor.com` no existe mientras el DNS esté en Wix; `ARSYS_USER`, `ARSYS_PASS`, `ARSYS_DIR` y, tras la primera conexión, `ARSYS_FINGERPRINT`). Antes de subir, `--listar` muestra lo que hay en la carpeta remota sin tocar nada:

```bash
python herramientas/empaquetar_arsys.py --listar
```


```bash
python herramientas/empaquetar_arsys.py --http --subir
```

Para ver la web ya subida al hosting mientras el dominio siga en Wix (la IP a secas da 403: el servidor es compartido y elige la web por el nombre) se usa un subdominio de previsualización, `nueva.twinsoldecor.com`: en el panel de Arsys, "Gestión de subdominios", crear `nueva` apuntando a la carpeta `html` (la misma de la web); y en Wix, en los registros DNS del dominio, añadir un registro A `nueva` con valor `217.76.130.116`. En unos minutos `http://nueva.twinsoldecor.com` muestra la copia de Arsys (sin https, es solo para ver) y el `.htaccess` le pone `X-Robots-Tag: noindex` para que no se indexe. El truco del fichero `hosts` no sirve aquí: el Wix actual manda HSTS de un año para `www.twinsoldecor.com`, así que el navegador forzaría https contra el hosting sin certificado. Al terminar el cambio, borrar el subdominio en Arsys.

Orden del día del cambio (antes del 28/11/2026, que es cuando vence el Wix):

1. Mirar por sFTP qué hay en la raíz del hosting y guardarlo aparte si tiene algo.
2. Subir `dist-arsys/` y probar la web en la URL de previsualización que da Arsys (o editando el fichero `hosts`): página, formulario real (que llegue el correo a `info@`), redirecciones antiguas, 404.
   Comprobaciones del hosting: `GET /img/` debe dar 403 (si da 500, Arsys no admite `Options` en `.htaccess`: quitar la línea `Options -Indexes`); subir un `ip.php` temporal con `<?php echo $_SERVER['REMOTE_ADDR'];` y visitarlo desde dos redes (oficina y móvil): si sale la misma IP hay un proxy delante y el límite por dirección del formulario contaría a todos como uno (habría que leer la última IP de `X-Forwarded-For` en `formulario.php`); borrar `ip.php` después.
3. DNS. Los nameservers del dominio son hoy los de Wix (`ns6/ns7.wixdns.net`): toda la zona, incluido el correo, vive en Wix. La zona que Arsys tiene preparada ("Entradas DNS" del panel) ya está completa: `twinsoldecor.com` y `www` apuntan al hosting (A 217.76.130.116), MX `mx.serviciodecorreo.es`, SPF, DKIM, DMARC, autodiscover. Así que el cambio es: (a) en Wix, exportar o anotar todos los registros de la zona actual y comparar con la de Arsys (la viva usa MX `smtp-02.servidoresdns.net`; copiar a Arsys cualquier TXT de verificación u otro registro que falte); (b) en el panel de Arsys, sección Dominios > "Servidores DNS", pasar el dominio a los servidores DNS de Arsys. Con eso la web y el correo quedan en Arsys; propaga en unas horas. No tocar nada del correo por separado.
4. Activar el certificado SSL en el panel; cuando esté emitido, volver a empaquetar sin `--http` y subir el `.htaccess`.
   Después `curl -sI https://www.twinsoldecor.com/` debe dar 200: si da 301 sobre sí misma, el SSL termina en un proxy que no manda `X-Forwarded-Proto`; volver al `.htaccess` de `--http` y ajustar la condición.
5. Comprobar `https://www.twinsoldecor.com`, `http://twinsoldecor.com` (debe redirigir) y dos URL antiguas; dar de alta la propiedad en Search Console y enviar `sitemap.xml`.
6. Cuando venza el Wix no hay que hacer nada más (la renovación ya está cancelada).

## Previsualización en GitHub Pages (herramientas/produccion.py)

Las dos finalistas (`index.html` = Planimetría, `nave/index.html` = Nave) ya están preparadas con:

- **Fuentes propias** en `fonts/` (subconjunto latin, 396 KB en total): nada se carga desde Google.
- **Metadatos** para buscadores y para compartir (canónica, Open Graph con `img/og.jpg` de 1200×630, Twitter card), icono para iOS y datos estructurados de la empresa (JSON-LD con NIF, dirección y teléfono).
- **Páginas de salto** para las URL antiguas del Wix (`galeria`, `quienes-somos`, `pavimentos-sin-juntas`, `project-2`, `project-3`, `project-4`, `impermeabilizaciones`, `politica-de-calidad`, `responsabilidadmedioambiental`, `seguridad`), que llevan a la sección correspondiente de la web nueva. Las dos finalistas comparten los mismos nombres de ancla.
- `404.html` propia.

Mientras la web esté en previsualización se regenera con:

```bash
python herramientas/produccion.py --base https://yjaviy.github.io/twinsol-web/
```

La opción `--produccion --dominio` (sitemap, robots y `CNAME` para servir desde GitHub Pages) queda como alternativa por si algún día el hosting de Arsys dejara de existir; la vía decidida es la del apartado anterior.

## Si el cliente prefiere seguir en Wix

No se puede pegar este HTML en Wix. Habría que reconstruir el diseño a mano en el editor de Wix (o Wix Studio) usando esta página como maqueta: mismas fotos (`img/`), mismos textos, misma paleta y las fuentes (están en Google Fonts, que Wix incluye). El elemento "Insertar HTML" de Wix mete un iframe por bloque: no sirve para toda la página.
