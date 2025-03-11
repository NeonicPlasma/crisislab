// Developed by Euan Monteclaro (NeonicPlasma), 2024
// St. Bernard's College 183z Team
// CRISiSLab Challenge 2024

// MAIN ARDUINO CODE
// Code that runs on the main arduino
// Reads pressure sensor using SparkFun_LPS28DFW pressure sensor library
// Sends out alarm when receiving a signal from the serial port
// Uses radiohead library and driver to transmit a wireless signal to the wireless alarm

#include <Wire.h>
#include "SparkFun_LPS28DFW_Arduino_Library.h"

// Get radio signal libraries
#include <RH_ASK.h>
#include <SPI.h>

// Create a new sensor object
LPS28DFW pressureSensor;

// Setup wireless driver
RH_ASK rf_driver;

// I2C address selection
uint8_t i2cAddress = LPS28DFW_I2C_ADDRESS_DEFAULT;

// Alarm constants
const int ALARM_ALTERNATION_MAX = 24; // Maximum amount of alternations to play
const int ALARM_ALTERNATE_LENGTH = 6; // Amount of 100ms between each alternation

// Pins
const int LED_PIN_1 = 11;
const int LED_PIN_2 = 10;
const int LED_PIN_3 = 9;
const int LED_PIN_4 = 6;

const int BUZZER_PIN_1 = 8;
const int BUZZER_PIN_2 = 7;

// Alarm variables
bool alarm_on = false;
bool alarm_rebound = true;

int current_alarm_alternation = 0;
int current_alarm_tick = 0;
bool screen_state = true; // Current state of the alarm screen 

//////////////////////////////////////////////
// Setup -- ran on initialisation
void setup()
{

    // Start serial
    Serial.begin(115200);

    // Initialize the I2C library
    Wire.begin();

    // Setup radio transmitter driver
    rf_driver.init();

    // Set pin modes
    pinMode(LED_PIN_1, OUTPUT);
    pinMode(LED_PIN_2, OUTPUT);
    pinMode(LED_PIN_3, OUTPUT);
    pinMode(LED_PIN_4, OUTPUT);
    pinMode(BUZZER_PIN_1, OUTPUT);
    pinMode(BUZZER_PIN_2, OUTPUT);

    // Check if sensor is connected and initialize
    // Address is optional (defaults to 0x5C)
    while (pressureSensor.begin(i2cAddress) != LPS28DFW_OK)
    {
        // Not connected, inform user
        Serial.println("Error: Sensor not connected, check wiring and I2C address!");

        // Wait a bit to see if connection is established
        delay(1000);
    }

    Serial.println("Sensor connected!");
}

//////////////////////////////////////////////
// Loop method -- constantly runs
void loop()
{
    // Get measurements from the sensor. This must be called before accessing
    // the pressure data, otherwise it will never update
    pressureSensor.getSensorData();

    // Print temperature and pressure
    Serial.println(pressureSensor.data.pressure.hpa);

    // Check if alarm got sent while alarm is not currently on
    if (alarm_on == false) {
      if (Serial.available() > 0) {
        // Use alarm rebound to make sure that you can't send more than one alarm signal
        if (alarm_rebound == true) {
          alarm_rebound = false;
          // Start the alarm
          startAlarm();
        }
      }
      else {
        alarm_rebound = true;
      }
    } else {
      // Alarm is on, run alarm on
      alarmLoop();
    }

    // Send data at a rate of 10Hz (10 times per second, every 100ms)
    delay(100);
}

//////////////////////////////////////////////
// Method that starts alarm
void startAlarm()
{ 
    // Send radio message to other alarm
    alarm_on = true;
    screen_state = false;
    current_alarm_tick = 0;
    current_alarm_alternation = 0;
    alarmLoop();
    activateOtherAlarm();
}

//////////////////////////////////////////////
// Runs in loop when alarm is on
void alarmLoop()
{
  // Increment current alarm tick
  current_alarm_tick++;

  bool change_state = false;

  // Check if alarm should change state
  if (current_alarm_tick == ALARM_ALTERNATE_LENGTH) {
    change_state = true;
    current_alarm_tick = 0;
    current_alarm_alternation++;
  } 

  // Change state of alarm
  if (change_state == true) {
    // Check if all alternations have been completed
    if (current_alarm_alternation == ALARM_ALTERNATION_MAX) {
      // Turn alarm off 
      turnAlarmOff();
    }
    else {
      // Alternate screen state
      if (screen_state == true) {
        digitalWrite(LED_PIN_1, false);
        digitalWrite(LED_PIN_2, false);
        digitalWrite(LED_PIN_3, false);
        digitalWrite(LED_PIN_4, false);
        screen_state = false;
      }
      else {
        digitalWrite(LED_PIN_1, true);
        digitalWrite(LED_PIN_2, true);
        digitalWrite(LED_PIN_3, true);
        digitalWrite(LED_PIN_4, true);
        tone(BUZZER_PIN_1, 523, ALARM_ALTERNATE_LENGTH * 100);
        tone(BUZZER_PIN_2, 415, ALARM_ALTERNATE_LENGTH * 100);
        screen_state = true;
      }
    }
  }
}

//////////////////////////////////////////////
// Runs in loop when alarm is on
void turnAlarmOff()
{
  // Turn alarm off in variables
  alarm_on = false;
  digitalWrite(LED_PIN_1, false);
  digitalWrite(LED_PIN_2, false);
  digitalWrite(LED_PIN_3, false);
  digitalWrite(LED_PIN_4, false);
}

//////////////////////////////////////////////
// Sends radio signal to receiver to activate the alarm
void activateOtherAlarm()
{
  // Send message
  const char *msg = "ACTIVATE";
  rf_driver.send((uint8_t *)msg, strlen(msg));
}