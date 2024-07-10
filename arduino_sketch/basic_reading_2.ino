// updated basic_reading

#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include "FS.h"
#include <ESP32Time.h>

#include "Freenove_WS2812_Lib_for_ESP32.h"

#define LED_PIN 1
Freenove_ESP32_WS2812 led = Freenove_ESP32_WS2812(1, LED_PIN, 0, TYPE_GRB);

Adafruit_MPU6050 mpu;
ESP32Time rtc;
int prevAccTime;

void setLED(uint8_t r,uint8_t g,uint8_t b) {
    led.setLedColorData(0, r, g, b);
    led.show();
}


#define BUFFER_SIZE 1000
struct SensorData {
  float accX;
  float accY;
  float accZ;
  float gyroX;
  float gyroY;
  float gyroZ;
  String timestamp;
};
SensorData buffer[BUFFER_SIZE];
int bufferIndex = 0;
unsigned long lastSaveTime = 0;

File Data;
SPIClass sdspi = SPIClass();
String filename;

void saveDataToSD() {
  Data = SD.open(filename, FILE_APPEND);
  if (Data) {
    for (int i = 0; i < bufferIndex; i++) {
      Data.print(buffer[i].accX);
      Data.print(",");
      Data.print(buffer[i].accY);
      Data.print(",");
      Data.print(buffer[i].accZ);
      Data.print(",");
      Data.print(buffer[i].gyroX);
      Data.print(",");
      Data.print(buffer[i].gyroY);
      Data.print(",");
      Data.print(buffer[i].gyroZ);
      Data.print(",");
      Data.println(buffer[i].timestamp);
    }
    Data.close();
  } else {
    Serial.println("Failed to open file for appending");
  }
  bufferIndex = 0;
}

void setup() {
  Serial.begin(115200);

  led.begin();
  led.setBrightness(1);
  //setLED(255,0,0);

  pinMode(SD_ENABLE, OUTPUT);
  digitalWrite(SD_ENABLE, LOW);
  sdspi.begin(VSPI_SCLK, VSPI_MISO, VSPI_MOSI, VSPI_SS);
  if (!SD.begin(VSPI_SS, sdspi)) {
    Serial.println("Failed to initialize SD card");
    while (1) {
      delay(10);
    }
  }

  if (!mpu.begin(0x68, &Wire1)) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_250_DEG); // 
  mpu.setFilterBandwidth(MPU6050_BAND_260_HZ);

  rtc.setTime(0);  // set time to 0 (unix epoch)

  filename = "/data_" + rtc.getTime("%F_%H-%M-%S") + ".csv";
  Data = SD.open(filename, FILE_WRITE);
  if (!Data) {
    Serial.println("Failed to create file");
    while (1) {
      delay(10);
    }
  }
  Data.print("AccX,AccY,AccZ,GyrX,GyrY,GyrZ,Time\n");
  Data.close();
  lastSaveTime = millis();
  prevAccTime = millis();

}

void loop() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  String timestampString = "000" + String(rtc.getMillis());
  String timestamp = String(rtc.getEpoch()) + timestampString.substring(timestampString.length() - 3);

  buffer[bufferIndex].accX = a.acceleration.x;
  buffer[bufferIndex].accY = a.acceleration.y;
  buffer[bufferIndex].accZ = a.acceleration.z;
  buffer[bufferIndex].gyroX = g.gyro.x;
  buffer[bufferIndex].gyroY = g.gyro.y;
  buffer[bufferIndex].gyroZ = g.gyro.z;
  buffer[bufferIndex].timestamp = timestamp;
  bufferIndex++;
  
  // alle 10 sekunden -> speichern dauert 0.5sekunden
  if (bufferIndex >= BUFFER_SIZE || millis() - lastSaveTime >= 10000) {  // write every 10 seconds
    saveDataToSD();
    lastSaveTime = millis();
  }
  // warte bis 10 milli vorbei sind
  if((millis() - prevAccTime) < 10) {
    delay(10-(millis() - prevAccTime));
    setLED(255,0,0);
  }
  
  Serial.println("acce: " + String(millis() - prevAccTime));
  prevAccTime = millis();
}
