# -*- coding: utf-8 -*-
"""Inyecta los textos legales definitivos en el pie de la web (nave/index.html).

    python herramientas/legales.py <ruta-al-html-de-textos-legales>

Toma los apartados 1 (aviso legal), 2 (política de privacidad) y 3 (política de cookies) del documento
validado por la asesoría y los coloca, adaptados al estilo del pie, dentro de <details id="textos-legales">.
Idempotente: la primera vez sustituye el bloque antiguo; después reemplaza lo que haya entre los marcadores
<!-- legales:inicio --> y <!-- legales:fin -->. El apartado 4 (textos del formulario) no se publica: ya está
aplicado en el propio formulario.
"""
import io, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGINA = os.path.join(RAIZ, "nave", "index.html")

SECCIONES = [("aviso-legal", "1. Aviso legal", "Aviso legal"),
             ("privacidad", "2. Política de privacidad", "Política de privacidad"),
             ("cookies", "3. Política de cookies", "Política de cookies")]


def seccion(doc, titulo, siguiente):
    i = doc.index("<h2>" + titulo)
    j = doc.index("<h2>" + siguiente) if siguiente else doc.index("</div>", doc.rfind("<p class=\"pie\"", i))
    s = doc[i:j]
    s = s[s.index("</h2>") + 5:]                       # quitar el h2 del documento
    s = re.sub(r"</?div[^>]*>", "", s)                 # envoltorios del documento
    s = s.replace("<h3>", "<h4>").replace("</h3>", "</h4>")
    s = re.sub(r"<mark>([^<]*)</mark>", r"\1", s)      # no debe quedar ninguna marca; si queda, se ve como texto
    s = re.sub(r'<p class="pie">', '<p class="legal-fecha">', s)
    s = re.sub(r'<p class="aviso">', '<p class="legal-aviso">', s)
    s = re.sub(r"<table>", '<div class="tabla"><table>', s)
    s = re.sub(r"</table>", "</table></div>", s)
    s = re.sub(r'<th style="[^"]*">', "<th>", s)
    return s.strip()


def main():
    fuente = os.path.abspath(sys.argv[1])
    doc = io.open(fuente, encoding="utf-8").read()
    if "<mark>" in doc[doc.index("<h2>1. Aviso legal"):doc.index("<h2>4.")]:
        raise SystemExit("El documento aún tiene huecos [ASÍ] en los apartados 1-3: rellénalos antes de publicar.")
    partes = []
    for k, (ancla, titulo, corto) in enumerate(SECCIONES):
        sig = SECCIONES[k + 1][1] if k + 1 < len(SECCIONES) else "4. Textos del formulario"
        partes.append(f'        <div id="{ancla}" class="legal-texto">\n          <h3>{corto}</h3>\n{seccion(doc, titulo, sig)}\n        </div>')
    bloque = "<!-- legales:inicio -->\n      <div class=\"legal-in\">\n" + "\n".join(partes) + "\n      </div>\n      <!-- legales:fin -->"

    html = io.open(PAGINA, encoding="utf-8").read()
    if "<!-- legales:inicio -->" in html:
        html = re.sub(r"<!-- legales:inicio -->.*?<!-- legales:fin -->", lambda m: bloque, html, flags=re.S)
    else:
        i = html.index('<div class="legal-in">')
        j = html.index("</details>", i)
        html = html[:i] + bloque + "\n    " + html[j:]
    if "/* legales */" not in html:
        css = """
  /* legales */
  .legal-in { grid-template-columns: 1fr; gap: 2.5rem; }
  .legal-texto { max-width: 78ch; }
  .legal-texto h4 { font-family: var(--f-cuerpo); font-size: .95rem; font-weight: 600; color: var(--nieve); margin: 1.2rem 0 .4rem; }
  .legal-texto p, .legal-texto li { color: var(--nieve-2); margin: 0 0 .6rem; }
  .legal-texto ul, .legal-texto ol { padding-left: 1.2rem; margin: 0 0 .6rem; }
  .legal-texto b { color: var(--nieve); font-weight: 600; }
  .legal-texto .tabla { overflow-x: auto; margin: 0 0 .8rem; }
  .legal-texto table { width: 100%; min-width: 36rem; border-collapse: collapse; font-size: .85rem; }
  .legal-texto th, .legal-texto td { text-align: left; vertical-align: top; padding: .45rem .5rem; border-bottom: 1px solid var(--marino-3); color: var(--nieve-2); }
  .legal-texto th { color: var(--nieve); font-weight: 600; }
  .legal-texto .legal-aviso { border-left: 2px solid var(--naranja); padding-left: .8rem; }
  .legal-texto .legal-fecha { font-size: .8rem; color: var(--nieve-2); margin-top: .8rem; }
"""
        k = html.rfind("</style>")
        html = html[:k] + css + html[k:]
    io.open(PAGINA, "w", encoding="utf-8", newline="\n").write(html)
    print("textos legales inyectados en", PAGINA, "| tamaño", os.path.getsize(PAGINA) // 1024, "KB")


if __name__ == "__main__":
    main()
