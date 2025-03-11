// Developed by Euan Monteclaro (NeonicPlasma), 2024
// St. Bernard's College 183z Team
// CRISiSLab Challenge 2024

// WIRELESS ALARM
// This code runs on the arduino that has a wireless signal sent to its alarm.
// Uses radiohead library and driver
// When it receives a signal, it activates four flashing lights.

#include <Wire.h>
#include <RH_ASK.h>
#include <SPI.h>

// Radiohead driver
RH_ASK rf_driver;

// Set buzzer pins
const int BUZZER_PIN_1 = 7;
const int BUZZER_PIN_2 = 3;

// Set LED pins
const int LED_1_PIN = 8;
const int LED_2_PIN = 6;
const int LED_3_PIN = 5;
const int LED_4_PIN = 4;

// Set frequency 
const int FIRST_FREQUENCY = 523;
const int SECOND_FREQUENCY = 415;

// Set length variables
const int TICK_LENGTH = 250;
const int REPEATS = 10;

void setup() {
  // put your setup code here, to run once:
  rf_driver.init();
  Serial.begin(9600);

  // Set pin modes
  pinMode(LED_1_PIN, OUTPUT);
  pinMode(LED_2_PIN, OUTPUT);
  pinMode(LED_3_PIN, OUTPUT);
  pinMode(LED_4_PIN, OUTPUT);
  pinMode(BUZZER_PIN_1, OUTPUT);
  pinMode(BUZZER_PIN_2, OUTPUT);
    
}

void loop() {
  
  // put your main code here, to run repeatedly:
  uint8_t buf[8];
  uint8_t buflen = sizeof(buf);

  // Check to see if signal received on wireless receiver, if so activate alarm
  if (rf_driver.recv(buf, &buflen))
  {
    Serial.println((char*)buf);
    startAlarm();
  }
  
}

//////////////////////////////////////////////
// Starts alarm when signal is received
void startAlarm() {

  for (int i = 0; i <= REPEATS; i++) {

    // Turn on first LED, play buzzer of higher frequency and wait for TICK_LENGTH
    digitalWrite(LED_1_PIN, HIGH);
    tone(BUZZER_PIN_1, FIRST_FREQUENCY, TICK_LENGTH);
    tone(BUZZER_PIN_2, FIRST_FREQUENCY, TICK_LENGTH);
    delay(TICK_LENGTH);
    // Turn off first LED
    digitalWrite(LED_1_PIN, LOW);

    // Turn on second LED, play buzzer of lower frequency and wait for TICK_LENGTH
    digitalWrite(LED_2_PIN, HIGH);
    tone(BUZZER_PIN_1, SECOND_FREQUENCY, TICK_LENGTH);
    tone(BUZZER_PIN_2, SECOND_FREQUENCY, TICK_LENGTH);
    delay(TICK_LENGTH);    
    // Turn off second LED
    digitalWrite(LED_2_PIN, LOW);

    // Turn on third LED
    digitalWrite(LED_3_PIN, HIGH);
    tone(BUZZER_PIN_1, FIRST_FREQUENCY, TICK_LENGTH);
    tone(BUZZER_PIN_2, FIRST_FREQUENCY, TICK_LENGTH);
    delay(TICK_LENGTH);
    digitalWrite(LED_3_PIN, LOW);

    // Turn on fourth LED
    digitalWrite(LED_4_PIN, HIGH);
    tone(BUZZER_PIN_1, SECOND_FREQUENCY, TICK_LENGTH);
    tone(BUZZER_PIN_2, SECOND_FREQUENCY, TICK_LENGTH);
    delay(TICK_LENGTH);    
    digitalWrite(LED_4_PIN, LOW);
  }
}
