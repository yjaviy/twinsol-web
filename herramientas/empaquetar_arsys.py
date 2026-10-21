# -*- coding: utf-8 -*-
"""Empaqueta la web definitiva (Nave) para el hosting de Arsys y, si se pide, la sube por sFTP.

    python herramientas/empaquetar_arsys.py            -> dist-arsys/ (con redirección a https)
    python herramientas/empaquetar_arsys.py --http     -> sin forzar https (mientras el SSL de Arsys no esté emitido)
    python herramientas/empaquetar_arsys.py --subir    -> además sube dist-arsys/ por sFTP (credenciales en .notas/arsys.env)

Qué hace: toma nave/index.html, lo deja como raíz del dominio (rutas sin ../, URL canónica www.twinsoldecor.com,
sin noindex), copia img/ fonts/ docs/ e iconos, añade formulario.php, .htaccess (301 de las URL antiguas del Wix,
https+www, caché, cabeceras), 404.html, sitemap.xml y robots.txt.
"""
import argparse, io, os, re, shutil, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from produccion import REDIRECCIONES, PAGINA_404  # noqa: E402

BASE = "https://www.twinsoldecor.com/"
PREVIA = "https://yjaviy.github.io/twinsol-web/"


def leer(p):
    return io.open(p, encoding="utf-8").read()


