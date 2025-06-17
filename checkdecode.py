#!/usr/bin/env python
# Script to observe and decode raw notification output from AC Infinity fan BLE characteristic.

import asyncio
import logging
import struct
import subprocess

from bleak import BleakClient, BleakScanner
from wrapt_timeout_decorator import timeout
from tenacity import retry, wait_exponential, stop_after_delay, before_sleep_log

UUID_READ_ADDRESS = "93B747B1-AD25-96FC-D7E4-0F64E49C462B"
DEFAULT_MAC_ADDRESS = "8D423FCD-72E2-9091-BAE4-D04AFC8A4AC5"

log = logging.getLogger("acinf-debug")


def decode_sensor_data(data: bytes):
    try:
        if len(data) != 54:
            return None
        # Example offsets based on observed patterns (may require tweaking)
        temp_raw = int.from_bytes(data[8:10], byteorder='big')
        humid_raw = int.from_bytes(data[10:12], byteorder='big')
        vpd_raw = int.from_bytes(data[12:14], byteorder='big')

        return {
            "temperature_c": round(temp_raw / 100.0, 2),
            "temperature_f": round(((temp_raw / 100.0) * 9 / 5) + 32, 2),
            "humidity": round(humid_raw / 100.0, 2),
            "vpd_kpa": round(vpd_raw / 100.0, 2)
        }
    except Exception as e:
        log.warning(f"Error decoding data: {e}")
        return None


@retry(wait=wait_exponential(multiplier=1, min=1, max=10),
       stop=stop_after_delay(30),
       before_sleep=before_sleep_log(log, logging.WARNING))
@timeout(30)
async def observe_raw_notifications(mac_address):
    if subprocess.call(['which', 'bluetoothctl'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
        subprocess.call(['bluetoothctl', 'disconnect', mac_address], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    async with BleakClient(mac_address) as client:
        def callback(sender, data):
            print(f"\n🔄 Raw notification from {sender}: {data.hex()} ({len(data)} bytes)")
            decoded = decode_sensor_data(data)
            if decoded:
                print("✅ Decoded sensor data:")
                for key, val in decoded.items():
                    print(f"    {key}: {val}")
            else:
                print("⚠️  Could not decode payload.")

        await client.start_notify(UUID_READ_ADDRESS, callback)

        print(f"📡 Listening for notifications from {mac_address}... (press Ctrl+C to stop)")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("👋 Exiting...")
            await client.stop_notify(UUID_READ_ADDRESS)


def main():
    import argparse
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description="Observe and decode BLE notifications from AC Infinity controller.")
    parser.add_argument('--mac', default=DEFAULT_MAC_ADDRESS, help='MAC address of the AC Infinity device')
    args = parser.parse_args()
    asyncio.run(observe_raw_notifications(args.mac))


if __name__ == '__main__':
    main()
