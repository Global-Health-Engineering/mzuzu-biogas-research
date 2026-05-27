#include <OneWire.h>
#include <DallasTemperature.h>

#define GAS_HEATER_TURN_ON_THRESHOLD 50.0

// DS18B20 ROMs (hard-coded)
// 2881774700000099
// 28BF1147000000EA

byte sensor0ROM[8] = { 0x28, 0x8D, 0x2A, 0x55, 0x00, 0x00, 0x00, 0xA2 }; // is at the bottom
byte sensor1ROM[8] = { 0x28, 0xBF, 0x11, 0x47, 0x00, 0x00, 0x00, 0xEA }; // is at the top

// PIN definitions
const int PUMP_OUT_PIN = 2;
const int TEMP_SENSOR_PIN = 3;
const int VALVE_EN = 9; // 32kHz PWM
const int VALVE_1_EN2 = 7;
const int VALVE_1_EN4 = 8;
const int VALVE_2_EN2 = 4;
const int VALVE_2_EN4 = 5;

bool valveState = 0;
bool pumpState = 0;

// OneWire + DallasTemperature
OneWire oneWire(TEMP_SENSOR_PIN);

DallasTemperature sensors(&oneWire);

DeviceAddress deviceAddress; // variable to store the device address

float temp0 = 0.0;
float temp1 = 0.0;


// Valve control helpers
void openValve(int valveNumber) {
  switch (valveNumber) {
    case 1:
      digitalWrite(VALVE_1_EN2, HIGH);
      digitalWrite(VALVE_1_EN4, LOW);
      break;
    case 2:
      digitalWrite(VALVE_2_EN2, HIGH);
      digitalWrite(VALVE_2_EN4, LOW);
      break;
  }
}

void closeValve(int valveNumber) {
  switch (valveNumber) {
    case 1:
      digitalWrite(VALVE_1_EN2, LOW);
      digitalWrite(VALVE_1_EN4, HIGH);
      break;
    case 2:
      digitalWrite(VALVE_2_EN2, LOW);
      digitalWrite(VALVE_2_EN4, HIGH);
      break;
  }
}

void stopValve(int valveNumber) {
  switch (valveNumber) {
    case 1:
      digitalWrite(VALVE_1_EN2, LOW);
      digitalWrite(VALVE_1_EN4, LOW);
      break;
    case 2:
      digitalWrite(VALVE_2_EN2, LOW);
      digitalWrite(VALVE_2_EN4, LOW);
      break;
  }
}

float readTempSafe(DallasTemperature &sensor) {
  float t;
  do {
    sensor.requestTemperatures();
    //delay(1000);
    t = sensor.getTempCByIndex(0);
    Serial.print("Measured temperature: ");
    Serial.println(t);
    
  } while (t == DEVICE_DISCONNECTED_C || t == 85.0);
  return t;
}


void setup() {
  // 32kHz PWM on Timer1
  //TCCR1A = (1 << WGM10) | (1 << COM1A1);
  //TCCR1B = (1 << WGM12) | (1 << CS10);

  pinMode(PUMP_OUT_PIN, OUTPUT);
  pinMode(VALVE_1_EN2, OUTPUT);
  pinMode(VALVE_1_EN4, OUTPUT);
  pinMode(VALVE_EN, OUTPUT);
  pinMode(VALVE_2_EN2, OUTPUT);
  pinMode(VALVE_2_EN4, OUTPUT);

  analogWrite(VALVE_EN, 128); // 50% duty

  Serial.begin(115200);

  sensors.begin();

  openValve(1);
  openValve(2);

  stopValve(1);
  stopValve(2);
}




void loop() {

  
  do {
    sensors.requestTemperatures();
    temp1 = sensors.getTempC(sensor1ROM);
    //temp1 = sensors1.getTempCByIndex(0);
//    Serial.println("failure 1");
    delay(100);
  } while (temp1 == DEVICE_DISCONNECTED_C || temp1 == 85.0);

  //Serial.println(temp1);

  do {
    sensors.requestTemperatures();
    temp0 = sensors.getTempC(sensor0ROM);
    //temp1 = sensors1.getTempCByIndex(0);
    //Serial.println("failure 0");
    delay(100);
  } while (temp0 == DEVICE_DISCONNECTED_C || temp0 == 85.0);

  
  
  if((temp0 > GAS_HEATER_TURN_ON_THRESHOLD) | (abs(temp0 - temp1) > 5.0))
    digitalWrite(PUMP_OUT_PIN, HIGH);
  else
    digitalWrite(PUMP_OUT_PIN, LOW);

  Serial.print("lj ");
  Serial.print("valveState ");
  Serial.print(valveState);
  Serial.print(" pumpState ");
  Serial.print(pumpState);
  Serial.print(" temps ");
  Serial.print(temp0);
  Serial.print(" ");
  Serial.println(temp1);

  delay(2300);
}


void printAddress(DeviceAddress deviceAddress) {
  for (uint8_t i = 0; i < 8; i++) {
    Serial.print("0x");
    if (deviceAddress[i] < 0x10) {
      Serial.print("0");
    }
    Serial.print(deviceAddress[i], HEX);
    if (i < 7) {
      Serial.print(", ");
    }
  }
  Serial.println();
}


