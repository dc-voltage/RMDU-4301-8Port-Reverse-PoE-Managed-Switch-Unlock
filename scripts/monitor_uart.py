#!/usr/bin/env python3
"""
==============================================================================
Project: RMDU-4301 / 4311 Unlock Toolkit
Developer: DC-Voltage Network (https://github.com/dc-voltage)
Description: 38400 Baud UART Serial Monitor & Logger
==============================================================================
"""

import sys
import time
import argparse

try:
    import serial
except ImportError:
    print("Please install pyserial: pip3 install pyserial")
    sys.exit(1)

def main():
    print("=" * 60)
    print("  DC-Voltage Network — RMDU 38400 Baud Serial Monitor  ")
    print("=" * 60)

    parser = argparse.ArgumentParser(description="DC-Voltage Network — RMDU Serial Monitor")
    parser.add_argument("-p", "--port", default="/dev/ttyUSB0", help="Serial port (default: /dev/ttyUSB0)")
    parser.add_argument("-b", "--baud", type=int, default=38400, help="Baud rate (default: 38400)")
    parser.add_argument("-l", "--log", default="uart_session.log", help="Log file path")
    args = parser.parse_args()

    print(f"[*] Opening {args.port} at {args.baud} baud...")
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except Exception as e:
        print(f"[!] Error opening serial port {args.port}: {e}")
        sys.exit(1)

    print(f"[✓] Connected. Press Ctrl+C to stop. Saving log to {args.log}")
    with open(args.log, "a", encoding="utf-8", errors="replace") as f:
        f.write(f"\n--- Serial session started at {time.strftime('%Y-%m-%d %H:%M:%S')} (DC-Voltage Network) ---\n")
        try:
            while True:
                data = ser.read(ser.in_waiting or 1)
                if data:
                    text = data.decode("utf-8", errors="replace")
                    sys.stdout.write(text)
                    sys.stdout.flush()
                    f.write(text)
                    f.flush()
        except KeyboardInterrupt:
            print("\n[*] Exiting serial monitor.")
        finally:
            ser.close()

if __name__ == "__main__":
    main()
