#!/usr/bin/env python3
"""
RMDU Device Manager & Telemetry Reader
Can query hardware sensor data, temperature, PoE port states, and control modes.
"""

import sys
import time
import argparse

try:
    import serial
except ImportError:
    print("Please install pyserial: pip3 install pyserial")
    sys.exit(1)

def run_command(ser, cmd, wait=0.5):
    ser.reset_input_buffer()
    ser.write(cmd.encode() + b"\n")
    time.sleep(wait)
    out = b""
    while ser.in_waiting:
        chunk = ser.read(ser.in_waiting)
        out += chunk
        time.sleep(0.05)
    return out.decode("utf-8", errors="replace").strip()

def main():
    parser = argparse.ArgumentParser(description="RMDU Hardware Control & Info")
    parser.add_argument("-p", "--port", default="/dev/ttyUSB0", help="Serial port")
    parser.add_argument("-b", "--baud", type=int, default=38400, help="Baud rate")
    parser.add_argument("--info", action="store_true", help="Display SoC, temperature, and PoE status")
    parser.add_argument("--set-mode", choices=["bridge", "gateway"], help="Set operation mode (bridge or gateway)")
    args = parser.parse_args()

    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except Exception as e:
        print(f"Error opening {args.port}: {e}")
        sys.exit(1)

    # Wake prompt
    ser.write(b"\x03\n")
    time.sleep(0.2)

    if args.info:
        print("=== Hardware Information ===")
        cpu = run_command(ser, "cat /proc/cpuinfo | grep 'system type'")
        mem = run_command(ser, "free | grep Mem")
        temp = run_command(ser, "cat /proc/comtrend/Celsius 2>/dev/null")
        pwr_port = run_command(ser, "cat /proc/comtrend/CurSupplyPort 2>/dev/null")
        mcu_ver = run_command(ser, "cat /proc/comtrend/MCU_fw_ver 2>/dev/null")
        opmode = run_command(ser, "flash get OP_MODE")

        print(f"SoC Type: {cpu}")
        print(f"Memory: {mem}")
        print(f"Temperature: {temp}°C")
        print(f"Active Power Port (Reverse PoE): Port {pwr_port}")
        print(f"TI MCU Firmware: v{mcu_ver}")
        print(f"Operation Mode: {opmode}")

        print("\n=== PoE Port Voltages ===")
        for port in range(8):
            mv = run_command(ser, f"cat /proc/comtrend/P{port}_mV 2>/dev/null")
            print(f"Port {port}: {mv} mV")

    if args.set_mode:
        mode_val = 1 if args.set_mode == "bridge" else 0
        print(f"[*] Setting OP_MODE to {mode_val} ({args.set_mode})...")
        run_command(ser, f"flash set OP_MODE {mode_val}")
        check = run_command(ser, "flash get OP_MODE")
        print(f"[✓] Flash set: {check}")
        print("[*] Reinitializing network stack...")
        init_arg = "ap" if args.set_mode == "bridge" else "gw"
        run_command(ser, f"init.sh {init_arg} all", wait=2.0)
        print("[✓] Operation mode changed successfully.")

    ser.close()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.append("--info")
    main()
