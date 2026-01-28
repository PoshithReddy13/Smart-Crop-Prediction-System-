#include <WiFi.h>
#include <HTTPClient.h>
#include <ModbusMaster.h>
#include "DHT.h"

// -----------------------------
// WiFi Credentials
// -----------------------------
const char* ssid = "Nithinreddy";
const char* password = "12345678";

// Flask server endpoint
const char* serverName = "http://10.252.52.83:5000/sensor";

// -----------------------------
// RS485 / Modbus Setup
// -----------------------------
#define RE_DE 4
#define RX_PIN 16
#define TX_PIN 17

HardwareSerial RS485Serial(2);
ModbusMaster node;

// -----------------------------
// DHT Sensor Setup
// -----------------------------
#define DHTPIN 15
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// RS485 Direction Control
void preTransmission() { digitalWrite(RE_DE, HIGH); }
void postTransmission() { digitalWrite(RE_DE, LOW); }

void setup() {
  Serial.begin(115200);
  pinMode(RE_DE, OUTPUT);
  digitalWrite(RE_DE, LOW);

  RS485Serial.begin(9600, SERIAL_8N1, RX_PIN, TX_PIN);
  node.begin(1, RS485Serial);
  node.preTransmission(preTransmission);
  node.postTransmission(postTransmission);

  dht.begin();

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void loop() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  node.readHoldingRegisters(0x0002, 2);
  float ec = node.getResponseBuffer(0);
  float ph = node.getResponseBuffer(1) / 10.0;

  node.readHoldingRegisters(0x001E, 3);
  int P = node.getResponseBuffer(1);
  int K = node.getResponseBuffer(2);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");

    String json = "{";
    json += "\"temperature\":" + String(temperature) + ",";
    json += "\"humidity\":" + String(humidity) + ",";
    json += "\"ec\":" + String(ec) + ",";
    json += "\"ph\":" + String(ph) + ",";
    json += "\"phosphorus\":" + String(P) + ",";
    json += "\"potassium\":" + String(K);
    json += "}";

    http.POST(json);
    http.end();
  }

  delay(10000);
}
