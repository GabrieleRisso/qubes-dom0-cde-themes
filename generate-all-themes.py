#!/usr/bin/env python3
"""
Generate one XFCE4 theme per CDE palette.
Creates ~/.themes/CDE-<PaletteName>/ for each of the 131 palettes.
Uses symlinks for shared assets (xfwm4, img, img2) to save disk space.

Run from the dom0-themes directory:
    python3 generate-all-themes.py
"""

import os
import sys
import re
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
THEMES_DIR = os.path.join(SCRIPT_DIR, ".themes")
PALETTES_DIR = os.path.join(SCRIPT_DIR, "palettes")
BASE_THEME = os.path.join(THEMES_DIR, "CDE-Theme")

# Motif color constants
XmCOLOR_LITE_SEL_FACTOR = 15
XmCOLOR_LITE_BS_FACTOR = 40
XmCOLOR_LITE_TS_FACTOR = 20
XmCOLOR_LO_SEL_FACTOR = 15
XmCOLOR_LO_BS_FACTOR = 60
XmCOLOR_LO_TS_FACTOR = 50
XmCOLOR_HI_SEL_FACTOR = 15
XmCOLOR_HI_BS_FACTOR = 40
XmCOLOR_HI_TS_FACTOR = 60
XmCOLOR_DARK_SEL_FACTOR = 15
XmCOLOR_DARK_BS_FACTOR = 30
XmCOLOR_DARK_TS_FACTOR = 50
XmRED_LUMINOSITY = 0.30
XmGREEN_LUMINOSITY = 0.59
XmBLUE_LUMINOSITY = 0.11
XmINTENSITY_FACTOR = 75
XmLIGHT_FACTOR = 0
XmLUMINOSITY_FACTOR = 25
XmMAX_SHORT = 65535
XmDEFAULT_DARK_THRESHOLD = 20
XmDEFAULT_LIGHT_THRESHOLD = 93
XmDEFAULT_FOREGROUND_THRESHOLD = 70
XmCOLOR_PERCENTILE = XmMAX_SHORT / 100
XmCOLOR_LITE_THRESHOLD = XmDEFAULT_LIGHT_THRESHOLD * XmCOLOR_PERCENTILE
XmCOLOR_DARK_THRESHOLD = XmDEFAULT_DARK_THRESHOLD * XmCOLOR_PERCENTILE
XmFOREGROUND_THRESHOLD = XmDEFAULT_FOREGROUND_THRESHOLD * XmCOLOR_PERCENTILE

HEX = '0123456789abcdef'
HEXNUM = [4096, 256, 16, 1]


def int2hex(n):
    n = max(0, min(65535, int(n)))
    if n == 0:
        return '0000'
    h = ''
    for a in HEXNUM:
        i = int(n / a)
        h += HEX[i]
        n -= i * a
    return h


def encode16bpp(color):
    color = color.strip()
    m = re.search(r'#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$', color)
    if m:
        a, b, c = m.group(1), m.group(2), m.group(3)
        return f"#{a}{a}{b}{b}{c}{c}"
    m = re.search(r'#[0-9a-fA-F]{12}$', color)
    if m:
        return color
    return "#888888888888"


def bpp_to_rgb(hexcolor):
    m = re.search(r'#(....)(....)(....)', hexcolor)
    if m:
        return [int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16)]
    m = re.search(r'#(..)(..)(..)', hexcolor)
    if m:
        return [int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16)]
    return [0, 0, 0]


def brightness(color):
    red, green, blue = color
    intensity = (red + green + blue) / 3.0
    luminosity = int(XmRED_LUMINOSITY * red + XmGREEN_LUMINOSITY * green + XmBLUE_LUMINOSITY * blue)
    ma = max(red, green, blue)
    mi = min(red, green, blue)
    light = (mi + ma) / 2.0
    return ((intensity * XmINTENSITY_FACTOR) + (light * XmLIGHT_FACTOR) + (luminosity * XmLUMINOSITY_FACTOR)) / 100.0


def calc_dark(bg_color):
    fg_c, sel_c, bs_c, ts_c = [0,0,0], [0,0,0], [0,0,0], [0,0,0]
    b = brightness(bg_color)
    fg_c = [0,0,0] if b > XmFOREGROUND_THRESHOLD else [XmMAX_SHORT]*3
    for i in range(3):
        sel_c[i] = bg_color[i] + XmCOLOR_DARK_SEL_FACTOR * (XmMAX_SHORT - bg_color[i]) / 100.0
        bs_c[i] = bg_color[i] + XmCOLOR_DARK_BS_FACTOR * (XmMAX_SHORT - bg_color[i]) / 100.0
        ts_c[i] = bg_color[i] + XmCOLOR_DARK_TS_FACTOR * (XmMAX_SHORT - bg_color[i]) / 100.0
    return fg_c, sel_c, bs_c, ts_c


