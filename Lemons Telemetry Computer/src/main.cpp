#include <Arduino.h>

// function headers
#include "main.h"

// create a GPS object for parsing
TinyGPSPlus gps;

// Create an instance of the ICM20948 sensor
Adafruit_ICM20948 icm;

// Pointers to the individual sensor objects
Adafruit_Sensor *icm_accel;
Adafruit_Sensor *icm_gyro;
Adafruit_Sensor *icm_mag;
Adafruit_Sensor *icm_temp;

long unsigned int heartbeat_time;
long unsigned int imu_time;
long unsigned int car_time;

byte tx_buffer[255]; // I'm sure I will never want this to be larger. NEVER
uint8_t tx_length;
byte error_code[2];

char hex_str[512]; // two characters per byte in tx_buffer, plus a newline, plus a null terminator
char log_name[11];

long unsigned int previous_rpm_time;
long unsigned int rpm_delta;
uint8_t number_rpm_measurements;

long unsigned int servo_time;
int servo_positions[5];
uint8_t servo_position;

int servo_steering_positions[50];
uint8_t servo_steering_position_head;
int servo_steering_position;

/* 
*
* Servo Driver Information
* 
*/
#define SERVOMIN  150 // This is the 'minimum' pulse length count (out of 4096)
#define SERVOMAX  650 // This is the 'maximum' pulse length count (out of 4096)
#define SERVO_FREQ 50 // Analog servos run at ~50 Hz updates

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// ISR must be fast and located in IRAM
void IRAM_ATTR handleRPMInterrupt() {
  long unsigned int time = micros();
  rpm_delta += time-previous_rpm_time;
  previous_rpm_time = time;
  number_rpm_measurements++;
}

void setup() {
  // turn off wifi
  WiFi.disconnect(true); 
  WiFi.mode(WIFI_OFF);

  // Serial.begin(115200);
  // while(!Serial){}
  // Serial.println("Testing Serial Port");

  /*
  *
  * RFD900ux-US setup
  * 
  */
  Serial1.begin(57600);

  /*
  *
  * GPS Module setup
  * 
  */
  Serial2.begin(9600);

  /*
  *
  * 9-DoF IMU setup
  * 
  */

  // Initialize I2C. On ESP32, Wire.begin() with no arguments
  // defaults to SDA = GPIO 21, SCL = GPIO 22.
  Wire.begin();

  // Try to initialize the ICM-20948 sensor
  if (!icm.begin_I2C()) {
    send_telemetry(7, 0);
  }

  // Get the sensor objects from the main ICM driver
  icm_accel = icm.getAccelerometerSensor();
  icm_gyro = icm.getGyroSensor();
  icm_temp = icm.getTemperatureSensor();

  /*
  *
  * SD Card Setup
  * 
  */

//  if(!SD.begin()){
//     Serial.println("Card Mount Failed");
//     return;
//   }
//   uint8_t card_type = SD.cardType();

//   if(card_type == CARD_NONE){
//     Serial.println("SD card not detected");
//     return;
//   }

//   // check how many folders there are in the root directory
//   uint32_t log_number = 0;

//   // create a new folder for the current logs
//   snprintf(log_name, sizeof(log_name), "%u", log_number);

//   // Find current length
//   size_t len = strlen(log_name);
//   snprintf(log_name + len, 5, ".txt");

//   Serial.println("Writing File");
//   writeFile(SD, log_name, "Log file of telemetry packets transmitted\n");

  // initialize the heartbeat counter to start sending heartbeat messages after the setup is done
  heartbeat_time = millis();
  imu_time = millis();
  car_time = millis();
  previous_rpm_time = micros();

  // PWM set up
  pwm.begin();
  pwm.setOscillatorFrequency(25000000);
  pwm.setPWMFreq(SERVO_FREQ);

  servo_positions[0] = 130;
  servo_positions[1] = 370;
  servo_positions[2] = 150;
  servo_positions[3] = 550;
  servo_positions[4] = 600;


  // interrupt handling
  attachInterrupt(digitalPinToInterrupt(35), handleRPMInterrupt, RISING);
}

