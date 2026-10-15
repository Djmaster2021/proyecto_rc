"""
Modo oscuro del panel del dentista por sustitución de colores.

Cada color "claro" (fondos/bordes) u "oscuro" (texto) en:
  - dentista/static/dentista/styles.css
  - bloques <style> de las plantillas del dentista
  - atributos style="" de las plantillas
se reemplaza por var(--dk-<rol>-<color>, <color original>).

En modo claro la variable no existe -> se usa el color original (sin cambios visuales).
En modo oscuro, theme-dark.css define cada --dk-* con su equivalente oscuro.
La cascada/especificidad del CSS original no cambia.

Uso: python gen_dark.py <raiz_proyecto> [--write]
"""
import colorsys
import pathlib
import re
import sys

ROOT = pathlib.Path(sys.argv[1])
WRITE = "--write" in sys.argv
CSS = ROOT / "dentista/static/dentista/styles.css"
TPL_DIR = ROOT / "dentista/templates/dentista"
OUT = ROOT / "dentista/static/dentista/theme-dark.css"
EXCLUDE_TPL = {"email-dentista.html", "email-paciente.html", "reporte_pdf.html"}

# Selectores que NO se tocan (el menú lateral ya es oscuro en ambos temas)
SKIP_SEL = ("sidebar", ".nav-", "nav-item", "nav-caption", "user-glass", "user-img", ".u-name", ".u-role",
            "btn-logout", "logo-", "brand-", "mobile-app-bar", "mobile-brand", "mobile-avatar", "status-dot", "swal2")

COLOR_RE = re.compile(r"#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|rgba?\([^)]*\)|\bwhite\b|\bblack\b")
VARS = {}
QUOTES = ("\"", "'")


