#!/usr/bin/env bash
# ==============================================================================
# Project: RMDU-4301 / 4311 Unlock Toolkit
# Developer: DC-Voltage Network (https://github.com/dc-voltage)
# Description: Configure or Clean up VLAN 960 for RMDU Factory Configuration
# ==============================================================================

set -e

IFACE="${1:-eth0}"
ACTION="${2:-add}"
VLAN_ID=960
IP_ADDR="192.168.33.2/24"

echo "=========================================================="
echo "  DC-Voltage Network — RMDU VLAN 960 Configuration Tool   "
echo "=========================================================="

if [ "$EUID" -ne 0 ]; then
  echo "[!] Please run as root (sudo)."
  exit 1
fi

case "$ACTION" in
  add)
    echo "[+] Creating VLAN $VLAN_ID on interface $IFACE..."
    ip link add link "$IFACE" name "$IFACE.$VLAN_ID" type vlan id "$VLAN_ID" 2>/dev/null || true
    ip addr flush dev "$IFACE.$VLAN_ID" 2>/dev/null || true
    ip addr add "$IP_ADDR" dev "$IFACE.$VLAN_ID"
    ip link set "$IFACE.$VLAN_ID" up
    echo "[✓] VLAN $VLAN_ID interface ready with IP $IP_ADDR."
    echo "[*] Testing ping to RMDU (192.168.33.1)..."
    ping -c 2 -W 1 192.168.33.1 || echo "[!] RMDU not responding yet. Ensure cable is connected."
    ;;
  del|remove)
    echo "[-] Removing VLAN $VLAN_ID on $IFACE..."
    ip link delete "$IFACE.$VLAN_ID" 2>/dev/null || true
    nmcli con delete "$IFACE.$VLAN_ID" 2>/dev/null || true
    echo "[✓] Cleaned up $IFACE.$VLAN_ID."
    ;;
  *)
    echo "Usage: sudo $0 [interface (default: eth0)] [add|del]"
    exit 1
    ;;
esac