def calc_light(bg_color):
    fg_c, sel_c, bs_c, ts_c = [0,0,0], [0,0,0], [0,0,0], [0,0,0]
    b = brightness(bg_color)
    fg_c = [0,0,0] if b > XmFOREGROUND_THRESHOLD else [XmMAX_SHORT]*3
    for i in range(3):
        sel_c[i] = bg_color[i] - (bg_color[i] * XmCOLOR_LITE_SEL_FACTOR) / 100.0
        bs_c[i] = bg_color[i] - (bg_color[i] * XmCOLOR_LITE_BS_FACTOR) / 100.0
        ts_c[i] = bg_color[i] - (bg_color[i] * XmCOLOR_LITE_TS_FACTOR) / 100.0
    return fg_c, sel_c, bs_c, ts_c


def calc_medium(bg_color):
    fg_c, sel_c, bs_c, ts_c = [0,0,0], [0,0,0], [0,0,0], [0,0,0]
    b = brightness(bg_color)
    fg_c = [0,0,0] if b > XmFOREGROUND_THRESHOLD else [XmMAX_SHORT]*3
    f_sel = XmCOLOR_LO_SEL_FACTOR + (b * (XmCOLOR_HI_SEL_FACTOR - XmCOLOR_LO_SEL_FACTOR) / XmMAX_SHORT)
    f_bs = XmCOLOR_LO_BS_FACTOR + (b * (XmCOLOR_HI_BS_FACTOR - XmCOLOR_LO_BS_FACTOR) / XmMAX_SHORT)
    f_ts = XmCOLOR_LO_TS_FACTOR + (b * (XmCOLOR_HI_TS_FACTOR - XmCOLOR_LO_TS_FACTOR) / XmMAX_SHORT)
    for i in range(3):
        sel_c[i] = bg_color[i] - (bg_color[i] * f_sel) / 100.0
        bs_c[i] = bg_color[i] - (bg_color[i] * f_bs) / 100.0
        ts_c[i] = bg_color[i] + f_ts * (XmMAX_SHORT - bg_color[i]) / 100.0
    return fg_c, sel_c, bs_c, ts_c


def rgb_to_hex(rgb):
    return "#" + int2hex(rgb[0]) + int2hex(rgb[1]) + int2hex(rgb[2])


def round_hex_to_6(h):
    return '#' + h[1:3] + h[5:7] + h[9:11]


def compute_colorset(palette_lines):
    bg = [None]*9; fg = [None]*9; ts = [None]*9; bs = [None]*9; sel = [None]*9
    for a in range(1, 9):
        line = palette_lines[a-1]
        if isinstance(line, bytes):
            line = line.decode()
        color16 = encode16bpp(line)
        bg_color = bpp_to_rgb(color16)
        b = brightness(bg_color)
        if b < XmCOLOR_DARK_THRESHOLD:
            fg_c, sel_c, bs_c, ts_c = calc_dark(bg_color)
        elif b > XmCOLOR_LITE_THRESHOLD:
            fg_c, sel_c, bs_c, ts_c = calc_light(bg_color)
        else:
            fg_c, sel_c, bs_c, ts_c = calc_medium(bg_color)
        bg[a] = color16; fg[a] = rgb_to_hex(fg_c)
        bs[a] = rgb_to_hex(bs_c); ts[a] = rgb_to_hex(ts_c); sel[a] = rgb_to_hex(sel_c)
    for a in range(1, 9):
        bg[a] = round_hex_to_6(bg[a]); fg[a] = round_hex_to_6(fg[a])
        bs[a] = round_hex_to_6(bs[a]); ts[a] = round_hex_to_6(ts[a]); sel[a] = round_hex_to_6(sel[a])
    return bg, fg, ts, bs, sel


