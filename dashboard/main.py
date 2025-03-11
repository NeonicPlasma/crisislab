# Developed by Euan Monteclaro (NeonicPlasma), 2024
# St. Bernard's College 183z Team
# CRISiSLab Challenge 2024

#################### IMPORTS ####################
from dashboard import Dashboard
from arduino_data import DataTransmitter
import threading
import os
 
#################### MAIN ROUTINE #################### 
if __name__ == "__main__":

    # Set working directory into main directory
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    # Create data transmitter object and dashboard
    data_transmitter = DataTransmitter(dashboard=None)
    dashboard = Dashboard("Tsunami Alert Dashboard", data_transmitter=data_transmitter)
    data_transmitter.set_dashboard(dashboard)

    # Run the data transmitter in a different thread
    # This is to reduce lag on the GUI
    data_thread = threading.Thread(target=data_transmitter.data_loop)
    data_thread.start()

    # Run the mainloop of the dashboard
    dashboard.mainloop()