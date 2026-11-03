# RMDU-4301 / 4311 — 8-Port Reverse PoE Managed Switch & Router Unlock Guide

<p align="center">
  <a href="https://github.com/dc-voltage"><img src="https://img.shields.io/badge/Author-DC--Voltage-blue.svg?style=for-the-badge&logo=github" alt="Author"></a>
  <a href="#hardware-specifications"><img src="https://img.shields.io/badge/Device-RMDU--4301%20%2F%204311-orange.svg?style=for-the-badge" alt="Device"></a>
  <a href="#hardware-specifications"><img src="https://img.shields.io/badge/SoC-Realtek%20RTL8197FS-success.svg?style=for-the-badge" alt="SoC"></a>
  <a href="#hardware-specifications"><img src="https://img.shields.io/badge/Switch-8--Port%20Managed%20RTL83xx-blueviolet.svg?style=for-the-badge" alt="Switch"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License"></a>
</p>

A comprehensive reverse-engineering, hardware analysis, and unlock guide for the **RMDU-4301 / 4311** (Remote / Reverse Managed Distribution Unit). This guide explains how to repurpose this 8-port telecom Reverse-PoE outdoor distribution unit into a versatile **8-Port Managed Switch**, a **VLAN Segmentation Lab**, or a **Standalone Gateway Router** for home labs, network testing, and multi-device development.

---

