#!/usr/bin/env python3
"""
CDE Theme Color Changer for XFCE4
===================================
Changes the CDE theme colors using authentic Motif color calculation algorithms.
Works standalone with Python 3 -- no PyQt5 or other dependencies needed.

Usage:
    python3 change-cde-colors.py                     # interactive - lists palettes
    python3 change-cde-colors.py <palette_name>      # apply a built-in palette
    python3 change-cde-colors.py --custom R,G,B      # use a single custom color (0-255)
    python3 change-cde-colors.py --list               # list all available palettes
    python3 change-cde-colors.py --preview <palette>  # preview palette colors

Examples:
    python3 change-cde-colors.py Crimson
    python3 change-cde-colors.py DarkBlue
    python3 change-cde-colors.py HPVue
    python3 change-cde-colors.py --custom 100,120,180
"""

import os
import sys
import re
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
THEME_DIR = os.path.join(SCRIPT_DIR, ".themes", "CDE-Theme")
PALETTES_DIR = os.path.join(SCRIPT_DIR, "palettes")

# =====================================================================
# Motif color calculation constants (from the original CDE source)
# =====================================================================
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
    """Convert #RRGGBB or #RRRRGGGGBBBB to 16bpp #RRRRGGGGBBBB."""
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
    """Convert hex color to [R, G, B] in 16-bit range (0-65535)."""
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
    fg_c = [0, 0, 0]
    sel_c = [0, 0, 0]
    bs_c = [0, 0, 0]
    ts_c = [0, 0, 0]
    b = brightness(bg_color)
    if b > XmFOREGROUND_THRESHOLD:
        fg_c = [0, 0, 0]
    else:
        fg_c = [XmMAX_SHORT, XmMAX_SHORT, XmMAX_SHORT]
    for i in range(3):
        sel_c[i] = bg_color[i] + XmCOLOR_DARK_SEL_FACTOR * (XmMAX_SHORT - bg_color[i]) / 100.0
        bs_c[i] = bg_color[i] + XmCOLOR_DARK_BS_FACTOR * (XmMAX_SHORT - bg_color[i]) / 100.0
        ts_c[i] = bg_color[i] + XmCOLOR_DARK_TS_FACTOR * (XmMAX_SHORT - bg_color[i]) / 100.0
    return fg_c, sel_c, bs_c, ts_c


def calc_light(bg_color):
    fg_c = [0, 0, 0]
    sel_c = [0, 0, 0]
    bs_c = [0, 0, 0]
    ts_c = [0, 0, 0]
    b = brightness(bg_color)
    if b > XmFOREGROUND_THRESHOLD:
        fg_c = [0, 0, 0]
    else:
        fg_c = [XmMAX_SHORT, XmMAX_SHORT, XmMAX_SHORT]
    for i in range(3):
        sel_c[i] = bg_color[i] - (bg_color[i] * XmCOLOR_LITE_SEL_FACTOR) / 100.0
        bs_c[i] = bg_color[i] - (bg_color[i] * XmCOLOR_LITE_BS_FACTOR) / 100.0
        ts_c[i] = bg_color[i] - (bg_color[i] * XmCOLOR_LITE_TS_FACTOR) / 100.0
    return fg_c, sel_c, bs_c, ts_c


def calc_medium(bg_color):
    fg_c = [0, 0, 0]
    sel_c = [0, 0, 0]
    bs_c = [0, 0, 0]
    ts_c = [0, 0, 0]
    b = brightness(bg_color)
    if b > XmFOREGROUND_THRESHOLD:
        fg_c = [0, 0, 0]
    else:
        fg_c = [XmMAX_SHORT, XmMAX_SHORT, XmMAX_SHORT]
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
    """Convert #RRRRGGGGBBBB to #RRGGBB."""
    return '#' + h[1:3] + h[5:7] + h[9:11]


