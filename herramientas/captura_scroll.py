# -*- coding: utf-8 -*-
"""Captura una página como la ve una persona: a tamaño de ventana y en varias posiciones de scroll.

    python herramientas/captura_scroll.py <ruta-html> <prefijo-salida> [1440x900,1024x768,390x844]

A diferencia de captura.py (que fotografía la página entera de una vez), aquí hay scroll real, así que
se ven los elementos pegajosos (position: sticky) y lo que tapan. Genera <prefijo>-<ancho>-<n>.png,
cada una con una banda arriba que indica tamaño de ventana y posición de scroll. La página se carga
dentro de un iframe del tamaño pedido (Chrome headless no baja de ~500 px de ancho de ventana).
"""
import glob, io, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw

CHROME = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
PASO = 0.85  # fracción de la altura de la ventana que se avanza entre capturas


def chrome(url, salida, ancho, alto, perfil=None):
    """Captura `url` en `salida`. Chrome vuelve enseguida (se desprende del proceso) y escribe el PNG unos
    segundos después, así que se espera a que el fichero exista y deje de crecer. Perfil nuevo por captura:
    si dos lanzamientos comparten perfil, el segundo se pega al primero y no captura nada."""
    import shutil, tempfile, time
    propio = tempfile.mkdtemp(prefix="chrome-captura-")
    if os.path.exists(salida):
        os.remove(salida)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox", "--no-first-run",
                    "--disable-extensions", "--allow-file-access-from-files", f"--user-data-dir={propio}",
                    "--virtual-time-budget=8000", f"--window-size={ancho},{alto}", f"--screenshot={salida}", url],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    t0, previo = time.time(), -1
    while time.time() - t0 < 120:
        if os.path.exists(salida) and os.path.getsize(salida) > 1000:
            actual = os.path.getsize(salida)
            if actual == previo:
                break
            previo = actual
        time.sleep(0.5)
    else:
        raise SystemExit(f"Chrome no ha escrito {salida} en 120 s")
    time.sleep(0.3)
    shutil.rmtree(propio, ignore_errors=True)


def altura_total(nombre, carpeta, ancho, perfil):
    """Mide la altura de la página a ese ancho (la escribe el propio iframe en el título de la página)."""
    ifr = os.path.join(carpeta, "_medida.html")
    io.open(ifr, "w", encoding="utf-8").write(
        '<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:#fff;font:bold 40px monospace}'
        'iframe{border:0;display:block;position:absolute;left:-9999px}</style></head><body><div id="h">?</div>'
        f'<iframe id="f" src="{nombre}" width="{ancho}" height="800"></iframe>'
        '<script>document.getElementById("f").addEventListener("load",function(){setTimeout(function(){'
        'var d=this.contentDocument.documentElement;document.getElementById("h").textContent=d.scrollHeight;}.bind(this),1500);});</script>'
        '</body></html>')
    s = os.path.join(carpeta, "_medida.png")
    chrome("file:///" + ifr.replace("\\", "/"), s, max(600, ancho), 200, perfil)
    im = Image.open(s).convert("L")
    os.remove(ifr); os.remove(s)
    # No se hace OCR: se devuelve una estimación generosa y las capturas vacías del final se descartan por color
    return im


def main():
    entrada = os.path.abspath(sys.argv[1])
    prefijo = os.path.abspath(sys.argv[2])
    tamanos = (sys.argv[3] if len(sys.argv) > 3 else "1440x900,1024x768,390x844").split(",")
    os.makedirs(os.path.dirname(prefijo), exist_ok=True)
    for tam in tamanos:
        for f in glob.glob(prefijo + f"-{tam.lower()}-*.png"):
            os.remove(f)
    carpeta = os.path.dirname(entrada)
    nombre = os.path.basename(entrada)
    salidas = []
    with tempfile.TemporaryDirectory() as perfil:
        for tam in tamanos:
            ancho, alto = (int(v) for v in tam.lower().split("x"))
            y, n, vacias = 0, 0, 0
            while y < 40000 and vacias < 2:
                ifr = os.path.join(carpeta, f"_scroll_{ancho}.html")
                io.open(ifr, "w", encoding="utf-8").write(
                    '<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:#666;overflow:hidden}'
                    'iframe{border:0;display:block}</style></head><body>'
                    f'<iframe id="f" src="{nombre}" width="{ancho}" height="{alto}"></iframe>'
                    '<script>document.getElementById("f").addEventListener("load",function(){'
                    f'var w=this.contentWindow;function ir(){{try{{w.document.documentElement.style.scrollBehavior="auto";}}catch(e){{}}'
                    f'w.scrollTo({{top:{y},left:0,behavior:"instant"}});}}setTimeout(ir,800);setTimeout(ir,2500);}});</script>'
                    '</body></html>')
                s = f"{prefijo}-{ancho}x{alto}-{n + 1:02d}.png"
                chrome("file:///" + ifr.replace("\\", "/"), s, max(600, ancho), alto, perfil)
                os.remove(ifr)
                im = Image.open(s).convert("RGB").crop((0, 0, ancho, alto))
                # Fin de página: la captura es igual que la anterior (el scroll ya no avanza)
                if y > alto and salidas and salidas[-1][0].startswith(f"{prefijo}-{ancho}x{alto}-") and list(im.getdata()) == salidas[-1][1]:
                    os.remove(s)
                    break
                banda = Image.new("RGB", (ancho, 28), "#111")
                ImageDraw.Draw(banda).text((8, 6), f"{ancho}x{alto}  scroll {y}px  captura {n + 1}", fill="#fff")
                hoja = Image.new("RGB", (ancho, alto + 28))
                hoja.paste(banda, (0, 0)); hoja.paste(im, (0, 28))
                hoja.save(s)
                salidas.append((s, list(im.getdata())))
                n += 1
                y += int(alto * PASO)
            print(f"{ancho}x{alto}: {n} capturas")
    for s, _ in salidas:
        print(s)


if __name__ == "__main__":
    main()