# ----------------------------------------------------------------------------- colores
def parse_color(tok):
    t = tok.lower()
    if t == "white":
        return 255, 255, 255, 1.0
    if t == "black":
        return 0, 0, 0, 1.0
    if t.startswith("#"):
        h = t[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        a = 1.0
        if len(h) == 8:
            a, h = int(h[6:8], 16) / 255, h[:6]
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a
    m = re.match(r"rgba?\(([^)]*)\)", t)
    if m:
        parts = [p for p in re.split(r"[,\s/]+", m.group(1).strip()) if p]
        try:
            r, g, b = (float(x.rstrip("%")) for x in parts[:3])
            a = float(parts[3]) if len(parts) > 3 else 1.0
            return int(r), int(g), int(b), a
        except (ValueError, IndexError):
            return None
    return None


def analyze(c):
    """(hue, lightness, chroma) — los grises azulados (slate) cuentan como neutros."""
    r, g, b, _ = c
    h, l, _s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    chroma = (max(r, g, b) - min(r, g, b)) / 255
    slate = 195 <= h * 360 <= 235 and chroma < (0.12 if l > 0.7 else 0.22)
    return h, l, 0.0 if slate else chroma


def hsl_css(h, s, l, a=1.0):
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    if a < 1:
        return f"rgba({round(r*255)}, {round(g*255)}, {round(b*255)}, {a:.2f})"
    return f"#{round(r*255):02x}{round(g*255):02x}{round(b*255):02x}"


def map_bg(c):
    h, l, ch = analyze(c)
    if c[3] < 0.35 or l < 0.80:
        return None
    if ch >= 0.06 and l < 0.985:
        return hsl_css(h, 0.45, 0.15, c[3])
    return "var(--bg-card)" if l >= 0.975 else "var(--bg-soft)"


def map_text(c):
    h, l, ch = analyze(c)
    if c[3] < 0.3:
        return None
    if ch < 0.22:
        if l <= 0.30:
            return "var(--text-main)"
        if l < 0.70:
            return "var(--text-muted)"
        return None
    if l <= 0.36:
        return hsl_css(h, 0.6, 0.72)
    return None


def map_border(c):
    h, l, ch = analyze(c)
    if c[3] < 0.3 or l < 0.75:
        return None
    if ch >= 0.08 and l < 0.97:
        return hsl_css(h, 0.4, 0.28)
    return "var(--border-subtle)"


ROLE = {map_bg: "bg", map_text: "tx", map_border: "bd"}
ROLE_FN = {"bg": map_bg, "tx": map_text, "bd": map_border}


def mapper_for(prop):
    p = prop.strip().lower()
    if p in ("background", "background-color", "background-image"):
        return map_bg
    if p in ("color", "fill", "-webkit-text-fill-color"):
        return map_text
    if p.startswith("border") or p.startswith("outline") or p == "box-shadow":
        return map_border
    return None


def var_for(fn, token):
    c = parse_color(token)
    new = fn(c) if c else None
    if new is None:
        return token
    name = f"--dk-{ROLE[fn]}-{re.sub(r'[^0-9a-z]', '', token.lower())}"
    VARS[name] = new
    return f"var({name}, {token})"


DECL_RE = re.compile(r"([a-zA-Z-]+)(\s*:\s*)([^;{}]+)")


def transform_decls(text):
    def rep(m):
        prop, sep, val = m.group(1), m.group(2), m.group(3)
        fn = mapper_for(prop)
        if not fn or "var(--dk-" in val:
            return m.group(0)
        return prop + sep + COLOR_RE.sub(lambda cm: var_for(fn, cm.group(0)), val)

    return DECL_RE.sub(rep, text)


# ----------------------------------------------------------------------------- CSS
def transform_css_text(text):
    """Recorre el CSS (comentarios, cadenas, etiquetas Django, @media) y transforma solo reglas normales."""
    out = []
    i, n = 0, len(text)
    stack = []
    seg = 0  # inicio del segmento pendiente
    while i < n:
        two = text[i:i + 2]
        if two == "/*":
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if two in ("{%", "{{"):
            j = text.find("%}" if two == "{%" else "}}", i + 2)
            i = n if j < 0 else j + 2
            continue
        ch = text[i]
        if ch in QUOTES:
            j = i + 1
            while j < n and text[j] != ch:
                j += 2 if text[j] == "\\" else 1
            i = j + 1
            continue
        if ch == "{":
            prelude = re.sub(r"/\*.*?\*/", "", text[seg:i], flags=re.S).strip().rsplit(";", 1)[-1].strip()
            stack.append(prelude)
            out.append(text[seg:i + 1])
            seg = i + 1
        elif ch == "}":
            prelude = stack.pop() if stack else ""
            body = text[seg:i]
            is_rule = (prelude and not prelude.startswith("@") and not prelude.startswith(":root")
                       and not any(k in prelude for k in SKIP_SEL)
                       and not any("print" in p for p in stack if p.startswith("@media"))
                       and not any(p.startswith("@keyframes") for p in stack))
            out.append(transform_decls(body) if is_rule else body)
            out.append("}")
            seg = i + 1
        i += 1
    out.append(text[seg:])
    return "".join(out)


STYLE_BLOCK_RE = re.compile(r"(<style[^>]*>)(.*?)(</style>)", re.S)
STYLE_ATTR_RE = re.compile(r'style="([^"]*)"')


def transform_template(src):
    src = STYLE_BLOCK_RE.sub(lambda m: m.group(1) + transform_css_text(m.group(2)) + m.group(3), src)
    return STYLE_ATTR_RE.sub(lambda m: 'style="' + transform_decls(m.group(1)) + '"', src)


def main():
    changed = []
    css_src = CSS.read_text(encoding="utf-8")
    css_new = transform_css_text(css_src)
    if css_new != css_src:
        changed.append(CSS.name)
        if WRITE:
            CSS.write_text(css_new, encoding="utf-8")
    for tpl in sorted(TPL_DIR.glob("*.html")):
        if tpl.name in EXCLUDE_TPL:
            continue
        src = tpl.read_text(encoding="utf-8")
        new = transform_template(src)
        if new != src:
            changed.append(tpl.name)
            if WRITE:
                tpl.write_text(new, encoding="utf-8")

    # Variables ya presentes de ejecuciones anteriores también se definen
    for f in [CSS, *TPL_DIR.glob("*.html")]:
        for name, orig in re.findall(r"var\((--dk-(bg|tx|bd)-[0-9a-z]+), ([^)]+\)?)\)", f.read_text(encoding="utf-8")) and \
                [(a, c) for a, _b, c in re.findall(r"var\((--dk-(bg|tx|bd)-[0-9a-z]+), ([^)]+\)?)\)", f.read_text(encoding="utf-8"))]:
            if name not in VARS:
                tok = COLOR_RE.search(orig)
                if tok:
                    var_for(ROLE_FN[name.split("-")[3]], tok.group(0))

    lines = [
        "/* ==========================================================================",
        "   MODO OSCURO — PANEL DEL DENTISTA (ARCHIVO GENERADO)",
        "   Los colores fijos de styles.css y de las plantillas usan var(--dk-*, original).",
        "   Aquí se define el valor oscuro de cada variable. En modo claro no aplica.",
        "   Ajustes manuales: dentista/static/dentista/theme.css",
        "   ========================================================================== */",
        'html[data-theme="dark"] {',
        *[f"  {k}: {VARS[k]};" for k in sorted(VARS)],
        "}",
        "",
    ]
    if WRITE:
        OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"variables: {len(VARS)}  archivos con cambios: {len(changed)} {'(escritos)' if WRITE else '(simulación)'}")
    print(", ".join(changed))


main()
