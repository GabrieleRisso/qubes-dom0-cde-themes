# Qubes OS dom0 CDE Themes

Authentic CDE (Common Desktop Environment) themes for Qubes OS dom0 running XFCE4. Uses the original Motif color calculation algorithms to generate pixel-perfect CDE color schemes for GTK2, GTK3, and GTK4.

## What's Included

- **131 CDE palettes** from HP VUE, Solaris, IRIX, and community collections (`.dp` format)
- **CDE-Theme** base XFCE4 theme with Motif-style widgets, window borders, and 3D bevels
- **Chicago95** cursors and icon sets
- **CDE backdrops** for workspace backgrounds
- **Retro fonts** (Cronyx Cyrillic)

## Quick Start

```bash
# Copy to dom0 (from a VM):
qvm-run --pass-io --no-gui VMNAME 'tar czf - -C /path/to qubes-dom0-cde-themes' | tar xzf - -C ~/

# Install base theme and assets
cp -r .themes/CDE-Theme ~/.themes/
cp -r .icons/* ~/.icons/
cp -r .fonts/* ~/.fonts/
fc-cache -f

# Generate all 131 palette variants
python3 generate-all-themes.py

# Apply a palette (e.g., HPVue, Crimson, Solaris, DarkBlue)
python3 change-cde-colors.py HPVue
```

Then switch to the `CDE-HPVue` theme in XFCE Settings > Appearance.

## Available Palettes

131 palettes including: Africa, Alpine, Arizona, Autumn, Cabernet, Charcoal, Chocolate, Crimson, DarkBlue, Default, DefaultVUE, Delphinium, Desert, Golden, HPVue, IRIX, Lilac, Mustard, Neptune, NorthernSky, Ocean, Olive, Orchid, Pastel, Savannah, Solaris, SouthWest, and many more.

```bash
python3 change-cde-colors.py --list      # list all palettes
python3 change-cde-colors.py --preview Crimson  # preview colors
python3 change-cde-colors.py --custom 100,120,180  # custom RGB
```

## How It Works

`change-cde-colors.py` implements the authentic Motif/CDE color calculation from the original CDE source code:

- Reads 8-color CDE `.dp` palette files
- Computes foreground, top-shadow, bottom-shadow, and select colors using Motif luminosity thresholds
- Generates `cdecolors.css` (GTK3/GTK4) and `cdecolors.rc` (GTK2)

`generate-all-themes.py` creates a complete XFCE4 theme directory for every palette, using symlinks for shared assets (xfwm4 borders, images) to save disk space.

## Screenshots

The CDE themes reproduce the classic look of:
- **HP VUE** (Visual User Environment) from HP-UX
- **Solaris CDE** from Sun Microsystems
- **IRIX** from SGI
- Classic CDE from various UNIX workstations

## Requirements

- Qubes OS 4.x with XFCE4 dom0
- Python 3 (no external dependencies)

## License

Palette files originate from the CDE open-source project (LGPL). Theme generation scripts are original work.
