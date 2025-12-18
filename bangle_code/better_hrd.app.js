// ===============================================
// Bangle.js: ECG Receiver + PPG Merger + Relay
// ===============================================

var ESP_SERVICE = "4fafc201-1fb5-459e-8fcc-c5c9c331914b";
var ESP_CHAR    = "beb5483e-36e1-4688-b7f5-ea07361b26a8";

// Graph variables
var pos = 0;
var lastY = 125; // Stores previous Y to draw a connected line
var localBPM = 0; 

// --- TUNING PARAMETERS ---
var midPoint = 135; // Adjust this to match your sensor's resting value
var gain = 4.0;     // Increase this (e.g., 5.0 or 6.0) to make waves taller

// --- SCREEN MANAGEMENT ---
Bangle.setLCDTimeout(0); // Keep screen on
Bangle.setLCDPower(1);   // Full brightness

// 1. SETUP INTERNAL PPG SENSOR
Bangle.setHRMPower(1);
Bangle.on('HRM', function(hrm) {
  localBPM = hrm.bpm; 
});

// 2. SETUP RELAY SERVICE
NRF.setServices({
  0x181A: {
    0x2A58: { 
      value : [0, 0],
      notify: true,
      readable: true
    }
  }
});

function drawGraph(ecgVal) {
  // --- A. RELAY BOTH SIGNALS ---
  try {
    NRF.updateServices({
      0x181A : {
        0x2A58 : {
          value : [ecgVal, localBPM], 
          notify: true
        }
      }
    });
  } catch(e) { } 

  // --- B. DRAW GRAPH ---
  var graphTop = 50;
  var graphBottom = 200;
  var graphCenter = (graphTop + graphBottom) / 2;

  // 1. Clear a sliver ahead of the current position
  g.setColor(0,0,0);
  var clearWidth = 8; 
  if (pos + clearWidth < 240) {
     g.fillRect(pos, graphTop, pos + clearWidth, graphBottom);
  } else {
     g.fillRect(pos, graphTop, 239, graphBottom);
     g.fillRect(0, graphTop, (pos + clearWidth) - 240, graphBottom);
  }

  // 2. Calculate Y position with Gain
  // We subtract midpoint to center it, multiply by gain to make it tall
  var y = graphCenter - ((ecgVal - midPoint) * gain);
  
  // Constrain y so it doesn't hit the text at top/bottom
  if (y < graphTop) y = graphTop;
  if (y > graphBottom) y = graphBottom;

  // 3. Draw a line from the last point to the current point
  g.setColor(0,1,0); 
  if (pos > 0) {
    g.drawLine(pos - 1, lastY, pos, y);
  } else {
    g.setPixel(pos, y);
  }
  lastY = y; // Save current Y for the next call
  
  // 4. Update PPG Number (Bottom Corner)
  g.setColor(0,0,0);
  g.fillRect(140, 210, 240, 240);
  g.setColor(1,1,1);
  g.setFont("6x8", 2);
  g.drawString("PPG:" + localBPM, 140, 220);

  pos++;
  if (pos >= 240) {
    pos = 0;
    // When wrapping, reset lastY to prevent a line drawing across the screen
    lastY = y; 
  }
}

function startScan() {
  g.clear();
  g.setFont("Vector", 18);
  g.setColor(1,1,1);
  g.drawString("Scanning for\nESP32...", 10, 50);
  
  NRF.requestDevice({ filters: [{ name: 'ESP32_ECG_Custom' }] }).then(function(device) {
    g.clear();
    g.drawString("Connecting...", 10, 50);
    return device.gatt.connect();
  }).then(function(gatt) {
    return gatt.getPrimaryService(ESP_SERVICE);
  }).then(function(service) {
    return service.getCharacteristic(ESP_CHAR);
  }).then(function(characteristic) {
    g.clear();
    g.setFont("6x8", 2);
    g.setColor(0,1,0);
    g.drawString("SYSTEM ACTIVE", 40, 10);
    g.setColor(1,1,1);
    g.drawString("Relaying ECG + PPG", 10, 30);
    
    characteristic.on('characteristicvaluechanged', function(event) {
      var val = event.target.value.getUint8(0);
      drawGraph(val);
    });
    return characteristic.startNotifications();
  }).catch(function(e) {
    g.clear();
    g.drawString("Retry in 3s...", 10, 50);
    setTimeout(startScan, 3000);
  });
}

// Start sequence
g.clear();
g.drawString("Initializing...", 10, 50);
setTimeout(startScan, 1000);