def gen_gtk3_css(bg, fg, ts, bs, sel, name):
    lines = [f"\n/*\n Generated by generate-all-themes.py for palette {name}\n*/\n"]
    for a in range(1, 9):
        lines.append(f"@define-color bg_color_{a} {bg[a]}; ")
        lines.append(f"@define-color fg_color_{a} {fg[a]}; ")
        lines.append(f"@define-color ts_color_{a} {ts[a]}; ")
        lines.append(f"@define-color bs_color_{a} {bs[a]}; ")
        lines.append(f"@define-color sel_color_{a} {sel[a]}; ")
        lines.append("")
    lines.append('\n* {\n    font-family: "DejaVu Serif";\n    font-size: 12px;\n}\n')
    return "\n".join(lines)


def gen_gtk2_rc(bg, fg, ts, bs, sel, name):
    lines = [f"#\n# Generated by generate-all-themes.py for palette {name}\n#\n"]
    scheme = (f"fg_color:{fg[5]}\\nbg_color:{bg[5]}\\nbase_color:{bg[4]}\\n"
              f"text_color:{fg[5]}\\nselected_bg_color:{sel[5]}\\nselected_fg_color:{fg[5]}\\n"
              f"tooltip_bg_color:{sel[5]}\\ntooltip_fg_color:{fg[5]}")
    lines.append(f'gtk-color-scheme = "{scheme}"\n')
    for a in range(1, 9):
        lines.append(f'style "cde_style_{a}"\n{{')
        lines.append(f'    fg[NORMAL]  ="{fg[a]}"\n    bg[NORMAL]  ="{bg[a]}"')
        lines.append(f'    text[NORMAL]="{fg[a]}"\n    base[NORMAL]="{bg[a]}"')
        lines.append(f'    fg[ACTIVE]  ="{fg[a]}"\n    bg[ACTIVE]  ="{sel[a]}"')
        lines.append(f'    text[ACTIVE]="{fg[a]}"\n    base[ACTIVE]="{sel[a]}"')
        lines.append(f'    fg[PRELIGHT]="{fg[a]}"\n    bg[PRELIGHT]="{bg[a]}"')
        lines.append(f'    text[PRELIGHT]="{fg[a]}"\n    base[PRELIGHT] ="{bg[a]}"')
        lines.append(f'    fg[SELECTED]="{bg[a]}"\n    bg[SELECTED]="{fg[a]}"')
        lines.append(f'    text[SELECTED]="{bg[a]}"\n    base[SELECTED]="{fg[a]}"')
        lines.append(f'    fg[INSENSITIVE]="{bs[a]}"\n    bg[INSENSITIVE]="{bg[a]}"')
        lines.append(f'    text[INSENSITIVE]="{bs[a]}"\n    base[INSENSITIVE]="{bg[a]}"')
        lines.append("}\n")
    for a in range(1, 9):
        lines.append(f'style "cde_style_sel_{a}"\n{{')
        lines.append(f'    fg[NORMAL]  ="{fg[a]}"\n    bg[NORMAL]  ="{sel[a]}"')
        lines.append(f'    text[NORMAL]="{fg[a]}"\n    base[NORMAL]="{sel[a]}"')
        lines.append(f'    fg[ACTIVE]  ="{fg[a]}"\n    bg[ACTIVE]  ="{bg[a]}"')
        lines.append(f'    text[ACTIVE]="{fg[a]}"\n    base[ACTIVE]="{bg[a]}"')
        lines.append(f'    fg[PRELIGHT]="{fg[a]}"\n    bg[PRELIGHT]="{bs[a]}"')
        lines.append(f'    text[PRELIGHT]="{fg[a]}"\n    base[PRELIGHT] ="{bs[a]}"')
        lines.append(f'    fg[SELECTED]="{fg[a]}"\n    bg[SELECTED]="{bs[a]}"')
        lines.append(f'    text[SELECTED]="{fg[a]}"\n    base[SELECTED]="{bs[a]}"')
        lines.append(f'    fg[INSENSITIVE]="{fg[a]}"\n    bg[INSENSITIVE]="{sel[a]}"')
        lines.append(f'    text[INSENSITIVE]="{fg[a]}"\n    base[INSENSITIVE]="{sel[a]}"')
        lines.append("}\n")
    return "\n".join(lines)


def gen_index_theme(name):
    return f"""[Desktop Entry]
Type=X-GNOME-Metatheme
Name=CDE - {name}
Comment=CDE Motif theme with {name} palette
Encoding=UTF-8

[X-GNOME-Metatheme]
GtkTheme=CDE - {name}
ButtonLayout=close,minimize,maximize:menu

[X-GNOME-Metatheme-GTK4]
GtkTheme=CDE - {name}
ButtonLayout=close,minimize,maximize:menu
"""