def compute_colorset(palette_lines):
    """From 8 palette color lines, compute all 8 colorsets with bg/fg/ts/bs/sel."""
    bg = [None] * 9
    fg = [None] * 9
    ts = [None] * 9
    bs = [None] * 9
    sel = [None] * 9

    for a in range(1, 9):
        color16 = encode16bpp(palette_lines[a - 1].decode() if isinstance(palette_lines[a - 1], bytes) else palette_lines[a - 1])
        bg_color = bpp_to_rgb(color16)
        b = brightness(bg_color)
        if b < XmCOLOR_DARK_THRESHOLD:
            fg_c, sel_c, bs_c, ts_c = calc_dark(bg_color)
        elif b > XmCOLOR_LITE_THRESHOLD:
            fg_c, sel_c, bs_c, ts_c = calc_light(bg_color)
        else:
            fg_c, sel_c, bs_c, ts_c = calc_medium(bg_color)
        bg[a] = color16
        fg[a] = rgb_to_hex(fg_c)
        bs[a] = rgb_to_hex(bs_c)
        ts[a] = rgb_to_hex(ts_c)
        sel[a] = rgb_to_hex(sel_c)

    # Round to 6-char hex
    for a in range(1, 9):
        bg[a] = round_hex_to_6(bg[a])
        fg[a] = round_hex_to_6(fg[a])
        bs[a] = round_hex_to_6(bs[a])
        ts[a] = round_hex_to_6(ts[a])
        sel[a] = round_hex_to_6(sel[a])

    return bg, fg, ts, bs, sel


def read_palette_file(filepath):
    with open(filepath, 'r') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    return lines[:8]


def generate_gtk3_colors_css(bg, fg, ts, bs, sel, palette_name):
    lines = []
    lines.append("")
    lines.append(f"/*")
    lines.append(f" Generated by change-cde-colors.py for palette {palette_name}")
    lines.append(f" Edits will be overwritten")
    lines.append(f"*/")
    lines.append("")
    for a in range(1, 9):
        lines.append(f"@define-color bg_color_{a} {bg[a]}; ")
        lines.append(f"@define-color fg_color_{a} {fg[a]}; ")
        lines.append(f"@define-color ts_color_{a} {ts[a]}; ")
        lines.append(f"@define-color bs_color_{a} {bs[a]}; ")
        lines.append(f"@define-color sel_color_{a} {sel[a]}; ")
        lines.append("")
    lines.append("")
    lines.append("* {")
    lines.append('    font-family: "DejaVu Serif";')
    lines.append("    font-size: 12px;")
    lines.append("}")
    lines.append("    ")
    return "\n".join(lines) + "\n"


