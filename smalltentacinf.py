#!/usr/bin/env python3
# Observe raw BLE data from AC Infinity controller on macOS.

import asyncio
import logging
from bleak import BleakClient

# Constants
DEVICE_MAC = "93B747B1-AD25-96FC-D7E4-0F64E49C462B"  # 🧹 Replace with your desired AC Infinity MAC address
UUID_READ_ADDRESS = "70d51002-2c7f-4e75-ae8a-d758951ce4e0"

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("acinf-ble")

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
        logger.warning(f"Error decoding data: {e}")
        return None

async def main():
    async with BleakClient(DEVICE_MAC) as client:
        print(f"📱 Connected to {DEVICE_MAC}, listening for notifications... (Press Ctrl+C to stop)")

        def handle_notification(sender, data):
            decoded = decode_sensor_data(data)
            if decoded:
                print(f"📊 Decoded Data: {decoded}")
            else:
                print(f"🔄 Raw notification from {sender} ({len(data)} bytes): {data.hex()}")

        await client.start_notify(UUID_READ_ADDRESS, handle_notification)

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            await client.stop_notify(UUID_READ_ADDRESS)

if __name__ == "__main__":
    asyncio.run(main())