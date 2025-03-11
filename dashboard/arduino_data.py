# Developed by Euan Monteclaro (NeonicPlasma), 2024
# St. Bernard's College 183z Team
# CRISiSLab Challenge 2024

#################### IMPORTS ####################
import serial
from serial.serialutil import SerialException
import time

class DataTransmitter():
    """Collects and sends data to/from a serial port, if able to connect to the serial port."""

    def __init__(self, dashboard):

        self.serial_COM = None
        self.break_loop = False

        self.dashboard = dashboard
    
    def connect_serial(self, port, baud_rate):
        """Attempt to connect to the serial port. If the port can be opened, returns True. If port cannot be opened or any other exception occurs, returns False."""

        # Attempt to connect to serial
        try:
            # If the serial port cannot be opened, raise SerialException
            self.serial_COM = serial.Serial(port, baud_rate)
            return True
        
        except SerialException:
            
            self.serial_COM = None
            return False
        
    def get_pressure_data(self):
        """
            Returns the latest pressure data recorded by the sensor connected to the Arduino.
            If the arduino runs into an error not being able to record the data or no new data has been sent, return None
        """

        # Attempt to read the latest line sent by the senseor
        try:
            data = self.serial_COM.readline().decode().strip()
        except Exception:
            # The data could not be retrieved, so do not return any data
            return None

        # If data exists, process the data and get the pressure reading
        if data:
            try:
                # Attempt to convert data to a floating point number
                data_float = float(data)
                return data_float
            except ValueError:
                # If the data is unable to be converted, return None
                return None
        else:
            # Data could not be retrieved, so do not return any data
            return None
        

    def data_loop(self):
        """
            Tries to collect data. Runs every 20th of a second.
        """

        # Run a While True loop to constantly retrieve pressure data from the sensor
        while True:

            time.sleep(0.05)

            # Check if dashboard is connected to this data transmitter
            if self.dashboard == None: continue

            # Check if serial is connected
            if not self.is_serial_connected(): continue

            # Retrieve pressure from sensor
            pressure = self.get_pressure_data()

            # If pressure data exists, send it to the dashboard to update the graph
            if pressure != None:
                self.dashboard.new_pressure_data(pressure)



    def set_dashboard(self, dashboard):
        """Set the dashboard this DataTransmitter is attached to, so data can be sent to and from the dashboard"""
        self.dashboard = dashboard



    def is_serial_connected(self):
        """Returns True if serial is connected, or False if serial is not connected."""
        return self.serial_COM != None
    
    
    def send_alarm(self):
        """Sends out the alarm to the connected arduino."""

        if self.serial_COM == None: return
        self.serial_COM.write("ALARM".encode())