def generate_gtk2_colors_rc(bg, fg, ts, bs, sel, palette_name):
    lines = []
    lines.append(f"#")
    lines.append(f"# Generated by change-cde-colors.py for palette {palette_name}")
    lines.append(f"# Edits will be overwritten")
    lines.append(f"#")
    lines.append("    ")

    # GTK color scheme string
    scheme = (f"fg_color:{fg[5]}\\nbg_color:{bg[5]}\\nbase_color:{bg[4]}\\n"
              f"text_color:{fg[5]}\\nselected_bg_color:{sel[5]}\\nselected_fg_color:{fg[5]}\\n"
              f"tooltip_bg_color:{sel[5]}\\ntooltip_fg_color:{fg[5]}")
    lines.append(f'gtk-color-scheme = "{scheme}"')
    lines.append("    ")

    for a in range(1, 9):
        lines.append(f'style "cde_style_{a}"')
        lines.append("{")
        lines.append(f'    fg[NORMAL]  ="{fg[a]}"')
        lines.append(f'    bg[NORMAL]  ="{bg[a]}"')
        lines.append(f'    text[NORMAL]="{fg[a]}"')
        lines.append(f'    base[NORMAL]="{bg[a]}"')
        lines.append("")
        lines.append(f'    fg[ACTIVE]  ="{fg[a]}"')
        lines.append(f'    bg[ACTIVE]  ="{sel[a]}"')
        lines.append(f'    text[ACTIVE]="{fg[a]}"')
        lines.append(f'    base[ACTIVE]="{sel[a]}"')
        lines.append("")
        lines.append(f'    fg[PRELIGHT]="{fg[a]}"')
        lines.append(f'    bg[PRELIGHT]="{bg[a]}"')
        lines.append(f'    text[PRELIGHT]="{fg[a]}"')
        lines.append(f'    base[PRELIGHT] ="{bg[a]}"')
        lines.append("")
        lines.append(f'    fg[SELECTED]="{bg[a]}"')
        lines.append(f'    bg[SELECTED]="{fg[a]}"')
        lines.append(f'    text[SELECTED]="{bg[a]}"')
        lines.append(f'    base[SELECTED]="{fg[a]}"')
        lines.append("")
        lines.append(f'    #this is the dark color of the etched in insensitive text when on normal background of widget')
        lines.append(f'    fg[INSENSITIVE]="{bs[a]}"')
        lines.append(f'    bg[INSENSITIVE]="{bg[a]}"')
        lines.append(f'    #insensitive text color in entry and also fg color of etched in text in combo box')
        lines.append(f'    text[INSENSITIVE]="{bs[a]}"')
        lines.append(f'    #in cde this is normal bg color')
        lines.append(f'    base[INSENSITIVE]="{bg[a]}"')
        lines.append("}")
        lines.append("")

    # Also generate sel styles
    for a in range(1, 9):
        lines.append(f'style "cde_style_sel_{a}"')
        lines.append("{")
        lines.append(f'    fg[NORMAL]  ="{fg[a]}"')
        lines.append(f'    bg[NORMAL]  ="{sel[a]}"')
        lines.append(f'    text[NORMAL]="{fg[a]}"')
        lines.append(f'    base[NORMAL]="{sel[a]}"')
        lines.append("")
        lines.append(f'    fg[ACTIVE]  ="{fg[a]}"')
        lines.append(f'    bg[ACTIVE]  ="{bg[a]}"')
        lines.append(f'    text[ACTIVE]="{fg[a]}"')
        lines.append(f'    base[ACTIVE]="{bg[a]}"')
        lines.append("")
        lines.append(f'    fg[PRELIGHT]="{fg[a]}"')
        lines.append(f'    bg[PRELIGHT]="{bs[a]}"')
        lines.append(f'    text[PRELIGHT]="{fg[a]}"')
        lines.append(f'    base[PRELIGHT] ="{bs[a]}"')
        lines.append("")
        lines.append(f'    fg[SELECTED]="{fg[a]}"')
        lines.append(f'    bg[SELECTED]="{bs[a]}"')
        lines.append(f'    text[SELECTED]="{fg[a]}"')
        lines.append(f'    base[SELECTED]="{bs[a]}"')
        lines.append("")
        lines.append(f'    fg[INSENSITIVE]="{fg[a]}"')
        lines.append(f'    bg[INSENSITIVE]="{sel[a]}"')
        lines.append(f'    text[INSENSITIVE]="{fg[a]}"')
        lines.append(f'    base[INSENSITIVE]="{sel[a]}"')
        lines.append("}")
        lines.append("")

    return "\n".join(lines) + "\n"


def generate_gtk4_colors_css(bg, fg, ts, bs, sel, palette_name):
    """GTK4 uses the same format as GTK3."""
    return generate_gtk3_colors_css(bg, fg, ts, bs, sel, palette_name)


def find_palettes():
    """Find palette files in the palettes/ directory or bundled."""
    palettes = {}

    # Check for palettes directory next to this script
    for search_dir in [PALETTES_DIR,
                       os.path.join(SCRIPT_DIR, "..", "cde-extract-py3", "cdetheme1.4.2-python3", "palettes"),
                       os.path.join(SCRIPT_DIR, "..", "cde-extract", "cdetheme1.4", "cdetheme", "palettes")]:
        if os.path.isdir(search_dir):
            for f in sorted(os.listdir(search_dir)):
                if f.endswith('.dp'):
                    name = f[:-3]
                    palettes[name] = os.path.join(search_dir, f)

    return palettes


def preview_palette(bg, fg, ts, bs, sel, name):
    """Print a visual preview of the palette colors."""
    print(f"\n  Palette: {name}")
    print(f"  {'─' * 60}")
    print(f"  {'Slot':<6} {'Background':<14} {'Foreground':<14} {'TopShadow':<14} {'BotShadow':<14} {'Select':<14}")
    print(f"  {'─' * 60}")
    for a in range(1, 9):
        print(f"  {a:<6} {bg[a]:<14} {fg[a]:<14} {ts[a]:<14} {bs[a]:<14} {sel[a]:<14}")

    print(f"\n  Color roles in CDE:")
    print(f"    Slot 1: Active titlebar / highlight")
    print(f"    Slot 2: Inactive titlebar")
    print(f"    Slot 3: Workspace 3 backdrop tint")
    print(f"    Slot 4: Text fields / lists")
    print(f"    Slot 5: Main widget background (buttons, panels)")
    print(f"    Slot 6: Menu bar / dialogs")
    print(f"    Slot 7: Workspace 1 backdrop tint")
    print(f"    Slot 8: Icon area / secondary")
    print()


