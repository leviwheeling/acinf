import asyncio
from bleak import BleakScanner

async def main():
    print("🔍 Scanning for 10 seconds...")
    devices = await BleakScanner.discover(timeout=10.0)

    print("\n🔎 Filtering potential AC Infinity controllers...\n")
    for d in devices:
        mfg_data = d.metadata.get('manufacturer_data', {})
        for mfg_id, data in mfg_data.items():
            if mfg_id != 76:  # 76 = Apple, skip those
                print(f"🧩 POSSIBLE AC INFINITY:")
                print(f"➡️  Address: {d.address}")
                print(f"    RSSI: {d.rssi}")
                print(f"    Manufacturer ID: {mfg_id}")
                print(f"    Raw Data: {data.hex()}")
                print()

    input("✅ Done. Press ENTER to close.")

if __name__ == "__main__":
    asyncio.run(main())
