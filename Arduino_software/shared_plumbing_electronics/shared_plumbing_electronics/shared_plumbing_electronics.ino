// Float switches
const int FLOAT_DRAIN_PIN = 5;
const int FLOAT_EFFLUENT_PIN = 6;

// Pumps (relay control)
const int PUMP_DRAIN_PIN = 3;
const int PUMP_EFFLUENT_PIN = 7;
//const int PUMP_TANK_OUT_PIN = 4; // declared but not used yet

// Analog water level sensor
const int TANK_LEVEL_SENSOR_PIN = A0;

// L298N valve control
const int VALVE_PWM_OUT = 10;
const int VALVE_OUT_1 = 12;
const int VALVE_OUT_2 = 11;


// Flow sensor
const int FLOW_SENSOR_PIN = 2;


// Analog water level sensor threshold values
const int WATER_LOW_THRESHOLD  = 300;  // below this → open valve
const int WATER_HIGH_THRESHOLD = 700;  // above this → close valve


// flow measurement variables
//volatile unsigned int pulseCount = 0;

volatile unsigned int pulseCount = 0;
volatile unsigned long lastPulseMicros = 0;

unsigned long lastMeasureTime = 0;
const unsigned long measureInterval = 1000; // 1000ms = 1s

float pulses;
int flowRate;

// comparison table of measured parameters
// this maps liters per minute to number of pulses
const float referenceTableOfFlows[11] = {0, 5.411, 12.50, 22.73, 31.65, 39.06, 46.30, 55.56, 64.10, 71.43, 80.65}; 

int counter = 0;
char serialBuffer[64];

int floatDrainState;
int floatEffluentState;


// Function definitions
void openValve() {
  digitalWrite(VALVE_OUT_2, HIGH);
  digitalWrite(VALVE_OUT_1, LOW);
}

void closeValve() {
  digitalWrite(VALVE_OUT_2, LOW);
  digitalWrite(VALVE_OUT_1, HIGH);
}

void stopValve() {
  digitalWrite(VALVE_OUT_1, LOW);
  digitalWrite(VALVE_OUT_2, LOW);
}

uint16_t readAdc(uint8_t channel) {
  // Select the channel (0-5 for A0-A5 on Uno)
  // Ensure previous channel bits are cleared first using a mask
  
  ADMUX = (ADMUX & 0xF0) | channel; 
  
  

  // Start the conversion by setting the ADSC bit
  ADCSRA |= (1 << ADSC); 

  // Wait for the conversion to complete
  while (ADCSRA & (1 << ADSC)); 

  return ADCL | (ADCH << 8);

}


bool drainRunningForTheFirstTime = 1;
bool effluentRunningForTheFirstTime = 1;

void setup() {
  pinMode(FLOAT_DRAIN_PIN, INPUT);
  pinMode(FLOAT_EFFLUENT_PIN, INPUT);

  pinMode(PUMP_DRAIN_PIN, OUTPUT);
  pinMode(PUMP_EFFLUENT_PIN, OUTPUT);

  analogWrite(VALVE_PWM_OUT, 255); // 50% duty

  pinMode(VALVE_OUT_1, OUTPUT);
  pinMode(VALVE_OUT_2, OUTPUT);

  pinMode(FLOW_SENSOR_PIN, INPUT_PULLUP);

  // Ensure everything is off at startup
  digitalWrite(PUMP_DRAIN_PIN, LOW);
  digitalWrite(PUMP_EFFLUENT_PIN, LOW);
  

  stopValve();

  Serial.begin(115200);

  attachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_PIN), flowPulseISR, FALLING);
  interrupts();

  lastMeasureTime = millis();


  // ADCSRA:
  // ADEN set to 1 -> Enable ADC
  // ADPS2, ADPS1, ADPS0 set to 1, 1, 1 -> Prescaler of 128 (16MHz/128 = 125kHz ADC clock)
  ADCSRA |= (1 << ADEN);
  ADCSRA |= (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);
  
  
  // ADMUX:
  // REFS0 set to 1, REFS1 set to 0 -> AVcc as reference (default 5V on Uno)
  // ADLAR set to 0 -> right adjust result (read ADCL then ADCH)
  ADMUX |= (1 << REFS0);
  delay(1);

  openValve();
   
  
}

unsigned long effluentPumpTurnOnTime = 0;
unsigned long drainPumpTurnOnTime = 0;

bool drainPumpOn = 0;
bool effluentPumpOn = 0;

unsigned long now;

unsigned long motorSampleTime = 0;

#define OPEN 1
#define CLOSE -1
#define STOP 0

#define GOAL_FLOWRATE 150

int motorDirection = STOP;

