#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// ==========================================
// CONFIGURATION
// ==========================================
#define SENSOR_PIN 35   // AD8232 OUTPUT
#define SDN_PIN    33   // AD8232 Shutdown (HIGH = ON)
#define LO_PLUS    32   // Lead-off +
#define LO_MINUS   34   // Lead-off -

#define SAMPLE_DELAY_MS 8   // 125 Hz ECG

// UUIDs (must match Bangle.js)
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

// ==========================================

BLEServer* pServer = nullptr;
BLECharacteristic* pCharacteristic = nullptr;
bool deviceConnected = false;

class MyServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    deviceConnected = true;
  }
  void onDisconnect(BLEServer* pServer) {
    deviceConnected = false;
    delay(500);
    pServer->getAdvertising()->start();
  }
};

void setup() {
  Serial.begin(115200);
  delay(1000);

  // ---- AD8232 Power ----
  pinMode(SDN_PIN, OUTPUT);
  digitalWrite(SDN_PIN, HIGH);

  // ---- Pins ----
  pinMode(SENSOR_PIN, INPUT);
  pinMode(LO_PLUS, INPUT);
  pinMode(LO_MINUS, INPUT);

  // ---- ADC CONFIG (CRITICAL) ----
  analogReadResolution(12);        // 0–4095
  analogSetAttenuation(ADC_11db);  // 0–3.3V

  // ---- BLE ----
  BLEDevice::init("ESP32_ECG_Custom");

  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService* pService = pServer->createService(SERVICE_UUID);

  pCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_NOTIFY
  );
  pCharacteristic->addDescriptor(new BLE2902());

  pService->start();

  BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(false);
  pAdvertising->setMinPreferred(0x0);
  BLEDevice::startAdvertising();

  Serial.println("ESP32 ECG BLE Ready");
}

void loop() {
  if (!deviceConnected) return;

  // ---- Lead-off check ----
  int loPlus  = digitalRead(LO_PLUS);
  int loMinus = digitalRead(LO_MINUS);

  if (loPlus || loMinus) {
    // Do NOT send ECG if leads are off
    delay(SAMPLE_DELAY_MS);
    return;
  }

  // ---- Read RAW ECG ----
  uint16_t rawECG = analogRead(SENSOR_PIN); // 0–4095

  // ---- BLE Packet (2 bytes, little-endian) ----
  uint8_t packet[2];
  packet[0] = rawECG & 0xFF;
  packet[1] = (rawECG >> 8) & 0xFF;

  pCharacteristic->setValue(packet, 2);
  pCharacteristic->notify();

  // ---- Debug (optional, keep while testing) ----
  Serial.println(rawECG);

  delay(SAMPLE_DELAY_MS);
}
