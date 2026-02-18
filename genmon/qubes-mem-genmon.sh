#!/bin/bash
# Qubes Memory Monitor for XFCE Generic Monitor
# Displays memory allocation via xenstore paths

# Convert KB to GB with one decimal
kb_to_gb() {
    local kb=$1
    if [ -z "$kb" ] || [ "$kb" = "0" ]; then
        echo ".0"
    else
        local result=$(awk "BEGIN {printf \"%.1f\", $kb/1048576}")
        echo "$result" | sed 's/^0\./\./'
    fi
}

mb_to_gb() {
    local mb=$1
    if [ -z "$mb" ] || [ "$mb" = "0" ]; then
        echo ".0"
    else
        local result=$(awk "BEGIN {printf \"%.1f\", $mb/1024}")
        echo "$result" | sed 's/^0\./\./'
    fi
}

# Initialize totals
total_act=0
total_tgt=0
total_max=0

# Build tooltip
tooltip=""

# Get all running domains including dom0
while read vm_name domid rest; do
    if [ -z "$vm_name" ] || [ -z "$domid" ]; then
        continue
    fi

    if [ "$domid" = "0" ]; then
        vm_name="dom0"
    fi
    
    # Read xenstore memory values
    tgt_kb=$(xenstore-read /local/domain/$domid/memory/target 2>/dev/null || echo "0")
    act_kb=$(xenstore-read /local/domain/$domid/memory/meminfo 2>/dev/null)
    static_max_kb=$(xenstore-read /local/domain/$domid/memory/static-max 2>/dev/null)
    hotplug_max_kb=$(xenstore-read /local/domain/$domid/memory/hotplug-max 2>/dev/null)
    act_kb="${act_kb:-${tgt_kb:-0}}"
    max_kb="${hotplug_max_kb:-${static_max_kb:-0}}"
    
    # Convert to GB
    act_gb=$(kb_to_gb $act_kb)
    tgt_gb=$(kb_to_gb $tgt_kb)
    max_gb=$(kb_to_gb $max_kb)
    
    # Add to totals (skip if values are 0)
    if [ "$act_kb" != "0" ]; then
        total_act=$((total_act + act_kb))
    fi
    if [ "$tgt_kb" != "0" ]; then
        total_tgt=$((total_tgt + tgt_kb))
    fi
    if [ "$max_kb" != "0" ]; then
        total_max=$((total_max + max_kb))
    fi
    
    # Add to tooltip with column alignment
    tooltip="${tooltip}$(printf '%-20s %5s  %5s  %5s' "$vm_name" "$act_gb" "$tgt_gb" "$max_gb")\n"
done < <(xl list | tail -n +2)

# Get system total memory
system_total_mb=$(xl info | grep total_memory | awk '{print $3}')
system_total_gb=$(mb_to_gb $system_total_mb)

# Convert totals to GB
total_act_gb=$(kb_to_gb $total_act)
total_tgt_gb=$(kb_to_gb $total_tgt)
total_max_gb=$(kb_to_gb $total_max)

# Add header and footer to tooltip
header="<span font_desc='monospace'>"
header="${header}$(printf '%-20s %5s  %5s  %5s' 'domain' 'act' 'tgt' 'max')\n"
header="${header}$(printf '%s' '────────────────────────────────────────────────')\n"

footer="$(printf '%s' '────────────────────────────────────────────────')\n"
footer="${footer}$(printf '%-20s %5s  %5s  %5s' 'TOTAL' "$total_act_gb" "$total_tgt_gb" "$total_max_gb")\n"
footer="${footer}$(printf '%-20s %5s' 'System Total' "$system_total_gb")"
footer="${footer}</span>"

tooltip="${header}${tooltip}${footer}"

# Output for genmon
echo "<txt> $total_act_gb / $total_tgt_gb / $total_max_gb / $system_total_gb </txt>"
echo -e "<tool>$tooltip</tool>"