/*
#include <OneWire.h>
#include <DallasTemperature.h>

// DS18B20 ROMs (hard-coded)
// 2881774700000099
// 28BF1147000000EA

byte sensor0ROM[8] = { 0x28, 0x8D, 0x2A, 0x55, 0x00, 0x00, 0x00, 0xA2 }; // is at the bottom
byte sensor1ROM[8] = { 0x28, 0xBF, 0x11, 0x47, 0x00, 0x00, 0x00, 0xEA }; // is at the top

// PIN definitions
const int PUMP_OUT_PIN = 2;
const int TEMP_SENSOR_PIN_0 = 10;
const int TEMP_SENSOR_PIN_1 = 3;
const int VALVE_EN = 9; // 32kHz PWM
const int VALVE_1_EN2 = 7;
const int VALVE_1_EN4 = 8;
const int VALVE_2_EN2 = 4;
const int VALVE_2_EN4 = 5;

bool valveState = 0;
bool pumpState = 0;

// OneWire + DallasTemperature
OneWire oneWire0(TEMP_SENSOR_PIN_0);
OneWire oneWire1(TEMP_SENSOR_PIN_1);

DallasTemperature sensors0(&oneWire0);
DallasTemperature sensors1(&oneWire1);

DeviceAddress deviceAddress; // variable to store the device address

float temp0 = 0.0;
float temp1 = 0.0;


// Valve control helpers
void openValve(int valveNumber) {
  switch (valveNumber) {
    case 1:
      digitalWrite(VALVE_1_EN2, HIGH);
      digitalWrite(VALVE_1_EN4, LOW);
      break;
    case 2:
      digitalWrite(VALVE_2_EN2, HIGH);
      digitalWrite(VALVE_2_EN4, LOW);
      break;
  }
}

void closeValve(int valveNumber) {
  switch (valveNumber) {
    case 1:
      digitalWrite(VALVE_1_EN2, LOW);
      digitalWrite(VALVE_1_EN4, HIGH);
      break;
    case 2:
      digitalWrite(VALVE_2_EN2, LOW);
      digitalWrite(VALVE_2_EN4, HIGH);
      break;
  }
}

void stopValve(int valveNumber) {
  switch (valveNumber) {
    case 1:
      digitalWrite(VALVE_1_EN2, LOW);
      digitalWrite(VALVE_1_EN4, LOW);
      break;
    case 2:
      digitalWrite(VALVE_2_EN2, LOW);
      digitalWrite(VALVE_2_EN4, LOW);
      break;
  }
}

float readTempSafe(DallasTemperature &sensor) {
  float t;
  do {
    sensor.requestTemperatures();
    //delay(1000);
    t = sensor.getTempCByIndex(0);
    Serial.print("Measured temperature: ");
    Serial.println(t);
    
  } while (t == DEVICE_DISCONNECTED_C || t == 85.0);
  return t;
}


void setup() {
  // 32kHz PWM on Timer1
  //TCCR1A = (1 << WGM10) | (1 << COM1A1);
  //TCCR1B = (1 << WGM12) | (1 << CS10);

  pinMode(PUMP_OUT_PIN, OUTPUT);
  pinMode(VALVE_1_EN2, OUTPUT);
  pinMode(VALVE_1_EN4, OUTPUT);
  pinMode(VALVE_EN, OUTPUT);
  pinMode(VALVE_2_EN2, OUTPUT);
  pinMode(VALVE_2_EN4, OUTPUT);

  analogWrite(VALVE_EN, 128); // 50% duty

  Serial.begin(115200);

  sensors0.begin();
  delay(10);
  sensors1.begin();
  delay(10);


}



void loop() {
  digitalWrite(PUMP_OUT_PIN, LOW);

  do {
    sensors1.requestTemperatures();
    temp1 = sensors1.getTempC(sensor1ROM);
    //temp1 = sensors1.getTempCByIndex(0);
    Serial.print("temperature 1: ");
    Serial.println(temp1);
  } while (temp1 == DEVICE_DISCONNECTED_C || temp1 == 85.0);
  
  do {
    sensors0.requestTemperatures();
    temp0 = sensors0.getTempC(sensor0ROM);
    Serial.print("temperature 0: ");
    Serial.println(temp0);
    
  } while (temp0 == DEVICE_DISCONNECTED_C || temp0 == 85.0);

  

  

  
  
  
  // temporary for testing
  

  Serial.print("lj ");
  Serial.print("valveState ");
  Serial.print(valveState);
  Serial.print(" pumpState ");
  Serial.print(pumpState);
  Serial.print(" temps ");
  Serial.print(temp0);
  Serial.print(" ");
  Serial.println(temp1);

  delay(2300);
}


void printAddress(DeviceAddress deviceAddress) {
  for (uint8_t i = 0; i < 8; i++) {
    Serial.print("0x");
    if (deviceAddress[i] < 0x10) {
      Serial.print("0");
    }
    Serial.print(deviceAddress[i], HEX);
    if (i < 7) {
      Serial.print(", ");
    }
  }
  Serial.println();
}



*/
