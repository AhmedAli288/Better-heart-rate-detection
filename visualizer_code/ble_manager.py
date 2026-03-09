import asyncio
from bleak import BleakClient

class BLEManager:
    # Industry standard Nordic UART Service UUIDs
    UART_TX_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
    
    def __init__(self, address, callback):
        self.address = address
        self.callback = callback # Function to send data to SignalProcessor

    async def run(self):
        print(f"Connecting to Bangle.js at {self.address}...")
        try:
            async with BleakClient(self.address) as client:
                print("Connected! Streaming Data...")
                
                buffer = ""

                def notification_handler(sender, data):
                    nonlocal buffer
                    try:
                        # Decode incoming bytes to string
                        buffer += data.decode()
                        # Process complete lines
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            if line.strip():
                                self.callback(line)
                    except Exception as e:
                        print(f"Data Error: {e}")

                # Subscribe to the UART TX characteristic
                await client.start_notify(self.UART_TX_CHAR_UUID, notification_handler)
                
                # Keep the connection alive
                while True:
                    await asyncio.sleep(1)
                    
        except Exception as e:
            print(f"Bluetooth Connection Failed: {e}")