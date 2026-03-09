import threading
import asyncio
from ble_manager import BLEManager
from signal_processor import SignalProcessor
from visualizer import Visualizer

def main():
    # Your specific Bangle.js 1 Address
    WATCH_ADDRESS = "F8:5B:A5:14:2D:D9"

    # 1. Initialize the Signal Processor (The Brain)
    processor = SignalProcessor()

    # 2. Initialize the BLE Manager (The Connector)
    # We pass processor.update as the callback
    ble = BLEManager(address=WATCH_ADDRESS, callback=processor.update)

    # 3. Initialize the Visualizer (The Face)
    ui = Visualizer(processor)

    # 4. Start Bluetooth thread (Background)
    # Daemon=True ensures it closes when you close the graph window
    ble_thread = threading.Thread(target=lambda: asyncio.run(ble.run()), daemon=True)
    ble_thread.start()

    # 5. Start Plotting (Main Thread)
    print("Launching Visualization...")
    ui.start()

if __name__ == "__main__":
    main()