void loop() {
  motorSampleTime = millis();
  // set the default behavior
  motorDirection = STOP;
  if(millis() - motorSampleTime > 100){ 
    if(abs(flowRate - GOAL_FLOWRATE) > 20){
      // we wanna open or close the valve
      if(flowRate > 150){
        motorDirection = CLOSE;
      }else
        motorDirection = OPEN;    
    }
    motorSampleTime = millis();
  }

  switch(motorDirection){
    case(STOP):
      stopValve();
      break;
    case(OPEN):
      openValve();
      break;
    case(CLOSE):
      closeValve();
      break;
  } 
  
  

  now = millis();

  // deal with the overflow case
  if(now < lastMeasureTime){
    lastMeasureTime = 0;  
  }
  
  if (now - lastMeasureTime >= measureInterval) {
    // Temporarily disable interrupt while reading shared variable
    noInterrupts();
    flowRate = pulseCount;
    pulseCount = 0;
    interrupts();
    lastMeasureTime = now;

    /*
    // Calculate flowRate
    flowRate = 0.0;
    for (int i = 1; i < 11; i++){
      if(pulses > referenceTableOfFlows[i - 1] && pulses < referenceTableOfFlows[i]){
        // now extrapolate here
        flowRate = i + (pulses - referenceTableOfFlows[i - 1] ) / (referenceTableOfFlows[i] - referenceTableOfFlows[i - 1]);
      }
    }
    */
    // this goes around the actual flow rate calculation

    
    // ---- FLOAT SWITCH → PUMP CONTROL ----

     // I want to replace these reads and writes with register level operations
    floatDrainState = digitalRead(FLOAT_DRAIN_PIN);
    if(floatDrainState == HIGH){
      drainRunningForTheFirstTime = 0;
      drainPumpTurnOnTime = millis();
    }

    if((millis() - drainPumpTurnOnTime) < 30000 && drainRunningForTheFirstTime == 0){
      digitalWrite(PUMP_DRAIN_PIN, HIGH);
    }else{
      digitalWrite(PUMP_DRAIN_PIN, LOW);
    }
    
    floatEffluentState = digitalRead(FLOAT_EFFLUENT_PIN);
    if(floatEffluentState == HIGH){
      effluentRunningForTheFirstTime = 0;
      effluentPumpTurnOnTime = millis();
    }

    if((millis() - effluentPumpTurnOnTime) < 10000 && effluentRunningForTheFirstTime == 0){
      digitalWrite(PUMP_EFFLUENT_PIN, HIGH);
    }else{
      digitalWrite(PUMP_EFFLUENT_PIN, LOW);
    }
    

    // reads all PORTD input bits at once (port D is pins 0 to 7)
    /*uint8_t portD = PIND;
    PORTD = PORTD & ~((1 << PD7) | (1 << PD3)); // clear pump bits
    PORTD = PORTD | ((portD & (1 << PD5)) ? (1 << PD7) : 0);
    PORTD = PORTD | ((portD & (1 << PD6)) ? (1 << PD3) : 0);
    */

  
    // ---- READ ANALOG WATER LEVEL ----
    //int tankLevel = analogRead(TANK_LEVEL_SENSOR_PIN);
    int tankLevel = readAdc(0);
    
    /*
    
    // ---- VALVE CONTROL BASED ON WATER LEVEL ----
    if (tankLevel < WATER_LOW_THRESHOLD) {
      openValve();
    }
    else if (tankLevel > WATER_HIGH_THRESHOLD) {
      closeValve();
    }
    else {
      stopValve(); // dead-band zone
    }
    */

        // For the practical benefit that we could print every second, which is the same frequency
    // as the flowRate calculation frequency, I will print the variables right here.
    
    // Variables to be printed: floatDrainState floatEffluentState tankLevel flowRate
    // floatDrainState is 1 or 0
    // float EffluentState is 1 or 0
    // tankLevel is in 0-1023
    // flowRate is a float between 0.0 and 100.0
    
    // every so often we want to print

    // edbDrain 1|0 edbEffluent 1|0 tankLevel 0-1023 flowRate 0.0-1023.0
    // the first word will identify which Arduino this is
    
    snprintf(
      serialBuffer,
      sizeof(serialBuffer),
      "edb Drain %d Effluent %d tankLevel %04d flowRate %04d\n",
      floatDrainState,
      floatEffluentState,
      tankLevel,
      flowRate
    );
    
    for(int i = 0; i < strlen(serialBuffer); i++){
      while (!(UCSR0A & (1 << UDRE0)));  // wait until UART ready
      UDR0 = serialBuffer[i];            // send byte  
    }
    
  }

  
}


void flowPulseISR() {

  /*
  unsigned long now = micros();
  if (now - lastPulseMicros > 100) {
    pulseCount++;
    lastPulseMicros = now;
  }
  */
  
  pulseCount++;
}
