#ifndef main_h
#define main_h

#include <Arduino.h>

#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ICM20948.h>
#include <TinyGPSPlus.h>
#include <Adafruit_DPS310.h>
#include <WiFi.h>
#include <esp_bt.h>
#include <HardwareSerial.h>

// PWM controller board
#include <Adafruit_PWMServoDriver.h>

// need this for writing logs to the microSD card
#include "FS.h"
#include "SD.h"
#include "SPI.h"

bool send_telemetry(byte msg_type, uint8_t length);

void writeFile(fs::FS &fs, const char * path, const char * message);
void appendFile(fs::FS &fs, const char * path, const char * message);

#endif