import asyncio
import csv
import datetime
from bleak import BleakScanner, BleakClient

# Look for Bangle.js
RELAY_SERVICE_UUID = "0000181a-0000-1000-8000-00805f9b34fb"
RELAY_CHAR_UUID    = "00002a58-0000-1000-8000-00805f9b34fb"

FILENAME = "study_data_ecg_vs_ppg.csv"

async def run():
    print("🔍 Scanning for Bangle.js...")
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: d.name and "Bangle" in d.name
    )

    if not device:
        print("❌ Bangle.js not found. Disconnect the IDE!")
        return

    print(f"✅ Found {device.name}. Connecting...")

    async with BleakClient(device) as client:
        print(f"🔗 Connected! Logging synchronized data...")

        with open(FILENAME, mode='a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            
            # Create Headers if file is new
            if csv_file.tell() == 0:
                writer.writerow(["Timestamp", "ESP32_ECG_Raw", "Bangle_PPG_BPM"])
            
            def notification_handler(sender, data):
                # Unpack the 2 bytes we sent from the watch
                # data[0] = ECG (0-255)
                # data[1] = PPG (0-200)
                
                if len(data) >= 2:
                    ecg_val = data[0]
                    ppg_val = data[1]
                    
                    now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    
                    print(f"[{now}] ⚡ECG: {ecg_val} | ❤️PPG: {ppg_val}")
                    writer.writerow([now, ecg_val, ppg_val])
                    csv_file.flush()

            await client.start_notify(RELAY_CHAR_UUID, notification_handler)

            print("📊 Logging active! Press Ctrl+C to stop.")
            while True:
                await asyncio.sleep(1)

if _name_ == "_main_":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nStopped.")