#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// ==========================================
//  CONFIGURATION (Matched to your PCB)
// ==========================================
#define SENSOR_PIN 35  // The pin reading ~2224 (ECG Signal)
#define SDN_PIN    33  // The Shutdown pin (Must be HIGH to turn sensor ON)
// ==========================================

// UUIDs for the Service (Must match Bangle.js code)
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

BLEServer* pServer = NULL;
BLECharacteristic* pCharacteristic = NULL;
bool deviceConnected = false;

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      deviceConnected = true;
    };
    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
      delay(500); 
      // Restart advertising so watch can find us again if connection is lost
      pServer->getAdvertising()->start();
    }
};

void setup() {
  Serial.begin(115200);

  // 1. Setup Pins
  pinMode(SENSOR_PIN, INPUT);
  pinMode(SDN_PIN, OUTPUT);
  digitalWrite(SDN_PIN, HIGH); // Turn the AD8232 Sensor ON

  // 2. Create the BLE Device
  BLEDevice::init("ESP32_ECG_Custom");

  // 3. Create the BLE Server
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // 4. Create the BLE Service
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // 5. Create the BLE Characteristic
  pCharacteristic = pService->createCharacteristic(
                      CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_NOTIFY
                    );
  pCharacteristic->addDescriptor(new BLE2902());

  // 6. Start the service & Advertising
  pService->start();
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(false);
  pAdvertising->setMinPreferred(0x0);
  BLEDevice::startAdvertising();
  
  Serial.println("ESP32 Ready! Turning on Sensor...");
}

void loop() {
  if (deviceConnected) {
    // Read the sensor (0-4095)
    int rawValue = analogRead(SENSOR_PIN);
    
    // Scale 12-bit (0-4095) to 8-bit (0-255) for Bluetooth speed
    // This makes graphing on the watch much faster/smoother
    uint8_t value = map(rawValue, 0, 4095, 0, 255);
    
    // Send the data packet
    pCharacteristic->setValue(&value, 1);
    pCharacteristic->notify();
    
    // Send at ~25Hz (40ms delay)
    // Faster than this might lag the Bangle.js screen
    delay(40); 
  }
}