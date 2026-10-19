# -*- coding: utf-8 -*-
"""Prepara la web para producción. Idempotente: se puede volver a ejecutar.

    python herramientas/produccion.py --base https://yjaviy.github.io/twinsol-web/
    python herramientas/produccion.py --base https://www.twinsoldecor.com/ --produccion --dominio www.twinsoldecor.com

Qué hace, sobre las dos finalistas (index.html = Planimetría, nave/index.html = Nave):
  1. Fuentes propias: descarga de Google Fonts los woff2 (subconjunto latin) y los sirve desde fonts/,
     sustituyendo los <link> a fonts.googleapis.com. Sin transferencia a Google y menos latencia.
  2. Metadatos para compartir y buscadores: canonical, og:url/og:image absolutos, imagen 1200x630,
     twitter:card, apple-touch-icon, preload de la foto del hero.
  3. Datos estructurados (JSON-LD, Organization) con los datos reales de la empresa.
  4. Páginas de salto para las URL antiguas del Wix (galeria, quienes-somos, project-2...), 404.html e iconos.
  5. Con --produccion: sitemap.xml, robots.txt y CNAME; sin él, la web sigue en noindex.
"""
import argparse, io, json, os, re, sys, urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"

EMPRESA = {
    "nombre": "TWINSOL DECOR, S.L.",
    "nif": "B19310671",
    "calle": "Calle Alcolea, 39",
    "cp": "19174",
    "localidad": "Torrejón del Rey",
    "provincia": "Guadalajara",
    "telefono": "+34648710497",
    "telefono2": "+34616052200",
    "email": "info@twinsoldecor.com",
    "descripcion": "Especialistas en pavimentos continuos industriales: soleras de hormigón sin juntas reforzadas con fibra de acero y alta planimetría, revestimientos continuos y restauración de soleras.",
}

# URL antiguas del Wix (sin barra final) -> ancla de la web nueva
REDIRECCIONES = {
    "galeria": "obras",
    "pavimentos-sin-juntas": "hormigon",
    "quienes-somos": "empresa",
    "project-2": "revestimientos",          # Revestimientos continuos
    "impermeabilizaciones": "revestimientos",   # la sublínea desaparece en la web definitiva
    "project-3": "servicios",               # Pavimentos artísticos: línea suprimida por el cliente
    "project-4": "restauracion",            # Restauración de soleras (Twin Cure)
    "politica-de-calidad": "calidad",
    "responsabilidadmedioambiental": "medio-ambiente",   # sección propia en la web definitiva (Nave)
    "seguridad": "calidad",
}

PAGINAS = [
    {"fichero": "index.html", "clave": "planimetria", "prefijo": "", "og": "img/og.jpg", "ruta": ""},
    {"fichero": os.path.join("nave", "index.html"), "clave": "nave", "prefijo": "../", "og": "img/og.jpg", "ruta": "nave/"},
]


def leer(p):
    return io.open(p, encoding="utf-8").read()


def escribir(p, s):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