void loop() {
  /*
  *
  * Get GPS Information
  * 
  */
  
  while (Serial2.available() > 0) {
    gps.encode(Serial2.read());
  }


  /*
  *
  * Get acceleration
  * 
  */
  //  /* Get a new normalized sensor event */
  sensors_event_t accel;
  sensors_event_t gyro;
  sensors_event_t temp;
  icm_temp->getEvent(&temp);
  icm_accel->getEvent(&accel);
  icm_gyro->getEvent(&gyro);

  /*
  *
  * Telemetry radio transmission
  * 
  */

  // send the IMU and Barometric Pressure data at 100 Hz
  if (millis() > imu_time + 10) {

    memcpy(tx_buffer+3, &temp.temperature, 4);
    // since we are using bytes, starting at the address plus four will copy into the correct location
    memcpy(tx_buffer+7, &accel.acceleration.x, 4);
    memcpy(tx_buffer+11, &accel.acceleration.y, 4);
    memcpy(tx_buffer+15, &accel.acceleration.z, 4);

    // now copy in the gyro data
    memcpy(tx_buffer+19, &gyro.gyro.x, 4);
    memcpy(tx_buffer+23, &gyro.gyro.y, 4);
    memcpy(tx_buffer+27, &gyro.gyro.z, 4);

    send_telemetry(0x03, 28);

    imu_time+=10;
  }

  if (millis() > car_time + 20) {

    uint16_t temp_adc = analogRead(34); // analog 1 filtered
    memcpy(tx_buffer+3, &temp_adc, 2);
    temp_adc = analogRead(35); // analog 2 filtered
    memcpy(tx_buffer+5, &temp_adc, 2);
    temp_adc = analogRead(32); // analog 3 filtered
    memcpy(tx_buffer+7, &temp_adc, 2);
    temp_adc = analogRead(25); // analog 4 filtered
    memcpy(tx_buffer+9, &temp_adc, 2);


    float avg = (float) rpm_delta / number_rpm_measurements;
    memcpy(tx_buffer+11, &avg, 4);

    send_telemetry(0x05, 12);

    // driver input updates occur on the same loop
    temp_adc = analogRead(26);
    memcpy(tx_buffer+3, &temp_adc, 2);

    temp_adc = analogRead(27);
    memcpy(tx_buffer+5, &temp_adc, 2);
    temp_adc = analogRead(14);
    memcpy(tx_buffer+7, &temp_adc, 2);

    send_telemetry(0x06, 6);

    car_time+=20;

  }

  // send a heartbeat message and GPS message at 1 Hz
  if (millis() > heartbeat_time + 1000) {
    send_telemetry(0x01, 0);
    
    // This is really stupid and inefficient but I am lazy
    double temp = gps.location.lat();
    memcpy(tx_buffer+3, &temp, 8);
    temp = gps.location.lng();
    memcpy(tx_buffer+11, &temp, 8);
    temp = gps.speed.mph();
    memcpy(tx_buffer+19, &temp, 8);
    temp = gps.course.deg();
    memcpy(tx_buffer+27, &temp, 8);
    temp = gps.altitude.feet();
    memcpy(tx_buffer+35, &temp, 8);
    uint32_t temp_sats = gps.satellites.value();
    memcpy(tx_buffer+43, &temp_sats, 4);
    temp = gps.hdop.hdop();
    memcpy(tx_buffer+47, &temp, 8);


    // GPS Message
    send_telemetry(0x02, 52);

    heartbeat_time+=1000;

    servo_steering_position = (analogRead(26)-2048)/2 + 400;
    // servo_steering_position = 0;
    // for (uint8_t i = 0; i < 50; i++) {
    //   servo_steering_position+=servo_steering_positions[i];
    // }
    // servo_steering_position /= 50;

    servo_steering_position = servo_steering_position < SERVOMIN ? SERVOMIN : servo_steering_position;
    servo_steering_position = servo_steering_position > SERVOMAX ? SERVOMAX : servo_steering_position;

    for (uint8_t servo_num = 8; servo_num < 16; servo_num++) {
      pwm.setPWM(servo_num, 0, servo_steering_position);
    }

    servo_steering_position_head+=1;
    servo_steering_position_head%=50;
  }

  /*
  * 
  * Servo Adjustments
  * 
  */
  if (millis() > servo_time + 5000)
  {
    servo_position += 1;
    servo_position %= 5;

    for (uint8_t servo_num = 0; servo_num < 8; servo_num++) {
      pwm.setPWM(servo_num, 0, servo_positions[servo_position]);
    }
    servo_time+=5000;
  }
}


/*
* Send telemetry information through serial port 1 (TX only)
* 
* Message type: 1 -- heartbeat; 2 -- GPS information; 3 -- IMU information; 4 -- Alt/Temp information
*               5 -- engine information; 6 -- car information; 7 -- debug information
* 
* 
* <START BYTE> <LENGTH BYTE> <MSG ID BYTE> <PAYLOAD> <ERROR CORRECTION BYTES (2)>
* 
*/
bool send_telemetry(byte msg_type, uint8_t length)
{
  // Populate the transmit buffer with what we want to send

  // Calculate the length of the message
  tx_length = length + 5;

  tx_buffer[0] = static_cast<unsigned char>(0xFE);   // This is the 'start' byte
  tx_buffer[1] = tx_length;   // This is the length of the message
  tx_buffer[2] = msg_type;

  // Error correction code
  error_code[0] = 0xAB; 
  error_code[1] = 0xCD;
  // Copy the error code into the end of the message
  memcpy(&tx_buffer[3+length], error_code, 2); 
  
  // Write the serial data
  Serial1.write(tx_buffer, tx_length); 

  for(int i = 0; i < tx_length; i++) {
    sprintf(&hex_str[i * 2], "%02X\n", tx_buffer[i]);
  }
  // append the telemetry message to the end of the file, can be decoded after the fact
  // appendFile(SD, log_name, hex_str);

  return true;
}

void writeFile(fs::FS &fs, const char * path, const char * message){
  Serial.printf("Writing file: %s\n", path);

  File file = fs.open(path, FILE_WRITE);
  if(!file){
    Serial.println("Failed to open file for writing");
    return;
  }
  if(file.print(message)){
    Serial.println("File written");
  } else {
    Serial.println("Write failed");
  }
  file.close();
}

void appendFile(fs::FS &fs, const char * path, const char * message){
  Serial.printf("Appending to file: %s\n", path);

  File file = fs.open(path, FILE_APPEND);
  if(!file){
    Serial.println("Failed to open file for appending");
    return;
  }
  if(file.print(message)){
    Serial.println("Message appended");
  } else {
    Serial.println("Append failed");
  }
  file.close();
}