def escribir(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


def pagina(forzar_https):
    html = leer(os.path.join(RAIZ, "nave", "index.html"))
    for a, b in (('../img/', 'img/'), ('../docs/', 'docs/'), ('../fonts/', 'fonts/'),
                 ('"../favicon.svg"', '"favicon.svg"'), ('"../apple-touch-icon.png"', '"apple-touch-icon.png"'),
                 ('"../icon-512.png"', '"icon-512.png"')):
        html = html.replace(a, b)
    html = html.replace(PREVIA + "nave/", BASE).replace(PREVIA, BASE)
    html = re.sub(r'<meta name="robots" content="noindex, nofollow">\n?', "", html)
    if "../" in html:
        restos = sorted(set(re.findall(r'[^"\s]*\.\./[^"\s]*', html)))
        raise SystemExit("Quedan rutas relativas sin convertir: " + ", ".join(restos[:10]))
    return html


def htaccess(forzar_https):
    # QSD: la query (utm, etc.) no puede ir detrás del #, el navegador la tomaría como parte del ancla
    reglas = "\n".join(f"RewriteRule ^{ruta}/?$ /#{ancla} [R=301,L,NE,QSD]" for ruta, ancla in REDIRECCIONES.items())
    https = """# HTTPS y www (requiere el certificado SSL de Arsys emitido)
RewriteCond %{HTTPS} !=on
RewriteCond %{HTTP:X-Forwarded-Proto} !=https
RewriteRule ^ https://www.twinsoldecor.com%{REQUEST_URI} [R=301,L,NE]
RewriteCond %{HTTP_HOST} !^www\\.twinsoldecor\\.com$ [NC]
RewriteRule ^ https://www.twinsoldecor.com%{REQUEST_URI} [R=301,L,NE]
""" if forzar_https else "# (La redirección a https y www se activa con el empaquetador sin --http una vez emitido el SSL)\n"
    return f"""# www.twinsoldecor.com · generado por herramientas/empaquetar_arsys.py
Options -Indexes
AddDefaultCharset UTF-8
DirectoryIndex index.html

<IfModule mod_rewrite.c>
RewriteEngine On
# La carpeta del contador del formulario nunca se sirve
RewriteRule ^\\.envios(/|$) - [F,L]
{https}
# URL antiguas del Wix -> secciones de la web nueva (redirección permanente)
{reglas}
</IfModule>

ErrorDocument 404 /404.html

<IfModule mod_expires.c>
ExpiresActive On
ExpiresByType image/jpeg "access plus 1 year"
ExpiresByType image/png "access plus 1 year"
ExpiresByType image/svg+xml "access plus 1 year"
ExpiresByType font/woff2 "access plus 1 year"
ExpiresByType text/css "access plus 1 month"
ExpiresByType application/pdf "access plus 1 month"
ExpiresByType text/html "access plus 0 seconds"
</IfModule>

# El subdominio de previsualización (nueva.twinsoldecor.com) no debe indexarse
<IfModule mod_setenvif.c>
SetEnvIfNoCase Host ^nueva\\. PREVIA
</IfModule>

<IfModule mod_headers.c>
Header set X-Robots-Tag "noindex, nofollow" env=PREVIA
Header set X-Content-Type-Options "nosniff"
Header set Referrer-Policy "strict-origin-when-cross-origin"
Header set X-Frame-Options "SAMEORIGIN"
<FilesMatch "\\.(woff2)$">
Header set Access-Control-Allow-Origin "https://www.twinsoldecor.com"
</FilesMatch>
</IfModule>

<IfModule mod_deflate.c>
AddOutputFilterByType DEFLATE text/html text/css application/javascript application/json image/svg+xml
</IfModule>

<IfModule mod_mime.c>
AddType font/woff2 .woff2
AddType image/svg+xml .svg
</IfModule>

# Ficheros internos: nunca servirlos
<FilesMatch "^\\.(htaccess|sal-twinsol)$">
<IfModule mod_authz_core.c>
Require all denied
</IfModule>
<IfModule !mod_authz_core.c>
Deny from all
</IfModule>
</FilesMatch>
"""


def copiar_arbol(origen, destino, patron=None):
    if os.path.isdir(destino):
        shutil.rmtree(destino)
    shutil.copytree(origen, destino)


def empaquetar(dest, forzar_https):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    escribir(os.path.join(dest, "index.html"), pagina(forzar_https))
    for carpeta in ("img", "fonts", "docs"):
        copiar_arbol(os.path.join(RAIZ, carpeta), os.path.join(dest, carpeta))
    for f in ("favicon.svg", "apple-touch-icon.png", "icon-512.png"):
        shutil.copy2(os.path.join(RAIZ, f), os.path.join(dest, f))
    # fuentes: solo las de Nave
    for f in os.listdir(os.path.join(dest, "fonts")):
        if f.endswith(".css") and f != "nave.css":
            os.remove(os.path.join(dest, "fonts", f))
    usadas = set(re.findall(r"url\(\./([^)]+)\)", leer(os.path.join(dest, "fonts", "nave.css"))))
    for f in os.listdir(os.path.join(dest, "fonts")):
        if f.endswith(".woff2") and f not in usadas:
            os.remove(os.path.join(dest, "fonts", f))
    shutil.copy2(os.path.join(RAIZ, "herramientas", "arsys", "formulario.php"), os.path.join(dest, "formulario.php"))
    escribir(os.path.join(dest, ".htaccess"), htaccess(forzar_https))
    escribir(os.path.join(dest, "404.html"), re.sub(r"\n<script>.*?</script>", "", PAGINA_404, flags=re.S))
    escribir(os.path.join(dest, "sitemap.xml"), f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc>{BASE}</loc><changefreq>monthly</changefreq><priority>1.0</priority></url>\n</urlset>\n')
    escribir(os.path.join(dest, "robots.txt"), f"User-agent: *\nAllow: /\nDisallow: /formulario.php\n\nSitemap: {BASE}sitemap.xml\n")
    total = 0
    for base, _, ficheros in os.walk(dest):
        for f in ficheros:
            total += os.path.getsize(os.path.join(base, f))
    print(f"Paquete en {dest}: {total // 1024} KB, https {'forzado' if forzar_https else 'NO forzado'}")


def conectar(carpeta=None):
    """Abre la sesión sFTP con los datos de .notas/arsys.env. Devuelve (transport, sftp, carpeta remota).
    `carpeta` sustituye a ARSYS_DIR (p. ej. /html/nueva para el subdominio de previsualización)."""
    import hashlib, base64
    import paramiko
    env = {}
    ruta_env = os.path.join(RAIZ, ".notas", "arsys.env")
    if not os.path.exists(ruta_env):
        raise SystemExit("Falta .notas/arsys.env con ARSYS_HOST, ARSYS_USER, ARSYS_PASS y ARSYS_DIR (fuera de git).")
    for linea in leer(ruta_env).splitlines():
        if "=" in linea and not linea.startswith("#"):
            k, v = linea.split("=", 1)
            env[k.strip()] = v.strip()
    host, user, pw = env.get("ARSYS_HOST", ""), env.get("ARSYS_USER", ""), env.get("ARSYS_PASS", "")
    if not host or not user or not pw:
        raise SystemExit("En .notas/arsys.env faltan ARSYS_HOST, ARSYS_USER o ARSYS_PASS.")
    remoto = (carpeta or env.get("ARSYS_DIR", "/")).rstrip("/") or "/"
    t = paramiko.Transport((host, int(env.get("ARSYS_PORT", "22"))))
    t.connect(username=user, password=pw)
    # Huella del servidor: la primera vez se apunta en arsys.env; si después cambia, se para
    huella = "SHA256:" + base64.b64encode(hashlib.sha256(t.get_remote_server_key().asbytes()).digest()).decode().rstrip("=")
    esperada = env.get("ARSYS_FINGERPRINT", "")
    if esperada and esperada != huella:
        t.close()
        raise SystemExit(f"La huella del servidor ({huella}) no coincide con ARSYS_FINGERPRINT: no se sube nada.")
    if not esperada:
        print(f"Huella del servidor sFTP: {huella}  (añade ARSYS_FINGERPRINT={huella} a .notas/arsys.env)")
    return t, paramiko.SFTPClient.from_transport(t), remoto


def listar(carpeta=None):
    """Muestra qué hay en la carpeta remota (y un nivel por debajo) sin tocar nada."""
    import stat
    t, sftp, remoto = conectar(carpeta)
    print(f"Contenido de {remoto}:")
    for e in sorted(sftp.listdir_attr(remoto), key=lambda e: e.filename):
        tipo = "d" if stat.S_ISDIR(e.st_mode) else "-"
        print(f"  {tipo} {e.st_size:>9}  {e.filename}")
        if tipo == "d":
            try:
                hijos = sorted(sftp.listdir(remoto.rstrip('/') + "/" + e.filename))
            except IOError:
                hijos = ["(sin acceso)"]
            print("      " + ", ".join(hijos[:15]) + (" ..." if len(hijos) > 15 else "") if hijos else "      (vacía)")
    sftp.close(); t.close()


def subir(dest, carpeta=None):
    t, sftp, remoto = conectar(carpeta)
    n = 0
    for base, carpetas, ficheros in os.walk(dest):
        rel = os.path.relpath(base, dest).replace("\\", "/")
        rdir = remoto if rel == "." else remoto + "/" + rel
        try:
            sftp.stat(rdir)
        except IOError:
            sftp.mkdir(rdir)
        for f in ficheros:
            sftp.put(os.path.join(base, f), rdir + "/" + f)
            n += 1
    sftp.close(); t.close()
    print(f"Subidos {n} ficheros a {remoto}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--http", action="store_true", help="no forzar https (hasta que Arsys emita el SSL)")
    ap.add_argument("--listar", action="store_true", help="solo listar la carpeta remota por sFTP, sin empaquetar ni subir")
    ap.add_argument("--subir", action="store_true", help="subir por sFTP con .notas/arsys.env")
    ap.add_argument("--dir", default=None, help="carpeta remota en lugar de ARSYS_DIR (p. ej. /html/nueva para la previsualización)")
    ap.add_argument("--dest", default=os.path.join(RAIZ, "dist-arsys"))
    a = ap.parse_args()
    if a.listar:
        listar(a.dir)
        return
    empaquetar(a.dest, not a.http)
    if a.subir:
        subir(a.dest, a.dir)


if __name__ == "__main__":
    main()