def apply_palette(palette_lines, palette_name):
    """Apply a palette to the CDE theme files."""
    bg, fg, ts, bs, sel = compute_colorset(palette_lines)

    preview_palette(bg, fg, ts, bs, sel, palette_name)

    # Write GTK3 cdecolors.css
    gtk3_dir = os.path.join(THEME_DIR, "gtk-3.0")
    if os.path.isdir(gtk3_dir):
        path = os.path.join(gtk3_dir, "cdecolors.css")
        with open(path, 'w') as f:
            f.write(generate_gtk3_colors_css(bg, fg, ts, bs, sel, palette_name))
        print(f"  [OK] Written: {path}")

    # Write GTK4 cdecolors.css
    gtk4_dir = os.path.join(THEME_DIR, "gtk-4.0")
    if os.path.isdir(gtk4_dir):
        path = os.path.join(gtk4_dir, "cdecolors.css")
        with open(path, 'w') as f:
            f.write(generate_gtk4_colors_css(bg, fg, ts, bs, sel, palette_name))
        print(f"  [OK] Written: {path}")

    # Write GTK2 cdecolors.rc
    gtk2_dir = os.path.join(THEME_DIR, "gtk-2.0")
    if os.path.isdir(gtk2_dir):
        path = os.path.join(gtk2_dir, "cdecolors.rc")
        with open(path, 'w') as f:
            f.write(generate_gtk2_colors_rc(bg, fg, ts, bs, sel, palette_name))
        print(f"  [OK] Written: {path}")

    print(f"\n  Done! CDE theme colors changed to '{palette_name}'.")
    print(f"  Restart your XFCE session or switch away and back to the CDE theme to apply.\n")


def main():
    palettes = find_palettes()

    if len(sys.argv) < 2 or sys.argv[1] == '--list':
        print("\nAvailable CDE Palettes:")
        print("=" * 50)
        names = sorted(palettes.keys(), key=str.lower)
        cols = 4
        for i in range(0, len(names), cols):
            row = names[i:i+cols]
            print("  " + "  ".join(f"{n:<18}" for n in row))
        print(f"\nTotal: {len(names)} palettes")
        print(f"\nUsage: python3 {sys.argv[0]} <PaletteName>")
        print(f"       python3 {sys.argv[0]} --preview <PaletteName>")
        print(f"       python3 {sys.argv[0]} --custom 180,140,100")
        print()
        return

    if sys.argv[1] == '--preview':
        if len(sys.argv) < 3:
            print("Usage: --preview <PaletteName>")
            return
        name = sys.argv[2]
        if name not in palettes:
            print(f"Palette '{name}' not found. Use --list to see available palettes.")
            return
        lines = read_palette_file(palettes[name])
        bg, fg, ts, bs, sel = compute_colorset(lines)
        preview_palette(bg, fg, ts, bs, sel, name)
        return

    if sys.argv[1] == '--custom':
        if len(sys.argv) < 3:
            print("Usage: --custom R,G,B  (values 0-255)")
            return
        try:
            r, g, b = [int(x.strip()) for x in sys.argv[2].split(',')]
        except ValueError:
            print("Error: provide R,G,B as comma-separated integers 0-255")
            return
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        # Create an 8-color palette based on variations of the base color
        import colorsys
        h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        palette_lines = []
        hue_offsets = [0.0, 0.45, 0.15, 0.08, 0.0, 0.55, 0.30, 0.05]
        val_offsets = [1.1, 0.85, 0.95, 0.9, 1.0, 0.88, 0.8, 0.92]
        for ho, vo in zip(hue_offsets, val_offsets):
            new_h = (h + ho) % 1.0
            new_s = min(1.0, s * 0.9)
            new_v = min(1.0, v * vo)
            nr, ng, nb = colorsys.hsv_to_rgb(new_h, new_s, new_v)
            palette_lines.append(f"#{int(nr*255):02x}{int(ng*255):02x}{int(nb*255):02x}")
        apply_palette(palette_lines, f"Custom({r},{g},{b})")
        return

    # Apply named palette
    name = sys.argv[1]
    if name not in palettes:
        # Try case-insensitive match
        for k in palettes:
            if k.lower() == name.lower():
                name = k
                break
        else:
            print(f"Palette '{name}' not found. Use --list to see available palettes.")
            return

    lines = read_palette_file(palettes[name])
    apply_palette(lines, name)


if __name__ == '__main__':
    main()
