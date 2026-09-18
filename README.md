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
| `favicon.svg` | Icono de pestaña (arco naranja del logo). |
| `.nojekyll` | Para que GitHub Pages sirva los ficheros tal cual. |

Todo el texto sale de la web actual; no hay cifras ni clientes inventados. Hay una contradicción que conviene confirmar con el cliente: los textos dicen "en proceso de certificación ISO 9001 / OHSAS 18001" pero los sellos AENOR e ICDQ de su web muestran ISO 9001 e ISO 14001:2015.

## Pasar a producción (cuando el cliente dé el OK)

Wix no permite importar HTML, así que la vía limpia es alojar esta web fuera y apuntarle el dominio:

1. **Alojar** (gratis): GitHub Pages (este repo), Cloudflare Pages o Netlify. También vale cualquier servidor con nginx.
2. **Dominio**: en el panel de Wix (o donde esté registrado `twinsoldecor.com`) cambiar el DNS: registro `A` a las IP de GitHub Pages (185.199.108.153 / .109 / .110 / .111) y `CNAME www → <usuario>.github.io`. Añadir el fichero `CNAME` con `www.twinsoldecor.com` y activar *Enforce HTTPS*. Si el correo `info@twinsoldecor.com` va por Wix, se dejan los registros `MX` como están: solo cambia la web.
3. **Formulario de contacto**: ahora el envío es simulado (muestra confirmación sin mandar nada). Para que llegue al correo sin servidor: crear una clave gratuita en [Web3Forms](https://web3forms.com) o [Formspree](https://formspree.io) y cambiar el `action` del `<form>` por su URL (dos líneas, marcadas con un comentario `PRODUCCIÓN` en el HTML).
4. **Quitar** la etiqueta `<meta name="robots" content="noindex, nofollow">` del `<head>` para que Google indexe la web nueva.
5. **Dar de baja** el plan Premium de Wix cuando la nueva esté sirviendo (mantener el dominio y el correo si están contratados ahí).

## Si el cliente prefiere seguir en Wix

No se puede pegar este HTML en Wix. Habría que reconstruir el diseño a mano en el editor de Wix (o Wix Studio) usando esta página como maqueta: mismas fotos (`img/`), mismos textos, misma paleta y las fuentes (están en Google Fonts, que Wix incluye). El elemento "Insertar HTML" de Wix mete un iframe por bloque: no sirve para toda la página.
