# -*- coding: utf-8 -*-
"""Captura una página entera con Chrome headless y la trocea para poder leerla.

    python herramientas/captura.py <ruta-html> <prefijo-salida>

Genera <prefijo>-desktop-N.png (1440 px de ancho, trozos de 1600 px) y <prefijo>-mobile-N.png
(hojas de 4 columnas de 390x1600). El móvil se renderiza dentro de un iframe de 390 px porque Chrome
headless impone un ancho mínimo de ventana. Imprime las rutas generadas.
"""
import glob, io, os, subprocess, sys, tempfile
from PIL import Image

CHROME = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"


def chrome(url, salida, ancho, alto, perfil):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
                    f"--user-data-dir={perfil}", "--virtual-time-budget=9000",
                    f"--window-size={ancho},{alto}", f"--screenshot={salida}", url],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)


def recortar_final(im):
    w, h = im.size
    px = im.load()
    fondo = px[w // 2, h - 1]
    y = h - 1
    while y > 200:
        if any(abs(px[x, y][0] - fondo[0]) + abs(px[x, y][1] - fondo[1]) + abs(px[x, y][2] - fondo[2]) > 18
               for x in range(0, w, max(1, w // 40))):
            break
        y -= 1
    return im.crop((0, 0, w, min(h, y + 60)))


def main():
    entrada = os.path.abspath(sys.argv[1])
    prefijo = os.path.abspath(sys.argv[2])
    os.makedirs(os.path.dirname(prefijo), exist_ok=True)
    for f in glob.glob(prefijo + "-desktop-*.png") + glob.glob(prefijo + "-mobile-*.png"):
        os.remove(f)
    carpeta = os.path.dirname(entrada)
    nombre = os.path.basename(entrada)
    url = "file:///" + entrada.replace("\\", "/")
    salidas = []
    with tempfile.TemporaryDirectory() as perfil:
        # Escritorio
        d = prefijo + "-desktop.png"
        chrome(url, d, 1440, 16000, perfil)
        im = recortar_final(Image.open(d).convert("RGB"))
        w, h = im.size
        for i in range(0, h, 1600):
            f = f"{prefijo}-desktop-{i // 1600 + 1}.png"
            im.crop((0, i, w, min(h, i + 1600))).save(f)
            salidas.append(f)
        print("desktop", w, h)
        # Móvil: iframe de 390 px en dos pasadas de 15000 px
        partes = []
        for paso in (0, 1):
            ifr = os.path.join(carpeta, f"_captura390_{paso}.html")
            io.open(ifr, "w", encoding="utf-8").write(
                '<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:#888;overflow:hidden}'
                f'iframe{{border:0;display:block;margin-top:-{paso * 15000}px}}</style></head><body>'
                f'<iframe src="{nombre}" width="390" height="30000"></iframe></body></html>')
            s = f"{prefijo}-mobile-p{paso}.png"
            chrome("file:///" + ifr.replace("\\", "/"), s, 600, 15000, perfil)
            partes.append(Image.open(s).convert("RGB").crop((0, 0, 390, 15000)))
            os.remove(ifr)
            os.remove(s)
        m = Image.new("RGB", (390, 30000))
        m.paste(partes[0], (0, 0))
        m.paste(partes[1], (0, 15000))
        m = recortar_final(m)
        w, h = m.size
        trozos = [m.crop((0, i, w, min(h, i + 1600))) for i in range(0, h, 1600)]
        for s in range(0, len(trozos), 4):
            hoja = Image.new("RGB", (4 * (w + 20), 1600), "#888")
            for j, t in enumerate(trozos[s:s + 4]):
                hoja.paste(t, (j * (w + 20), 0))
            f = f"{prefijo}-mobile-{s // 4 + 1}.png"
            hoja.save(f)
            salidas.append(f)
        print("mobile", w, h)
    print("\n".join(salidas))


if __name__ == "__main__":
    main()