def read_palette(filepath):
    with open(filepath, 'r') as f:
        return [l.strip() for l in f.readlines() if l.strip()][:8]


def make_relative_symlink(target, link_path):
    """Create a relative symlink from link_path -> target."""
    rel = os.path.relpath(target, os.path.dirname(link_path))
    os.symlink(rel, link_path)


def main():
    if not os.path.isdir(BASE_THEME):
        print(f"ERROR: Base theme not found at {BASE_THEME}")
        sys.exit(1)
    if not os.path.isdir(PALETTES_DIR):
        print(f"ERROR: Palettes dir not found at {PALETTES_DIR}")
        sys.exit(1)

    palette_files = sorted([f for f in os.listdir(PALETTES_DIR) if f.endswith('.dp')])
    print(f"Generating {len(palette_files)} CDE themes...\n")

    # Shared directories that are the same across all palettes (images, xfwm4 borders)
    shared_dirs = ['xfwm4', 'img', 'img2']

    # GTK files that need to be copied (not color files -- the structural CSS/rc)
    # We'll copy the whole gtk-2.0, gtk-3.0, gtk-4.0 dirs and then overwrite the color files

    count = 0
    for pf in palette_files:
        name = pf[:-3]  # strip .dp
        theme_name = f"CDE-{name}"
        theme_dir = os.path.join(THEMES_DIR, theme_name)

        # Remove old version if exists
        if os.path.exists(theme_dir):
            shutil.rmtree(theme_dir)

        os.makedirs(theme_dir)

        # Write index.theme
        with open(os.path.join(theme_dir, "index.theme"), 'w') as f:
            f.write(gen_index_theme(name))

        # Symlink shared asset directories to the base theme
        for sd in shared_dirs:
            src = os.path.join(BASE_THEME, sd)
            if os.path.exists(src):
                make_relative_symlink(src, os.path.join(theme_dir, sd))

        # Copy GTK directories and generate color files
        palette_lines = read_palette(os.path.join(PALETTES_DIR, pf))
        if len(palette_lines) < 8:
            print(f"  SKIP {name}: palette has only {len(palette_lines)} colors (need 8)")
            continue

        bg, fg, ts, bs, sel = compute_colorset(palette_lines)

        # gtk-2.0: copy structure, write colors
        gtk2_src = os.path.join(BASE_THEME, "gtk-2.0")
        gtk2_dst = os.path.join(theme_dir, "gtk-2.0")
        if os.path.isdir(gtk2_src):
            shutil.copytree(gtk2_src, gtk2_dst)
            with open(os.path.join(gtk2_dst, "cdecolors.rc"), 'w') as f:
                f.write(gen_gtk2_rc(bg, fg, ts, bs, sel, name))

        # gtk-3.0: copy structure, write colors
        gtk3_src = os.path.join(BASE_THEME, "gtk-3.0")
        gtk3_dst = os.path.join(theme_dir, "gtk-3.0")
        if os.path.isdir(gtk3_src):
            shutil.copytree(gtk3_src, gtk3_dst)
            with open(os.path.join(gtk3_dst, "cdecolors.css"), 'w') as f:
                f.write(gen_gtk3_css(bg, fg, ts, bs, sel, name))

        # gtk-4.0: copy structure, write colors
        gtk4_src = os.path.join(BASE_THEME, "gtk-4.0")
        gtk4_dst = os.path.join(theme_dir, "gtk-4.0")
        if os.path.isdir(gtk4_src):
            shutil.copytree(gtk4_src, gtk4_dst)
            with open(os.path.join(gtk4_dst, "cdecolors.css"), 'w') as f:
                f.write(gen_gtk3_css(bg, fg, ts, bs, sel, name))

        count += 1
        # Print a sample color for visual reference
        print(f"  [{count:3d}] CDE-{name:<24s}  main={bg[5]}  title={bg[1]}  menu={bg[6]}")

    print(f"\nDone! Generated {count} themes in {THEMES_DIR}/")
    print(f"Each theme is named 'CDE-<Palette>' and will appear in XFCE Appearance settings.")
    print(f"\nShared assets (xfwm4, img, img2) are symlinked to save ~400MB of disk space.")

    # Print total size
    total = 0
    for dirpath, dirnames, filenames in os.walk(THEMES_DIR):
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            if not os.path.islink(fp):
                total += os.path.getsize(fp)
    print(f"Total disk usage (excluding symlinks): {total / 1024 / 1024:.1f} MB")


if __name__ == '__main__':
    main()