## 📋 Table of Contents
1. [Overview & Capabilities](#-overview--capabilities)
2. [Hardware Specifications](#-hardware-specifications)
3. [Reverse PoE Architecture & Powering](#-reverse-poe-architecture--powering)
4. [UART Debug Interface & Baud Rate Fix](#-uart-debug-interface--baud-rate-fix)
5. [Root Shell & Authentication](#-root-shell--authentication)
6. [Web UI Access & Default VLAN 960 Bypass](#-web-ui-access--default-vlan-960-bypass)
7. [Default Credentials & Password Formula](#-default-credentials--password-formula)
8. [Hidden Engineer Web Interfaces](#-hidden-engineer-web-interfaces)
9. [Operation Modes: Switch vs Router](#-operation-modes-switch-vs-router)
10. [Hardware Telemetry & Control (`/proc/comtrend/`)](#-hardware-telemetry--control)
11. [Bundled Scripts](#-bundled-scripts)
12. [Disclaimer](#-disclaimer)

---

## 🔍 Overview & Capabilities

The **RMDU-4301 / 4311** is an outdoor-grade distribution unit originally manufactured on the Comtrend / Realtek MSDK platform for FTTB (Fiber to the Building) deployments. Instead of drawing power from an external AC wall outlet, it utilizes **Reverse PoE (PoE IN)**, allowing subscriber PoE injectors to power the unit.

By unlocking and reconfiguring the firmware:
* **7-to-1 Port Multiplier:** Expand a laptop's single USB-to-LAN adapter into 7 high-speed Ethernet ports.
* **802.1Q VLAN Lab:** Create 7 isolated virtual network interfaces on a single physical cable for security testing or homelab isolation.
* **Standalone Router:** Run full NAT, PPPoE / DHCP WAN, DHCP Server, DMZ, and Port Forwarding.
* **Network Tap:** Perform live packet captures and port mirroring directly from hardware.

---

## ⚙️ Hardware Specifications

| Component | Specification |
| :--- | :--- |
| **Main SoC** | Realtek RTL8197FS (MIPS 24Kc V8.5 @ ~1GHz / 666 BogoMIPS) |
| **RAM** | 64 MB DDR SDRAM |
| **Flash Storage** | Dual-Bank SPI NOR/NAND Flash (MTD partitions: `boot`, `setting`, `linux`, `rootfs` + Bank 2) |
| **Switch Controller** | Realtek RTL83xx 8-Port Switch with 802.1Q, Port Mirroring & IGMP Snooping |
| **Power Controller** | Texas Instruments (TI) MSP430 MCU (`0xBB82`) managing eFuses, power-sharing, and failover |
| **Operating System** | Embedded Linux Kernel 3.10.90 (Realtek MSDK) with BusyBox v1.13.4 |
| **Interfaces** | 8x FastEthernet/Gigabit RJ45 Ports (with Reverse PoE sensing) + Internal UART Debug Header |

---

## ⚡ Reverse PoE Architecture & Powering

Unlike standard PoE switches that provide power out (PSE) to cameras or phones, the RMDU is a **Reverse PoE (PoE PD)** device:

1. **How It Works:** Connect a standard 24V or 48V passive PoE injector to any active port.
2. **Power Sharing & Failover:** The onboard TI MCU continuously monitors voltage across all 8 ports (`/proc/comtrend/P0_mV` to `P7_mV`). If one subscriber disconnects their injector, the unit automatically transfers power draw to another active port without rebooting.
3. **Powering with a Laptop:** 
   Connect a PoE injector between the laptop and the RMDU:
   ```text
   [Laptop USB-LAN Adapter]
         │ (Standard Ethernet Patch Cable)
         ▼
   [PoE Injector: LAN / Data Port]
   [PoE Injector: PoE Port] ─── (Plugged to Wall Socket)
         │ (Cable carrying Data + 24V/48V Power)
         ▼
   [RMDU Port 6]  <── Powers the RMDU & establishes Ethernet link!
   ```
   *Ports 0, 1, 2, 3, 4, 5, and 7 remain completely free for other devices.*

---

## 📟 UART Debug Interface & Baud Rate Fix

An internal 4-pin UART header is available on the PCB (Pinout: `GND`, `TX`, `RX`, `3.3V`).

> [!WARNING]
> **Critical Baud Rate Note:**  
> Standard Linux routers typically use 115200 baud. However, the Realtek RTL8197FS SoC kernel is explicitly compiled for **`38400 baud`**:
> ```text
> console=ttyS0,38400 root=/dev/mtdblock3
> ```
> Connecting at `115200` baud causes severe framing errors and raw binary escape sequence floods that cause terminal emulators (like `minicom`) to crash with segmentation faults.

### Recommended Connection Commands:

```bash
# Using picocom (Recommended — does not leave stale lock files)
picocom -b 38400 /dev/ttyUSB0

# Using minicom
minicom -D /dev/ttyUSB0 -b 38400

# Using screen
screen /dev/ttyUSB0 38400
```

*(If minicom crashes and complains that `/var/lock/LCK..ttyUSB0` is locked, remove it with `sudo rm -f /var/lock/LCK..ttyUSB0`)*

---

## 🔓 Root Shell & Authentication

The device provides **unrestricted local Root access**:
* **Serial Console:** Spawns a root prompt directly upon boot with **no password required**:
  ```text
  root::0:0:root:/:/bin/sh
  # 
  ```
* **Telnet (Port 23):** Running by default on `0.0.0.0:23` via `/etc/init.d/rcS`.
* **SSH (Port 22):** Running Dropbear by default (`dropbear -B`).

---

## 🌐 Web UI Access & Default VLAN 960 Bypass

In factory configuration, the management bridge `br0` (`192.168.33.1`) is bound exclusively to **VLAN ID 960** (`eth0.960`). Connecting a normal computer with an untagged cable will result in dropped packets and an inaccessible web interface.

### Method 1: Connect using a Tagged VLAN on Host (Temporary)
Run the bundled script or configure manually:
```bash
sudo ip link add link eth0 name eth0.960 type vlan id 960
sudo ip addr add 192.168.33.2/24 dev eth0.960
sudo ip link set eth0.960 up
```

### Method 2: Permanently Disable VLAN for Untagged Access (Recommended)
1. Access the root shell via UART or Web UI (`/8021q_vlan.htm`).
2. Delete the VLAN 960 rule:
   ```bash
   flash set VLAN_OPMODE 0
   brctl delif br0 eth0.960 2>/dev/null
   brctl addif br0 eth0
   ```
3. Now all 8 ports respond directly on standard untagged Ethernet at `http://192.168.33.1`.

---

## 🔑 Default Credentials & Password Formula

* **Web UI URL:** `http://192.168.33.1`
* **Admin Username:** `admin`
* **Default Admin Password Formula:**
  ```text
  [MODEL_NAME][MAC_ADDRESS_IN_LOWERCASE]
  Example: RMDU4311 + a01842xxxxxx => RMDU4311a01842xxxxxx
  ```
* **Guest User:** `Guest` / `Guest`
* **SNMP Communities:**
  - Read-Only: `public`
  - Read-Write: `private`

---

## 🛠️ Hidden Engineer Web Interfaces

The Boa web server includes several powerful diagnostic and management pages not listed in standard user navigation:

| Hidden Endpoint | Description & Utility |
| :--- | :--- |
| **`/syscmd.htm`** | **Web Shell / Arbitrary Command Execution:** Run arbitrary Linux shell commands from the browser and inspect stdout. Submits to `/boafrm/formSysCmd`. |
| **`/super_password.htm`** | **Super User Credentials:** Configure high-privilege administrative and root credentials. |
| **`/8021q_vlan.htm`** | **802.1Q VLAN Management:** Full port-based and tag-based VLAN trunking configuration. |
| **`/opmode.htm`** | **Operation Mode Selector:** Toggle between Gateway (Router) and Bridge (Switch) modes. |
| **`/rtct.htm`** | **Realtek Cable Diagnostic:** Tests cable lengths and detects open/short pair faults across all 8 ports. |
| **`/capture.htm`** | **Hardware Frame Capture:** Capture raw switch frames (`switch_capture`). |
| **`/mirror.htm`** | **Port Mirroring:** Mirror ingress/egress traffic from target ports to a dedicated monitor port for Wireshark analysis. |
| **`/mqttConfig.htm`** | **MQTT Client Settings:** Configure telemetry brokers, topics, and keep-alive intervals. |
| **`/openvpn.htm`** | **OpenVPN Tunneling:** Full client/server OpenVPN setup. |
| **`/tr069config.htm`** | **CWMP / TR-069 Configuration:** Modify or disable remote ACS management. |

---

## 🔀 Operation Modes: Switch vs Router

### 1. Bridge Mode (8-Port Managed Switch — Recommended for Homelab / Laptop Expansion)
* **Value:** `OP_MODE=1`
* Connect your primary home router/modem to **Port 0**.
* Connect your laptop to **Port 6** (via PoE injector).
* Connect up to 6 target devices to **Ports 1, 2, 3, 4, 5, 7**.
* All devices receive IP addresses from your main home router via DHCP. Your laptop maintains uninterrupted Internet while communicating directly with all 6 target devices simultaneously!

### 2. Gateway Mode (Standalone NAT Router)
* **Value:** `OP_MODE=0`
* **Port 7** acts as WAN (supports PPPoE, Dynamic DHCP, and Static IP).
* Ports 0 to 6 act as LAN with the built-in DHCP server serving `192.168.33.100 - 192.168.33.200`.
* Activates Linux `iptables` NAT, SPI Firewall, Port Forwarding, and DMZ.

### Changing Mode via CLI:
```bash
# Switch to Bridge Mode (Switch)
flash set OP_MODE 1
init.sh ap all

# Switch to Gateway Mode (Router)
flash set OP_MODE 0
init.sh gw all
```

---

## 📊 Hardware Telemetry & Control (`/proc/comtrend/`)

The Realtek kernel driver exposes live hardware parameters under `/proc/comtrend/`:

```bash
# Read live temperature sensor
cat /proc/comtrend/Celsius
# Output: 27.4 °C

# Identify which port is currently supplying PoE power
cat /proc/comtrend/CurSupplyPort
# Output: 06 (Port 6)

# Read port voltages (in millivolts)
cat /proc/comtrend/P0_mV   # Port 0
cat /proc/comtrend/P6_mV   # Port 6

# Control individual port status LEDs (0 = Off, 1 = Green, 2 = Amber/Blink)
echo 1 > /proc/comtrend/LED1
echo 0 > /proc/comtrend/LED_R
echo 1 > /proc/comtrend/LED_G
```

---

## 📂 Bundled Scripts

* **[`scripts/setup_vlan960.sh`](scripts/setup_vlan960.sh)**: Automates tagged VLAN 960 interface creation and teardown on Linux hosts.
* **[`scripts/monitor_uart.py`](scripts/monitor_uart.py)**: Python UART reader preset to 38400 baud with session logging.
* **[`scripts/rmdu_control.py`](scripts/rmdu_control.py)**: Command-line utility to query hardware sensors, port voltages, and switch operation modes.

---

## ⚠️ Disclaimer

This repository is strictly for research, educational, and hardware repurposing purposes. Modifying network devices should be done responsibly and on equipment you legally own. All hardware trademarks belong to their respective manufacturers.