def descargar(url, binario=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        datos = r.read()
    return datos if binario else datos.decode("utf-8")


# ---------- 1. Fuentes propias ----------

def fuentes_propias(pagina):
    html = leer(os.path.join(RAIZ, pagina["fichero"]))
    m = re.search(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com/css2\?[^"]+)">', html)
    css_local = os.path.join(RAIZ, "fonts", pagina["clave"] + ".css")
    if not m:
        return html, os.path.exists(css_local)
    url = m.group(1).replace("&amp;", "&")
    css = descargar(url)
    # Nos quedamos solo con los bloques /* latin */ (cubre español: acentos, ñ, €, «», guiones)
    bloques = re.findall(r"/\* (\w[\w-]*) \*/\s*(@font-face \{[^}]+\})", css)
    salida = ["/* Fuentes servidas desde el propio dominio. Generado por herramientas/produccion.py; subconjunto latin. */"]
    n = 0
    for subconjunto, bloque in bloques:
        if subconjunto != "latin":
            continue
        fam = re.search(r"font-family: '([^']+)'", bloque).group(1)
        estilo = re.search(r"font-style: (\w+)", bloque).group(1)
        peso = re.search(r"font-weight: ([\d ]+)", bloque).group(1).strip().replace(" ", "-")
        ancho = re.search(r"font-stretch: ([\d% ]+)", bloque)
        ancho = ("-w" + ancho.group(1).strip().replace("% ", "-").replace("%", "")) if ancho else ""
        src = re.search(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", bloque).group(1)
        nombre = re.sub(r"[^a-z0-9]+", "-", fam.lower()).strip("-") + f"-{estilo}-{peso}{ancho}.woff2"
        destino = os.path.join(RAIZ, "fonts", nombre)
        if not os.path.exists(destino):
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            io.open(destino, "wb").write(descargar(src, binario=True))
        bloque_local = bloque.replace(src, "./" + nombre)
        if "font-display" not in bloque_local:
            bloque_local = bloque_local.replace("font-style:", "font-display: swap;\n  font-style:", 1)
        salida.append(bloque_local)
        n += 1
    escribir(css_local, "\n".join(salida) + "\n")
    # Sustituir los tres <link> (dos preconnect + hoja) por la hoja local
    html = re.sub(r'<link rel="preconnect" href="https://fonts\.g(?:oogleapis|static)\.com"(?: crossorigin)?>\s*', "", html)
    html = html.replace(m.group(0), f'<link rel="stylesheet" href="{pagina["prefijo"]}fonts/{pagina["clave"]}.css">')
    print(f"  fuentes: {n} caras latin -> fonts/{pagina['clave']}.css")
    return html, True


# ---------- 2 y 3. Cabecera y JSON-LD ----------

def bloque_cabecera(pagina, base, produccion):
    pre = pagina["prefijo"]
    # En producción la propuesta elegida vive en la raíz; en previsualización cada una tiene su URL
    url = base if produccion else base + pagina["ruta"]
    html_hero = leer(os.path.join(RAIZ, pagina["fichero"]))
    og_desc = "" if 'property="og:description"' in html_hero else f'<meta property="og:description" content="{EMPRESA["descripcion"]}">'

    hero = re.search(r'<img[^>]*fetchpriority="high"[^>]*src="([^"]+)"', html_hero) or re.search(r'<img[^>]*src="([^"]+)"[^>]*fetchpriority="high"', html_hero)
    preload = f'<link rel="preload" as="image" href="{hero.group(1)}" fetchpriority="high">' if hero else ""
    robots = "" if produccion else '<meta name="robots" content="noindex, nofollow">'
    return f"""<!-- produccion:inicio -->
<link rel="canonical" href="{url}">
{robots}
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="TWINSOL DECOR">
{og_desc}
<meta property="og:locale" content="es_ES">
<meta property="og:image" content="{base}{pagina['og']}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Nave industrial con solera de hormigón pulido, TWINSOL DECOR">
<meta name="twitter:card" content="summary_large_image">
<link rel="apple-touch-icon" href="{pre}apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="512x512" href="{pre}icon-512.png">
<meta name="theme-color" content="#14181D">
{preload}
<!-- produccion:fin -->"""


def bloque_jsonld(base):
    e = EMPRESA
    datos = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "TWINSOL DECOR",
        "legalName": e["nombre"],
        "vatID": "ES" + e["nif"],
        "taxID": e["nif"],
        "url": base,
        "logo": base + "icon-512.png",
        "image": base + "img/og.jpg",
        "description": e["descripcion"],
        "email": e["email"],
        "telephone": e["telefono"],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": e["calle"],
            "postalCode": e["cp"],
            "addressLocality": e["localidad"],
            "addressRegion": e["provincia"],
            "addressCountry": "ES",
        },
        "areaServed": ["ES", "Europa Central", "Sudamérica", "Oriente Medio"],
        "contactPoint": [{
            "@type": "ContactPoint",
            "contactType": "sales",
            "telephone": e["telefono"],
            "email": e["email"],
            "availableLanguage": ["es"],
        }],
        "knowsAbout": ["pavimentos industriales", "soleras de hormigón sin juntas", "hormigón reforzado con fibra de acero", "alta planimetría", "revestimientos continuos", "restauración de soleras"],
    }
    salto = (
        "<script>\n"
        "// Llegada con ancla (enlaces antiguos, redirecciones): salto instantáneo a la sección, sin recorrer toda la página.\n"
        "(function(){var h=location.hash&&location.hash.slice(1);if(!h)return;var e=document.getElementById(h);if(!e)return;"
        "var r=document.documentElement,p=r.style.scrollBehavior;r.style.scrollBehavior='auto';"
        "function ir(){e.scrollIntoView({block:'start'});}ir();window.addEventListener('load',function(){ir();setTimeout(function(){r.style.scrollBehavior=p;},50);});})();\n"
        "</script>"
    )
    return "<!-- produccion:jsonld -->\n" + salto + "\n<script type=\"application/ld+json\">\n" + json.dumps(datos, ensure_ascii=False, indent=1) + "\n</script>\n<!-- produccion:jsonld:fin -->"


def aplicar_cabecera(html, pagina, base, produccion):
    # Quitar el noindex antiguo (y su comentario) y el og:image/og:type relativos: los pone el bloque nuevo
    html = re.sub(r'<!-- Quitar la l[^\n]*-->\n', "", html)
    html = re.sub(r'<!-- Propuesta de dise[^\n]*-->\n', "", html)
    html = re.sub(r'<meta name="robots" content="noindex, nofollow">\n', "", html)
    html = re.sub(r'<meta property="og:image" content="[^"]*">\n', "", html)
    html = re.sub(r'<!-- produccion:inicio -->.*?<!-- produccion:fin -->\n?', "", html, flags=re.S)
    html = html.replace("</head>", bloque_cabecera(pagina, base, produccion) + "\n</head>", 1)
    html = re.sub(r'<!-- produccion:jsonld -->.*?<!-- produccion:jsonld:fin -->\n?', "", html, flags=re.S)
    html = html.replace("</body>", bloque_jsonld(base) + "\n</body>", 1)
    return html


# ---------- 4. Imágenes: OG e iconos ----------

def imagen_og():
    from PIL import Image, ImageDraw, ImageFont
    destino = os.path.join(RAIZ, "img", "og.jpg")
    im = Image.open(os.path.join(RAIZ, "img", "hero-nave.jpg")).convert("RGB")
    # recorte 1200x630 centrado un poco hacia abajo (la solera)
    W, H = 1200, 630
    esc = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * esc), round(im.height * esc)), Image.LANCZOS)
    x = (im.width - W) // 2
    y = min(im.height - H, int((im.height - H) * 0.7))
    im = im.crop((x, y, x + W, y + H))
    # velo oscuro degradado por la izquierda para el texto
    velo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(velo)
    for i in range(W):
        a = int(max(0, 215 - i * 0.32))
        d.line([(i, 0), (i, H)], fill=(20, 24, 29, a))
    im = Image.alpha_composite(im.convert("RGBA"), velo)
    d = ImageDraw.Draw(im)
    fuentes = "C:/Windows/Fonts/"
    f1 = ImageFont.truetype(fuentes + "ARIALNB.TTF", 112)
    f2 = ImageFont.truetype(fuentes + "ARIALN.TTF", 44)
    f3 = ImageFont.truetype(fuentes + "arial.ttf", 30)
    # arco naranja (guiño al logotipo)
    d.arc([(70, 150), (690, 420)], start=200, end=330, fill=(232, 100, 27, 255), width=6)
    d.text((70, 250), "TWINSOL", font=f1, fill=(255, 255, 255, 255))
    d.text((70, 365), "DECOR", font=f2, fill=(232, 100, 27, 255))
    d.text((70, 455), "Pavimentos continuos industriales", font=f3, fill=(235, 238, 242, 255))
    d.text((70, 495), "Soleras sin juntas  ·  Alta planimetría  ·  Revestimientos", font=f3, fill=(200, 206, 214, 255))
    im.convert("RGB").save(destino, "JPEG", quality=86, optimize=True, progressive=True)
    print("  og.jpg:", os.path.getsize(destino) // 1024, "KB")


def iconos():
    import fitz
    svg = os.path.join(RAIZ, "favicon.svg")
    for nombre, px in (("apple-touch-icon.png", 180), ("icon-512.png", 512)):
        doc = fitz.open(svg)
        pag = doc[0]
        esc = px / max(pag.rect.width, pag.rect.height)
        pix = pag.get_pixmap(matrix=fitz.Matrix(esc, esc), alpha=False)
        pix.save(os.path.join(RAIZ, nombre))
    print("  iconos: apple-touch-icon.png 180, icon-512.png 512")


# ---------- 5. Páginas de salto y 404 ----------

PLANTILLA_SALTO = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo} · TWINSOL DECOR</title>
<meta http-equiv="refresh" content="0; url=./#{ancla}">
<link rel="canonical" href="{base}">
<meta name="robots" content="noindex">
<script>location.replace("./#{ancla}");</script>
<style>body{{margin:0;min-height:100vh;display:grid;place-items:center;font:17px/1.5 system-ui,"Segoe UI",Roboto,Arial,sans-serif;background:#14181D;color:#EDEFF2}}a{{color:#F07A35}}p{{margin:0;padding:24px;text-align:center}}</style>
</head>
<body>
<p>Esta página ha cambiado de sitio. <a href="./#{ancla}">Ir a {titulo}</a></p>
</body>
</html>
"""

TITULOS = {
    "obras": "la galería de obras", "hormigon": "pavimentos de hormigón sin juntas", "empresa": "quiénes somos",
    "revestimientos": "revestimientos continuos", "impermeabilizaciones": "impermeabilizaciones poliméricas",
    "artisticos": "pavimentos artísticos", "restauracion": "restauración de soleras", "calidad": "calidad y seguridad",
}


def saltos(base):
    for ruta, ancla in REDIRECCIONES.items():
        escribir(os.path.join(RAIZ, ruta + ".html"), PLANTILLA_SALTO.format(titulo=TITULOS[ancla].capitalize(), ancla=ancla, base=base))
    print(f"  saltos: {len(REDIRECCIONES)} páginas (URL antiguas del Wix)")


PAGINA_404 = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Página no encontrada · TWINSOL DECOR</title>
<meta name="robots" content="noindex">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<style>
body{margin:0;min-height:100vh;display:grid;place-items:center;font:17px/1.55 system-ui,"Segoe UI",Roboto,Arial,sans-serif;background:#14181D;color:#EDEFF2}
main{padding:32px 24px;max-width:36rem}
p.c{font:12px/1 ui-monospace,Consolas,monospace;letter-spacing:.14em;text-transform:uppercase;color:#F07A35;margin:0 0 14px}
h1{font-size:clamp(1.8rem,5vw,2.6rem);line-height:1.1;margin:0 0 14px;font-weight:600}
p{margin:0 0 12px;color:#C9CFD6}
a.btn{display:inline-block;margin-top:10px;padding:12px 18px;background:#E8641B;color:#14181D;text-decoration:none;font-weight:700}
a.btn:hover,a.btn:focus-visible{background:#F07A35}
svg{display:block;width:120px;height:30px;margin-bottom:22px}
</style>
</head>
<body>
<main>
<svg viewBox="0 0 120 30" aria-hidden="true"><path d="M3 27 C 28 4, 82 2, 117 16" fill="none" stroke="#E8641B" stroke-width="2.4" stroke-linecap="round"/></svg>
<p class="c">Error 404</p>
<h1>Esta página no existe</h1>
<p>Puede que la dirección haya cambiado con la web nueva. Todo el contenido está en la página principal: servicios, sistemas, obras, empresa y contacto.</p>
<a class="btn" id="inicio" href="/">Ir a la página principal</a>
</main>
<script>
// La web vive en la raíz del dominio; mientras esté en GitHub Pages, cuelga de /twinsol-web/.
var p=location.pathname.indexOf("/twinsol-web/")===0?"/twinsol-web/":"/";
document.getElementById("inicio").href=p;
</script>
</body>
</html>
"""


def pagina_404():
    escribir(os.path.join(RAIZ, "404.html"), PAGINA_404)
    print("  404.html")


# ---------- 6. Producción: sitemap, robots, CNAME ----------

def produccion_ficheros(base, dominio):
    escribir(os.path.join(RAIZ, "sitemap.xml"), f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{base}</loc><changefreq>monthly</changefreq><priority>1.0</priority></url>
</urlset>
""")
    escribir(os.path.join(RAIZ, "robots.txt"), f"User-agent: *\nAllow: /\nDisallow: /propuestas/\nDisallow: /matriz/\nDisallow: /arco/\nDisallow: /catalogo/\nDisallow: /nave/\n\nSitemap: {base}sitemap.xml\n")
    if dominio:
        escribir(os.path.join(RAIZ, "CNAME"), dominio + "\n")
    print("  sitemap.xml, robots.txt" + (", CNAME" if dominio else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="URL pública con barra final, p. ej. https://www.twinsoldecor.com/")
    ap.add_argument("--produccion", action="store_true", help="quita el noindex y genera sitemap, robots y CNAME")
    ap.add_argument("--dominio", default="", help="dominio para el fichero CNAME (solo con --produccion)")
    args = ap.parse_args()
    base = args.base if args.base.endswith("/") else args.base + "/"

    print("Imágenes e iconos"); imagen_og(); iconos()
    for pagina in PAGINAS:
        print("Página", pagina["fichero"])
        html, _ = fuentes_propias(pagina)
        html = aplicar_cabecera(html, pagina, base, args.produccion)
        escribir(os.path.join(RAIZ, pagina["fichero"]), html)
    print("Rutas"); saltos(base); pagina_404()
    if args.produccion:
        produccion_ficheros(base, args.dominio)
    print("Hecho. Modo:", "PRODUCCIÓN (indexable)" if args.produccion else "previsualización (noindex)")


if __name__ == "__main__":
    main()
