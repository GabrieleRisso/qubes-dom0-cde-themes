# Qubes XFCE Genmon Scripts

XFCE4 Generic Monitor (genmon) panel plugins for Qubes OS dom0.

## qubes-mem-genmon.sh

Displays per-VM memory allocation (actual / target / max / system total) in the XFCE panel with a detailed tooltip breakdown.

### Panel Display

```
.5 / 12.3 / 24.0 / 62.8
```

Shows: total actual / total target / total max / system total (in GB).

### Tooltip

Hovering shows a table of every running VM with memory columns:

```
domain                 act    tgt    max
────────────────────────────────────────────────
dom0                   3.2    4.0    4.0
sys-net                .4     .5    1.0
sys-firewall           .3     .5    1.0
sys-usb                .3     .4     .8
work                   2.1    4.0    8.0
personal               1.8    2.0    4.0
────────────────────────────────────────────────
TOTAL                  8.1   11.4   18.8
System Total          62.8
```

### Installation

1. Copy to dom0:

```bash
qvm-run --pass-io --no-gui VMNAME 'cat /path/to/qubes-mem-genmon.sh' > ~/qubes-mem-genmon.sh
chmod +x ~/qubes-mem-genmon.sh
```

2. Add a Generic Monitor to your XFCE panel:
   - Right-click panel > Panel > Add New Items > Generic Monitor
   - Set command to `~/qubes-mem-genmon.sh`
   - Set period to 5-10 seconds
   - Enable "Label" display

### How It Works

Reads Xen hypervisor memory data via `xl list` and `xenstore-read`:
- `memory/target` — current memory allocation
- `memory/meminfo` — actual memory in use
- `memory/static-max` / `memory/hotplug-max` — maximum allowed

Outputs genmon-compatible XML (`<txt>` for panel, `<tool>` for tooltip).

### Requirements

- Qubes OS dom0 with XFCE4
- `xfce4-genmon-plugin` package
- `xenstore-read` and `xl` commands (standard in dom0)

## License

GPL-2.0-or-later
