// =================================================
// Bangle.js 1 - High-Efficiency Comparison Dashboard
// No Graph -> Maximum CPU for Data Relay
// =================================================

// Blu Device 9
const ESP32_ADDR = "08:f9:e0:e3:fd:02 public";
// Blu Device 7
// const ESP32_ADDR = "08:f9:e0:e3:f9:c6 public";
const ECG_SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b";
const ECG_CHAR_UUID    = "beb5483e-36e1-4688-b7f5-ea07361b26a8";

// Variables
let currentPPG = 0;
let ppgConfidence = 0;
let ecgBPM = 0;
let lastPeakTime = Date.now();
let lastDraw = 0;

// Hardware Setup
Bangle.setLCDTimeout(0);
Bangle.setHRMPower(1);

// Handle PPG Sensor
Bangle.on("HRM", hrm => {
  currentPPG = hrm.bpm || 0;
  ppgConfidence = hrm.confidence || 0;
});

// Simple ECG Peak Detection (to get a number)
function calculateEcgBPM(val) {
  // If the raw signal spikes above a threshold (adjust if needed)
  if (val > 2200) { 
    let now = Date.now();
    let diff = now - lastPeakTime;
    if (diff > 400) { // Refractory period: ignore spikes too close together
      ecgBPM = Math.round(60000 / diff);
      lastPeakTime = now;
    }
  }
}

// Data Handler
function handleData(rawECG) {
  // 1. RELAY DATA (Always 1st priority)
  Bluetooth.write(rawECG + "," + currentPPG + "," + ppgConfidence + "\n");

  // 2. CALCULATE ECG BPM
  calculateEcgBPM(rawECG);

  // 3. REFRESH UI (Only 2 times per second for extreme efficiency)
  if (Date.now() - lastDraw < 500) return;
  lastDraw = Date.now();

  g.clear();
  
  // Header
  g.setFont("6x8", 2).setColor(0,1,0);
  g.drawString("ECG (Electrical)", 20, 30);
  g.setFont("Vector", 50).setColor(1,1,1);
  // g.drawString(ecgBPM > 0 ? ecgBPM : "--", 60, 60);
  g.drawString(rawECG, 60, 60);
  // Divider
  g.setColor(0.3, 0.3, 0.3).drawLine(10, 120, 230, 120);

  // Bottom Section
  g.setFont("6x8", 2).setColor(1,0.6,0);
  g.drawString("PPG (Optical)", 20, 140);
  g.setFont("Vector", 50).setColor(1,1,1);
  g.drawString(currentPPG > 0 ? currentPPG : "--", 60, 170);

  // Confidence Bar
  g.setColor(0,0.5,1);
  g.fillRect(60, 225, 60 + ppgConfidence, 230);
  g.setFont("6x8", 1).drawString("CONFIDENCE: " + ppgConfidence + "%", 60, 215);
}

// Optimized Connection Logic
function connectECG() {
  g.clear().setFont("Vector", 18).drawString("Connecting to\nBlu Device...", 10, 100);

  NRF.connect(ESP32_ADDR).then(gatt => {
    return gatt.getPrimaryService(ECG_SERVICE_UUID);
  }).then(service => {
    return service.getCharacteristic(ECG_CHAR_UUID);
  }).then(characteristic => {
    g.clear();
    characteristic.on('characteristicvaluechanged', event => {
      let val = event.target.value;
      let rawECG = val.getUint8(0) | (val.getUint8(1) << 8);
      handleData(rawECG);
    });
    return characteristic.startNotifications();
  }).catch(e => {
    g.clear().setColor(1,0,0).drawString("Retry in 3s...", 40, 100);
    setTimeout(connectECG, 3000);
  });
}

connectECG();