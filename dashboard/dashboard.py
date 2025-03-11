# Developed by Euan Monteclaro (NeonicPlasma), 2024
# St. Bernard's College 183z Team
# CRISiSLab Challenge 2024

################# IMPORTS ##################
from tkinter import *
import matplotlib
import matplotlib.axes
import matplotlib.figure
import matplotlib.pyplot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import threading
import numpy as np
from datetime import datetime

class Dashboard(Tk):

    def __init__(self, title, data_transmitter):

        super().__init__()

        # Set title and color of root window
        self.title(title)
        self.configure(background="#06070A")

        # Data transmitter object that receives and sends data
        self.data_transmitter = data_transmitter

        # Define data variables
        ##########################
        # Data received from the pressure sensor 
        # (first list is time values in seconds, second list is pressure in hPa)
        self.pressure_data = [[], []]
        # Data calculated for the water height above the sensor
        # (first list is time values in seconds, second list is water height in centimetres)
        self.water_height_data = [[], []]

        # Calibrated air pressure used in water level calculations - if None, that means not calibrated yet
        self.calibrated_air_pressure = None

        # Standing water height - the height of the water when no waves are created
        # If None, this means not calibrated yet
        self.standing_water_level = None
        self.standing_water_air_pressure = None

        # Wave threshold to set off an alarm
        self.alarm_threshold = None

        # The amount of seconds since right now that the graph and statistics should show
        self.data_period_var = IntVar()
        self.data_period_var.set(15)

        # Variables to check if alarm has been sent, and if it is on cooldown
        self.alarm_sent = False
        self.alarm_cooldown = False
        self.pressure_on_alarm_activate = None
        self.wave_height_on_alarm_activate = None

        # Default boundaries of pressure graph and water height graph
        # The buffer is the amount of space that should be left between the limits of the graph and the line
        self.pressure_graph_default_ylim = [995, 1025]
        self.pressure_graph_ylim_buffer = 5
        self.water_height_graph_default_ylim = [0, 15]
        self.water_height_graph_ylim_buffer = 2.5

        # Set time of initialisation - used in time calculations
        self.init_time = time.time()

        # Create all widgets
        self.create_widgets()



    def create_widgets(self):
        """Creates the widgets"""

        # Create header frame
        self.header_frame = Frame(self, padx=20, pady=20, background="#41D3BD")
        self.header_frame.grid(row=0,column=0,columnspan=3,sticky="NESW")

        # Create header
        self.header = Label(self.header_frame, text="Tsunami Alert System Dashboard", anchor=W, justify=LEFT, font=("Roboto", 24, "bold"), 
                            background="#41D3BD", foreground="#0E1116")
        self.header.grid(row=0,column=0,sticky="NESW",rowspan=2)

        # Add date and time
        self.date_time_stringvar = StringVar()
        self.date_time_label = Label(self.header_frame, textvariable=self.date_time_stringvar, anchor=W, justify=LEFT, font=("Roboto", 16, "bold"), 
                            background="#41D3BD", foreground="#0E1116", padx=20, pady=0)
        self.date_time_label.grid(row=0,column=1,sticky="WE")

        # Add date and time
        self.date_time_label = Label(self.header_frame, text="New Zealand Standard Time (UTC+12)", anchor=W, justify=LEFT, font=("Roboto", 12, "bold"), 
                            background="#41D3BD", foreground="#0E1116", padx=20, pady=0)
        self.date_time_label.grid(row=1,column=1,sticky="WE")

        #####################################################################################
        ############################### CREATING GRAPH FIGURE ###############################
        #####################################################################################

        # Create frame for graph
        self.graph_frame = Frame(self, background="#0E1116", width=40)
        self.graph_frame.grid(row=2, column=0, rowspan=3, padx=20, pady=20, sticky="WE")

        # Create scrolling graphs
        self.graph = UpdatingGraphFigure(self.graph_frame, 1, 2)
        self.graph.canvas.get_tk_widget().pack()

        # Retrieve important subplots
        self.pressure_subplot = self.graph.get_subplot(0)
        self.water_height_subplot = self.graph.get_subplot(1)

        # Format both subplots
        for subplot in self.graph.axes_list:

            # Set colors and fonts
            subplot.set_facecolor("#0E1116") 

            # Add grid
            subplot.grid(visible=True, which="major", axis="both")
            subplot.grid(visible=True, which="minor", axis="y")

            subplot.tick_params(color="#E4FDE1", 
                                labelcolor="#E4FDE1", 
                                grid_color="#547AA5", 
                                labelfontfamily="Roboto", 
                                width=2,
                                grid_linewidth=1)
            
            # Color the data line in each subplot and increase the thickness
            for line in subplot.get_lines():
                line.set_color("#41D3BD")
                line.set_linewidth(3)
            
            for spine in subplot.spines.values():
                spine.set(color="#E4FDE1", linewidth=2)

        # Set titles of pressure subplot
        self.pressure_subplot.set_title("Pressure Over Time in seconds", color="#E4FDE1", fontfamily="Roboto", fontweight="bold", fontsize=20)
        self.pressure_subplot.set_xlabel("Time (s)", color="#E4FDE1", fontfamily="Roboto", fontweight="bold",)
        self.pressure_subplot.set_ylabel("Pressure (hPa)", color="#E4FDE1", fontfamily="Roboto", fontweight="bold")

        # Set titles of pressure subplot
        self.water_height_subplot.set_title("Approx. Water Height Over Time", color="#E4FDE1", fontfamily="Roboto", fontweight="bold", fontsize=20)
        self.water_height_subplot.set_xlabel("Time (s)", color="#E4FDE1", fontfamily="Roboto", fontweight="bold")
        self.water_height_subplot.set_ylabel("Approx. Water Height Above Bottom (cm)", color="#E4FDE1", fontfamily="Roboto", fontweight="bold")

        # Customise figure appearance
        self.graph.fig.set_facecolor("#0E1116") # Customise background of figure
        self.graph.fig.subplots_adjust(wspace=0.3, hspace=0.5) # Change the distance between the subplots

        # Manually set vertical limits on the subplots
        self.pressure_subplot.set_ylim(bottom=self.pressure_graph_default_ylim[0], top=self.pressure_graph_default_ylim[1])
        self.water_height_subplot.set_ylim(bottom=self.water_height_graph_default_ylim[0], top=self.water_height_graph_default_ylim[1])

        # Add horizontal line onto the water height graph to display the standing water height
        self.standing_water_height_line = self.water_height_subplot.axhline(-250, -1000000, 1000000)
        self.standing_water_height_line.set_color("#90D1C6") # Change color of alarm threshold line to light turquoise
        self.standing_water_height_line.set_linewidth(1) # Make line thin

        # Add horizontal line onto the water height graph to display the threshold
        self.alarm_threshold_line = self.water_height_subplot.axhline(-250, -1000000, 1000000)
        self.alarm_threshold_line.set_color("#FB3640") # Change color of alarm threshold line to red
        self.alarm_threshold_line.set_linestyle("--") # Set to dash line style
        self.alarm_threshold_line.set_linewidth(2) # Increase thickness of line

        # Create text on upper graph to show current pressure
        self.current_pressure_text = self.pressure_subplot.text(0, 1000, "No pressure reading", fontfamily="Roboto", 
                                                                    color="#41D3BD", fontweight="bold", fontsize=12,
                                                                    horizontalalignment="left",verticalalignment="center")
        
        # Create text on lower graph to show current water height
        self.current_water_height_text = self.water_height_subplot.text(0, 1000, "No water height reading", fontfamily="Roboto", 
                                                                    color="#41D3BD", fontweight="bold", fontsize=12,
                                                                    horizontalalignment="left",verticalalignment="center")
        
        # Create text on lower graph to show water height threshold
        self.alarm_threshold_text = self.water_height_subplot.text(0, 1000, "ALARM THRESHOLD: 20.00 cm", fontfamily="Roboto", 
                                                                    color="#FB3640", fontweight="bold", fontsize=12,
                                                                    horizontalalignment="right",verticalalignment="baseline")

        #####################################################################################
        ################################ CREATING INPUT FRAME ###############################
        #####################################################################################

        self.input_frame = Frame(self, background="#0E1116")
        self.input_frame.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="WE")

        # Creating functions for when buttons are hovered over
        default_button_options_format = {
            "background": "#41D3BD", 
            "foreground": "#0E1116", 
            "activebackground": "#1B594E", 
            "hoverbackground": "#2F9987",
            "disabledbackground": "#292A2B",
        }

        # Create button to connect to arduino
        self.connect_button_text = StringVar()
        self.connect_button = HoverButton(self.input_frame, text="Connect to\nArduino", font=("Roboto", 14, "bold"), command=self.connect_serial, 
                                            width = 10, **default_button_options_format)
        
        self.connect_button.grid(row=0, column=0, padx=(10, 0), pady=10, rowspan=2, sticky="NS")

        # Create button that starts pressure calibration
        self.pressure_calibrate_button = HoverButton(self.input_frame, text="Calibrate Air Pressure", font=("Roboto", 12, "bold"), 
                                                        command=self.calibrate_pressure_button_pressed, width=25, state=DISABLED, 
                                                        **default_button_options_format)
        
        self.pressure_calibrate_button.grid(row=0, column=1, padx=(10, 0), pady=(10, 10))


        self.set_standing_depth_button = HoverButton(self.input_frame, text="Calibrate Standing Water Depth", font=("Roboto", 12, "bold"), 
                                                        command=self.calibrate_swh_button_pressed, width = 25, state=DISABLED, **default_button_options_format)
        
        self.set_standing_depth_button.grid(row=1, column=1, padx=(10, 0), pady=(0, 10))

        # Create button to reset alarm on dashboard
        self.reset_alarm_button = HoverButton(self.input_frame, text="Reset\nAlarm", font=("Roboto", 14, "bold"), command=self.reset_alarm, 
                                            width = 10, **default_button_options_format, state=DISABLED)
        
        self.reset_alarm_button.grid(row=0, column=2, padx=(10, 0), pady=10, rowspan=2, sticky="NS")

        # Create label for alarm threshold entry
        self.alarm_threshold_label = Label(self.input_frame, text="Enter Alarm Threshold (cm)\n(wave height)", font=("Roboto", 12, "bold"),
                                                 background="#0E1116", foreground="#FB3640")
        self.alarm_threshold_label.grid(row=0, column=3, padx=(20, 0), rowspan=2, sticky="WE")


        # Create entry where alarm threshold can be entered
        self.alarm_threshold_entry_frame = Frame(self.input_frame, padx=7, pady=7, background="#190A0B")
        self.alarm_threshold_entry_frame.grid(row=0, column=4, rowspan=2, padx=10)

        self.alarm_threshold_var = StringVar()
        self.alarm_threshold_entry = Entry(self.alarm_threshold_entry_frame, textvariable=self.alarm_threshold_var, font=("Roboto", 22, "bold"), borderwidth=0,
                                           background="#190A0B", foreground="#FB3640", justify=CENTER, width=6)
        self.alarm_threshold_entry.grid(row=0, column=0)

        # Create button which sets the alarm threshold using the entry created above
        self.set_alarm_threshold_button = HoverButton(self.alarm_threshold_entry_frame, text="Set", font=("Roboto", 14, "bold"), pady=0, padx=0,
                                                      background="#FB3640", foreground="#190A0B", hoverbackground="#721922", activebackground="#FF6675",
                                                      command=self.set_alarm_threshold)
        self.set_alarm_threshold_button.grid(row=0, column=1, sticky="WE")

        # Add scale for the data period
        self.data_period_slider_frame = Frame(self.input_frame, background="#0E1116")
        self.data_period_slider_frame.grid(row=0, column=5, rowspan=2, padx=10)

        self.data_period_slider = Scale(self.data_period_slider_frame, orient=HORIZONTAL, troughcolor="#151921", foreground="#E4FDE1", background="#0E1116", 
                                        bd=0, borderwidth=0, highlightthickness=0, length=150, font=("Roboto", 14, "bold"), relief=FLAT,
                                        command=self.data_period_change, from_=5, to=60, variable=self.data_period_var)
        self.data_period_slider.grid(row=0, column=0)
        self.data_period_slider.set(15)

        # Add label for the scale
        self.data_period_label = Label(self.data_period_slider_frame, text="Last secs to display", foreground="#E4FDE1", background="#0E1116", 
                                        font=("Roboto", 10, "bold"))
        self.data_period_label.grid(row=1, column=0, pady=(3, 0))

        # Create status label that updates when an event occurs
        self.status_var = StringVar()
        self.status_var.set("Connect to Arduino to start collecting data.")
        self.status_label = Label(self, textvariable=self.status_var, anchor=W, justify=LEFT, font=("Roboto", 14), width=120, padx=20, pady=10, 
                                    background="#0E1116", foreground="#E4FDE1")
        self.status_label.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="WE")



        #####################################################################################
        ########################### CREATING DATA DISPLAY FRAMES ############################
        #####################################################################################

        # Creating frame that says period of data
        #############################
        self.period_data_frame = Frame(self, background="#0E1116", width=15)
        self.period_data_frame.grid(row=2, column=1, padx=(0, 20), pady=(20, 0), sticky="NESW")
        self.period_data_frame.columnconfigure(0, weight=1)
        self.period_data_frame.rowconfigure(0, weight=1)

        self.period_data_label = Label(self.period_data_frame, background="#0E1116", text="Last {:.2f} seconds".format(self.data_period_var.get()), 
                                       font=("Roboto", 16, "bold"), foreground="#E4FDE1", pady=5)
        self.period_data_label.grid(row=0, column=0)

        # CREATING PRESSURE DISPLAY FRAME
        #############################

        self.pressure_stats_frame = Frame(self, background="#0E1116", width=15)
        self.pressure_stats_frame.grid(row=3, column=1, padx=(0, 20), pady=20, sticky="NESW")

        # Add max pressure
        self.max_pressure_var = StringVar()
        self.max_pressure_var.set("N/A")
        self.max_pressure_number = Label(self.pressure_stats_frame, textvariable=self.max_pressure_var, font=("Roboto", 36, "bold"), 
                                        background="#0E1116", foreground="#202733", width=8)
        self.max_pressure_number.grid(row=1, column=0, columnspan=2, sticky="WE", pady=(15, 0))
        self.max_pressure_label = Label(self.pressure_stats_frame, text="Maximum Pressure (hPa)", font=("Roboto", 12, "bold"), 
                                        background="#0E1116", foreground="#202733", pady=0, height=1)
        self.max_pressure_label.grid(row=2, column=0, columnspan=2, sticky="WE")

        # Add calibrated air pressure
        self.air_pressure_var = StringVar()
        self.air_pressure_var.set("N/A")
        self.air_pressure_number_label = Label(self.pressure_stats_frame, textvariable=self.air_pressure_var, font=("Roboto", 16, "bold"), 
                                        background="#0E1116", foreground="#202733", width=4)
        self.air_pressure_number_label.grid(row=3, column=0, sticky="WE", pady=(15, 0))
        self.air_pressure_label = Label(self.pressure_stats_frame, text="Calibrated\nAir Pressure", font=("Roboto", 8), 
                                        background="#0E1116", foreground="#202733", height=2, pady=0, width=4)
        self.air_pressure_label.grid(row=4, column=0, sticky="WE")

        # Add standing water pressure
        self.swd_pressure_var = StringVar()
        self.swd_pressure_var.set("N/A")
        self.swd_pressure_number = Label(self.pressure_stats_frame, textvariable=self.swd_pressure_var, font=("Roboto", 16, "bold"), 
                                        background="#0E1116", foreground="#202733", width=4)
        self.swd_pressure_number.grid(row=3, column=1, sticky="WE", pady=(15, 0))
        self.swd_pressure_label = Label(self.pressure_stats_frame, text="Standing Water\nDepth Pressure", font=("Roboto", 8), 
                                        background="#0E1116", foreground="#202733", height=2, pady=0, width=4)
        self.swd_pressure_label.grid(row=4, column=1, sticky="WE")



        # CREATING WATER HEIGHT DISPLAY FRAME
        #############################

        self.water_height_stats_frame = Frame(self, background="#0E1116", width=15)
        self.water_height_stats_frame.grid(row=4, column=1, padx=(0, 20), pady=(0, 20), sticky="NESW")

        # Add current wave height
        self.max_wave_height_var = StringVar()
        self.max_wave_height_var.set("N/A")
        self.max_wave_height_number = Label(self.water_height_stats_frame, anchor=CENTER, textvariable=self.max_wave_height_var, font=("Roboto", 36, "bold"), 
                                        background="#0E1116", foreground="#202733", width=8)
        self.max_wave_height_number.grid(row=0, column=0, columnspan=2, sticky="WE", pady=(15, 0))
        self.max_wave_height_label = Label(self.water_height_stats_frame, anchor=CENTER, text="Peak Wave Height (cm)", font=("Roboto", 12, "bold"), 
                                        background="#0E1116", foreground="#202733", height=1)
        self.max_wave_height_label.grid(row=1, column=0, columnspan=2, sticky="WE")

        # Add max wave height
        self.current_wave_height_var = StringVar()
        self.current_wave_height_var.set("N/A")
        self.current_wave_height_number = Label(self.water_height_stats_frame, anchor=CENTER, textvariable=self.current_wave_height_var, font=("Roboto", 36, "bold"), 
                                        background="#0E1116", foreground="#202733", width=8)
        self.current_wave_height_number.grid(row=2, column=0, columnspan=2, sticky="WE", pady=(15, 0))
        self.current_wave_height_label = Label(self.water_height_stats_frame, anchor=CENTER, text="Current Wave Height (cm)", font=("Roboto", 12, "bold"), 
                                        background="#0E1116", foreground="#202733", height=1)
        self.current_wave_height_label.grid(row=3, column=0, columnspan=2, sticky="WE")

        # Add min water height
        self.min_water_height_var = StringVar()
        self.min_water_height_var.set("N/A")
        self.min_water_height_number = Label(self.water_height_stats_frame, textvariable=self.min_water_height_var, font=("Roboto", 20, "bold"), 
                                        background="#0E1116", foreground="#202733", width=4)
        self.min_water_height_number.grid(row=4, column=0, sticky="WE", pady=(15, 0))
        self.min_water_height_label = Label(self.water_height_stats_frame, text="Minimum\nWater Height", font=("Roboto", 8), 
                                        background="#0E1116", foreground="#202733", height=2, pady=0, width=4)
        self.min_water_height_label.grid(row=5, column=0, sticky="WE")

        # Add max water height
        self.max_water_height_var = StringVar()
        self.max_water_height_var.set("N/A")
        self.max_water_height_number = Label(self.water_height_stats_frame, textvariable=self.max_water_height_var, font=("Roboto", 20, "bold"), 
                                        background="#0E1116", foreground="#202733", width=4)
        self.max_water_height_number.grid(row=4, column=1, sticky="WE", pady=(15, 0))
        self.max_water_height_label = Label(self.water_height_stats_frame, text="Maximum\nWater Height", font=("Roboto", 8), 
                                        background="#0E1116", foreground="#202733", height=2, pady=0, width=4)
        self.max_water_height_label.grid(row=5, column=1, sticky="WE")

        ####################################################################################
        ########################### CREATING ALARM STATUS FRAME ############################
        ####################################################################################

        # Create frame to show the current alarm status
        self.alarm_status_frame = Frame(self, background="#0E1116", width=15)
        self.alarm_status_frame.grid(row=5, column=1, rowspan=2, padx=(0, 20), pady=(0, 20), sticky=NSEW)
        # Make column 0 take up the entire frame
        self.alarm_status_frame.columnconfigure(0, weight=1)

        # Create photo images for every alarm icon
        self.alarm_not_ready_img = PhotoImage(file="resources/alarm_not_ready.png")
        self.alarm_ready_img = PhotoImage(file="resources/alarm_ready.png")
        self.alarm_activated_img = PhotoImage(file="resources/alarm_activated.png")
        self.alarm_activated_big_img = PhotoImage(file = "resources/alarm_activated_big.png")

        # Create a label for the current status of the alarm
        self.alarm_status_image_label = Label(self.alarm_status_frame, image=self.alarm_not_ready_img, background="#0E1116", anchor=CENTER)
        self.alarm_status_image_label.grid(row=0, column=0, sticky=NSEW, padx=10, pady=(10, 5))

        self.alarm_status_label = Label(self.alarm_status_frame, anchor=CENTER, text="Alarm: Not Ready", font=("Roboto", 16, "bold"), 
                                        background="#0E1116", foreground="#202733", height=1)
        self.alarm_status_label.grid(row=1, column=0, sticky=NSEW, padx=10, pady=(0, 10))


    def connect_serial(self):
        """Connect to serial port specified"""

        # Attempt to connect to serial
        success = self.data_transmitter.connect_serial("COM5", 115200)
        if success:
            self.status_var.set("Arduino connected!")
            self.pressure_calibrate_button.enable()
        else:
            self.status_var.set("Failed to connect to Arduino")


    def mainloop(self):

        while True:

            time_since_init = time.time() - self.init_time

            self.graph.set_center(time_since_init)
            self.graph.update_subplots(self.data_period_var.get())      

            # Update graph text
            self.update_graph_text()

            # Draw canvas
            self.graph.draw_canvas()

            # Update statistics
            self.update_statistics()

            # Check if message needs to be sent
            if self.alarm_cooldown == False and self.alarm_sent == True:

                self.alarm_cooldown = True

                self.window_activate_alarm()

            # Update date and time on top
            self.update_date_time()

            # Update window widgets
            self.update()
            self.update_idletasks()



    def window_activate_alarm(self):
        """Runs when the alarm is activated. Runs in the while loop on the main thread"""

        # Get current date and time
        now = datetime.now()
        # Format date and time as string
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

        # Send message on status var
        self.status_var.set("{} > TSUNAMI ALARM ACTIVATED: Wave height threshold breached".format(dt_string))
        self.status_label.configure(foreground="#FB3640")

        # Set alarm status to activated
        self.change_alarm_status("activated")

        # Open popup window to get attention of dashboard user
        self.alarm_pop_up(date_and_time=dt_string, pressure=self.pressure_on_alarm_activate, wave_height=self.wave_height_on_alarm_activate)

        # Enable reset alarm button
        self.reset_alarm_button.enable()


    def reset_alarm(self):
        """Resets alarm on dashboard"""

        # Revert status var
        self.status_var.set("Alarm system reset and set to Ready.")
        self.status_label.configure(foreground="#E4FDE1")

        # Change alarm status back to ready
        self.change_alarm_status("ready")

        # Reset alarm sending variables
        self.alarm_sent = False
        self.alarm_cooldown = False
        self.pressure_on_alarm_activate = None
        self.wave_height_on_alarm_activate = None

        # Disable reset alarm button so it cannot be used until alarm is activated
        self.reset_alarm_button.disable()


    def update_graph_text(self):
        """Update the text on the graph figure, including the pressure, water height and wave threshold displays."""

        # UPDATING PRESSURE GRAPH

        # Get subplot limits from pressure subplot
        pressure_g_xlim = list(self.pressure_subplot.get_xlim())
        pressure_g_ylim = list(self.pressure_subplot.get_ylim())

        # Calculate positional values - this will assist in creating the text
        pressure_g_middle_x = sum(pressure_g_xlim) / 2
        pressure_g_middle_y = sum(pressure_g_ylim) / 2
        pressure_g_size_x = pressure_g_xlim[1] - pressure_g_xlim[0]
        pressure_g_size_y = pressure_g_ylim[1] - pressure_g_ylim[0]

        # Get coordinates of last point on pressure subplot
        pressure_last_x, pressure_last_y = self.graph.get_data_point(0, -1)

        # Check if a last position on the graph exists
        if pressure_last_x != None or pressure_last_y != None:
            # Set the text to the current pressure rounded to 2 decimal places with hPa units
            self.current_pressure_text.set_text("{:.2f} hPa".format(pressure_last_y))
            self.current_pressure_text.set_x(pressure_g_middle_x + (pressure_g_size_x / 6) + pressure_g_size_x / 48)
            if pressure_last_y - pressure_g_ylim[0] > pressure_g_size_y / 12:
                self.current_pressure_text.set_y(pressure_last_y)
            else:
                self.current_pressure_text.set_y(pressure_g_ylim[0] + pressure_g_size_y / 12)
        else:
            # Set the text to be displayed in the middle of the graph
            self.current_pressure_text.set_x(pressure_g_middle_y)
            self.current_pressure_text.set_y(pressure_g_middle_y)


        # UPDATING WATER HEIGHT GRAPH
        # Get subplot limits from water height subplot
        waterh_g_xlim = list(self.water_height_subplot.get_xlim())
        waterh_g_ylim = list(self.water_height_subplot.get_ylim())

        # Calculate positional values - this will assist in creating the text
        waterh_g_middle_x = sum(waterh_g_xlim) / 2
        waterh_g_middle_y = sum(waterh_g_ylim) / 2
        waterh_g_size_x = waterh_g_xlim[1] - waterh_g_xlim[0]
        waterh_g_size_y = waterh_g_ylim[1] - waterh_g_ylim[0]

        # Get coordinates of last point on pressure subplot
        waterh_last_x, waterh_last_y = self.graph.get_data_point(1, -1)

        # Check if a last position on the graph exists
        if waterh_last_x != None or waterh_last_y != None:
            # Set the text to the current water height rounded to 2 decimal places with hPa units
            self.current_water_height_text.set_text("{:.2f} cm".format(waterh_last_y))
            self.current_water_height_text.set_x(waterh_g_middle_x + (waterh_g_size_x / 6) + waterh_g_size_x / 48)
            if waterh_last_y - waterh_g_ylim[0] > waterh_g_size_y / 12:
                self.current_water_height_text.set_y(waterh_last_y)
            else:
                self.current_water_height_text.set_y(waterh_g_ylim[0] + waterh_g_size_y / 12)
        else:
            # Set the text to be displayed in the middle of the graph
            self.current_pressure_text.set_x(waterh_g_middle_x)
            self.current_pressure_text.set_y(waterh_g_middle_y)

        # Put text on alarm threshold
        if self.alarm_threshold != None:
            self.alarm_threshold_text.set_text("ALARM THRESHOLD: {:.2f} cm".format(self.alarm_threshold + self.standing_water_level))
            self.alarm_threshold_text.set_x(waterh_g_xlim[1] - waterh_g_size_x / 64)
            self.alarm_threshold_text.set_y(self.alarm_threshold + self.standing_water_level + waterh_g_size_y / 48)




        
    def new_pressure_data(self, pressure):
        """
            Send pressure data from the data transmitter to the dashboard. 
            Usually ran in a seperate thread
        """

        # Get the time since initialisation, and use that as x coordinate on graph
        time_since_init = time.time() - self.init_time
        self.pressure_data[0].append(time_since_init)

        # Use pressure as y coordinate on graph
        self.pressure_data[1].append(pressure)

        # Add data point to pressure graph
        self.graph.add_data_point(0, time_since_init, pressure)

        # Calculate water height from pressure
        if self.calibrated_air_pressure != None:
            water_height = self.calculate_water_height(pressure)
            self.graph.add_data_point(1, time_since_init, water_height)

            if self.standing_water_level != None and self.alarm_threshold != None:

                # Check if water height has broken threshold
                wave_height =  water_height - self.standing_water_level
                if wave_height > self.alarm_threshold and self.alarm_sent == False:

                    # Save the pressure wave height on alarm activation
                    self.pressure_on_alarm_activate = pressure
                    self.wave_height_on_alarm_activate = wave_height

                    self.alarm_sent = True

                    # SEND TSUNAMI ALARM IN DIFFERENT THREAD
                    send_alarm_thread = threading.Thread(target=self.send_alarm)
                    send_alarm_thread.start()


    def send_alarm(self):
        """Start the alarm. Ran when the wave height threshold is breached."""

        self.data_transmitter.send_alarm()            

    
    def data_period_change(self, period):
        """Called when the data period slider is changed"""

        # Snap slider to every 5
        self.data_period_slider.set(round(float(int(period) / 5)) * 5)
        self.data_period_var.set(round(float(int(period) / 5)) * 5)

        # Update text next to top right in statistics
        self.period_data_label.configure(text="Last {:.2f} seconds".format(self.data_period_var.get()))


    def calculate_water_height(self, pressure):
        """Calculate water height in centimetres using formula P = P0 + pgh"""

        # Set constants
        WATER_DENSITY = 997 # p - Density of water (kgm^-3)
        GRAVITY_FORCE = 9.81 # g - Weight of gravity (ms^-2)

        # Calculate water height (h) in metres using formula P = P0 + pgh
        water_height = ((pressure - self.calibrated_air_pressure) * 100) / (WATER_DENSITY * GRAVITY_FORCE)

        if water_height < 0:
            return 0

        # Convert water height into centimetres and return value
        return (water_height * 100)
    


    def update_statistics(self):
        """Updates statistics, showing the statistics in the last self.data_period seconds."""

        # Get data points
        time_since_init = time.time() - self.init_time
        pressure_xs, pressure_ys = self.graph.get_data_within_last_x(0, time_since_init - self.data_period_var.get())
        water_height_xs, water_height_ys = self.graph.get_data_within_last_x(1, time_since_init - self.data_period_var.get())

        # Calculate maximum pressure
        max_pressure = None
        min_pressure = None
        if len(pressure_ys) > 0:

            # Calculate max pressure and light up statistic's color
            max_pressure = max(pressure_ys)
            min_pressure = min(pressure_ys)

            # Change the maximum and minimum y limits of the pressure graph, so it displays all data correctly
            # without going out of bounds
            ylim_min = self.pressure_graph_default_ylim[0]
            ylim_max = self.pressure_graph_default_ylim[1]
            if min_pressure - self.pressure_graph_ylim_buffer < ylim_min:
                ylim_min = min_pressure - self.pressure_graph_ylim_buffer
            
            if max_pressure + self.pressure_graph_ylim_buffer > ylim_max:
                ylim_max = max_pressure + self.pressure_graph_ylim_buffer

            self.pressure_subplot.set_ylim(ylim_min, ylim_max)


        # Change display of maximum pressure
        self.change_stat_display(max_pressure, self.max_pressure_var, self.max_pressure_number, self.max_pressure_label,
                                     number_color="#E4FDE1", label_color="#E4FDE1")
            
        # Change display of calibrated air pressure if air pressure has been calibrated
        self.change_stat_display(self.calibrated_air_pressure, self.air_pressure_var, self.air_pressure_number_label, self.air_pressure_label,
                                     number_color="#E4FDE1", label_color="#E4FDE1")
        
        # Change display of standing water pressure if standing water height pressure has been calibrated
        self.change_stat_display(self.standing_water_air_pressure, self.swd_pressure_var, self.swd_pressure_number, self.swd_pressure_label,
                                     number_color="#E4FDE1", label_color="#E4FDE1")
        

        # Calculate maximum water height
        max_wave_height = None
        current_wave_height = None

        max_water_height = None
        min_water_height = None

        max_wave_height_color = "#E4FDE1"
        current_wave_height_color = "#E4FDE1"

        if len(water_height_ys) > 0:

            min_water_height = min(water_height_ys)
            max_water_height = max(water_height_ys)

            if self.standing_water_level != None:

                # Get max wave height and current wave height
                max_wave_height = max_water_height - self.standing_water_level
                current_wave_height = water_height_ys[0] - self.standing_water_level
                
                # Set lower boundary to 0
                if max_wave_height < 0: max_wave_height = 0
                if current_wave_height < 0: current_wave_height = 0

                # Change color of max and current wave height colors
                if self.alarm_threshold != None:
                    max_wave_height_color = self.get_number_color(max_wave_height, self.alarm_threshold)
                    current_wave_height_color = self.get_number_color(current_wave_height, self.alarm_threshold)

            # Change the maximum y limit of the water height graph, so it displays all data correctly
            # without going out of bounds (the minimum will always be)
            ylim_min = self.water_height_graph_default_ylim[0]
            ylim_max = self.water_height_graph_default_ylim[1]
            if max_water_height + self.water_height_graph_ylim_buffer > ylim_max:
                ylim_max = max_water_height + self.water_height_graph_ylim_buffer

            self.water_height_subplot.set_ylim(ylim_min, ylim_max)

        # Change display if air pressure has been calibrated
        self.change_stat_display(max_wave_height, self.max_wave_height_var, self.max_wave_height_number, self.max_wave_height_label,
                                     number_color=max_wave_height_color, label_color="#E4FDE1")
        
        self.change_stat_display(current_wave_height, self.current_wave_height_var, self.current_wave_height_number, self.current_wave_height_label,
                                     number_color=current_wave_height_color, label_color="#E4FDE1")
        
        # Change display if air pressure has been calibrated
        self.change_stat_display(max_water_height, self.max_water_height_var, self.max_water_height_number, self.max_water_height_label,
                                     number_color="#E4FDE1", label_color="#E4FDE1")
        
        self.change_stat_display(min_water_height, self.min_water_height_var, self.min_water_height_number, self.min_water_height_label,
                                     number_color="#E4FDE1", label_color="#E4FDE1")
        

    
    def get_number_color(self, number, max):   
        """Gets the color of a display number, scaling from turquoise to red"""

        if max == 0: return "#E4FDE1"

        # Calculate ratio of number compared to max
        ratio = number / max

        if ratio > 1:
            # If larger than max, make color red
            return "#FB363A"
        elif ratio > 0.75:
            # If larger than 75% of the max, make color orange
            return "#F97E36"
        elif ratio > 0.5:
            # If larger than 50% of the max, make color yellow
            return "#E8E055"
        else:
            # Return normal blue
            return "#41D3BD"

        

    def update_date_time(self):
        """Update date and time at top of window"""

        # Get current date and time
        now = datetime.now()
 
        # Format date and time as string
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        
        # Set variable to string
        self.date_time_stringvar.set(dt_string)

        

        

        
    def change_stat_display(self, stat, var, number_widget, label_widget, number_color, label_color):

        if stat != None:

            var.set("{:.2f}".format(stat))
            number_widget.configure(foreground=number_color)
            label_widget.configure(foreground=label_color)

        else:

            var.set("N/A")
            number_widget.configure(foreground="#202733")
            label_widget.configure(foreground="#202733")

    

    def calibrate_pressure_button_pressed(self):
        """Function connected to the calibrate button being pressed"""

        print("Calibrating air pressure...")
        self.status_var.set("Calibrating air pressure...")

        # Disable calibration button
        self.pressure_calibrate_button.disable()

        # Calibrate air pressure for 5 seconds
        self.after(5000, self.calibrate_air_pressure, 5)


    def calibrate_air_pressure(self, length):
        """Calibrates the environment's average air pressure in the last length seconds"""

        time_since_init = time.time() - self.init_time
        pressure_data_points = []

        index = 1
        while True:

            # Find data point on pressure graph
            time_recorded, pressure_recorded = self.graph.get_data_point(0, -index)
            if time_recorded == None or pressure_recorded == None: break

            if time_since_init - time_recorded <= length:
                pressure_data_points.append(pressure_recorded)
            else:
                break
            index += 1

        # Calculate mean air pressure in the last length seconds
        try:
            self.calibrated_air_pressure = sum(pressure_data_points) / len(pressure_data_points)
        except ZeroDivisionError:
            # No data points were collected
            print("Could not calibrate air pressure, lack of data")
            self.status_var.set("Could not calibrate air pressure, lack of data")
            return

        # Enable pressure calibrate button again
        self.pressure_calibrate_button.enable()
        self.set_standing_depth_button.enable()

        self.status_var.set("Air pressure calibrated to be {:.2f} hPa".format(self.calibrated_air_pressure))
        print("Air pressure calibrated to be {:.2f} hPa".format(self.calibrated_air_pressure))


    def set_alarm_threshold(self):

        # Can only set alarm threshold if standing 
        if self.standing_water_level == None:
            self.status_var.set("You must calibrate standing wave height first before entering the alarm threshold.")
            self.alarm_threshold_var.set("")
            return
        
        try:
            alarm_threshold = float(self.alarm_threshold_var.get())
        except ValueError:
            self.status_var.set("Alarm threshold must be a float number")
            self.alarm_threshold_var.set("")
            return
            
        if (alarm_threshold < 0):
            self.status_var.set("Alarm threshold must be greater than 0")
            self.alarm_threshold_var.set("")
            return
        
        # Set alarm threshold
        self.alarm_threshold = alarm_threshold
        self.alarm_threshold_line.set_ydata([alarm_threshold + self.standing_water_level, alarm_threshold + self.standing_water_level])
        self.alarm_threshold_var.set("{:.2f}".format(alarm_threshold))
        self.status_var.set("Alarm threshold set to {:.2f}".format(alarm_threshold))

        # Set alarm status to ready
        self.change_alarm_status("ready")


    def calibrate_swh_button_pressed(self):
        """Function connected to the calibrate standing water height button being pressed"""

        print("Calibrating standing water height...")
        self.status_var.set("Calibrating standard water height...")

        # Disable calibration button
        self.set_standing_depth_button.disable()

        # Calibrate air pressure for 5 seconds
        self.after(5000, self.calibrate_swh, 5)


    def calibrate_swh(self, length):
        """Calibrates the standing water height once the sensor is in the bottom of the water"""

        time_since_init = time.time() - self.init_time
        water_height_data_points = []

        x_points, pressure_data_points = self.graph.get_data_within_last_x(0, time_since_init - length)
        x_points, water_height_data_points = self.graph.get_data_within_last_x(1, time_since_init - length)

        # Calculate mean air pressure in the last length seconds
        try:
            self.standing_water_level = sum(water_height_data_points) / len(water_height_data_points)
            self.standing_water_air_pressure = sum(pressure_data_points) / len(pressure_data_points)
        except ZeroDivisionError:
            # No data points were collected
            print("Could not calibrate standing water height, lack of data")
            self.status_var.set("Could not calibrate standing water height, lack of data")
            return

        # Enable water height calibrate button again
        self.set_standing_depth_button.enable()
        self.standing_water_height_line.set_ydata([self.standing_water_level, self.standing_water_level])

        self.status_var.set("Standing water height calibrated to be {:.2f} cm".format(self.standing_water_level))
        print("Standing water height calibrated to be {:.2f} cm".format(self.standing_water_level))


    def change_alarm_status(self, alarm_status):
        """Changes alarm status display to 3 states - 'not ready', 'ready' and 'activated'."""

        # If alarm is not ready, set image and color to gray
        if alarm_status == "not ready":
            self.alarm_status_image_label.configure(image=self.alarm_not_ready_img)
            self.alarm_status_label.configure(foreground="#1A1F28", text="Alarm: Not Ready")

        # If alarm is ready, set image and color to turquoise
        elif alarm_status == "ready":
            self.alarm_status_image_label.configure(image=self.alarm_ready_img)
            self.alarm_status_label.configure(foreground="#41D3BD", text="Alarm: Ready")
        
        # If alarm has been activated, set image and color to red
        elif alarm_status == "activated":
            self.alarm_status_image_label.configure(image=self.alarm_activated_img)
            self.alarm_status_label.configure(foreground="#FB363A", text="Alarm: ACTIVATED")

    
    def alarm_pop_up(self, date_and_time, pressure, wave_height):
        """Creates a pop up window to alert dashboard user that the alarm threshold has been breached."""

        # Create popup window
        popup_win = Toplevel(self, background="#06070A")
        popup_win.title("ALERT - Tsunami Threshold Breached")

        # Add warning symbol -- point is to capture attention of user
        warning_symbol_label = Label(popup_win, image=self.alarm_activated_big_img, background="#06070A", anchor=CENTER)
        warning_symbol_label.grid(row=0, column=0, sticky=NSEW, padx=(10, 30), pady=(10, 0), rowspan=3)

        # Add header label
        header_label = Label(popup_win, text="TSUNAMI ALARM ACTIVATED", font=("Roboto", 30, "bold"), 
                                        background="#06070A", foreground="#FB363A")
        header_label.grid(row=0, column=1, sticky=NSEW, padx=20, pady=5)

        # Create string of information
        information_str = ""

        # Add date and time to information string
        information_str += "Time activated: {}\n".format(date_and_time)

        # Add pressure reading 
        information_str += "Pressure reading: {:.2f} hPa\n".format(pressure)

        # Add wave height reading
        information_str += "Wave height reading: {:.2f} cm".format(wave_height)

        # Show pressure reading
        information_label = Label(popup_win, text=information_str, font=("Roboto", 14, "bold"), 
                                        background="#06070A", foreground="#E4FDE1", anchor=W, justify=LEFT)
        information_label.grid(row=1, column=1, sticky=NSEW, padx=20, pady=(0, 3))

        # Create button to close window
        close_button = HoverButton(popup_win, text="Close", font=("Roboto", 14, "bold"), pady=0, padx=0,
                                                      background="#FB3640", foreground="#190A0B", hoverbackground="#721922", activebackground="#FF6675",
                                                      command=popup_win.destroy)
        close_button.grid(row=2, column=1, padx=20, pady=(0, 3))

        popup_win.update()
        popup_win.update_idletasks()








class UpdatingGraphFigure():

    """An updating line graph that scrolls on the x axis displayed using matplotlib."""

    def __init__(self, root, graphs_x, graphs_y):
        
        # Define list of graph axes
        self.axes_list = []

        # Define list of graph line artists
        self.axes_lines = []

        # Define datapoints of each graph -- this will be a nested list
        self.x_points = []
        self.y_points = []

        # Define graph size
        self.x_center = 0
        self.y_boundary = [0, 5]

        # Define root tkinter parent
        self.root = root

        self.hlines = []
        self.text = []
        self.scrolling_text = []

        # Create graphs
        self.create_subplots(graphs_x, graphs_y)

    def create_subplots(self, graphs_x, graphs_y):
        """Create the desired amount of graphs and put them onto the window"""
        
        # Add amount of desired subplots with data
        self.fig, axes_array = matplotlib.pyplot.subplots(graphs_y, graphs_x)

        # Matplotlib returns a singular Axes, not an a
        if isinstance(axes_array, matplotlib.axes.Axes):
            self.axes_list.append(self.axes)
        else:
            self.axes_list = list(axes_array)

        # Set display values of graph frame
        self.fig.set_size_inches(13, 6.8)
        self.fig.set_facecolor("#F0F0F0")

        # Setup subplots
        for subplot in self.axes_list:

            # Create empty datapoints list for each subplot 
            self.x_points.append([])
            self.y_points.append([])

            # Create dictionary for each subplot's horizontal lines
            self.hlines.append({})

            # Capture the graph line artist for each subplot
            line = subplot.plot([], [])[0]
            self.axes_lines.append(line)

        # Create the tkinter canvas containing the graph
        self.canvas = FigureCanvasTkAgg(self.fig, master = self.root)
        self.canvas.draw()

    def update_subplots(self, data_period):
        """Update the subplots with new data. new_period is the amount of data to show."""

        # Set plot limits
        # Set the plot limits of the x axis so that the current time on the graph is 2/3rds to the right
        x_lim_left = self.x_center - data_period
        x_lim_right = self.x_center + data_period / 2

        # Update all subplots
        for i, subplot in enumerate(self.axes_list):

            # Get information of subplot
            subplot_line = self.axes_lines[i]
            x_data = self.x_points[i]
            y_data = self.y_points[i]

            # Set data points of the subplot line
            subplot_line.set_xdata(self.x_points[i])
            subplot_line.set_ydata(self.y_points[i])

            # Set limits of subplot
            subplot.set_xlim(left=x_lim_left, right=x_lim_right)

    def draw_canvas(self):
        """ Draw the canvas of the subplots figure"""
        self.canvas.draw()

    def get_subplot(self, subplot_num):
        """Get a subplot by its index number"""

        # Get subplot by index, if no subplot exists for desired index return None
        try:
            return self.axes_list[subplot_num]
        except IndexError:
            return None

    def add_data_point(self, subplot_num, x, y):
        """Add data point to the desired subplot and update it"""

        # Get current data coordinates for the desired graph and check if desired graph exists
        try:
            x_data = self.x_points[subplot_num]
            y_data = self.y_points[subplot_num]
        except IndexError:
            return
    
        # Append coordinate points to list
        x_data.append(x)
        y_data.append(y)

    def get_data_point(self, subplot_num, point_index):
        """Gets a datapoint from a subplot at a certain index"""

        # Get current data coordinates for the desired graph and check if desired graph exists
        try:
            x_point = self.x_points[subplot_num][point_index]
            y_point = self.y_points[subplot_num][point_index]
        except IndexError:
            return None, None
        
        return x_point, y_point
    

    def get_data_within_last_x(self, subplot_num, min_x):
        """Gets all data points on a subplot within the last data_period on the x axis."""

        # Get correct subplot, and return nothing
        subplot = self.get_subplot(subplot_num)
        if subplot == None: return None
        
        # Get data points of the subplot
        subplot_x_points = self.x_points[subplot_num]
        subplot_y_points = self.y_points[subplot_num]

        x_within_boundaries = []
        y_within_boundaries = []

        # Go through list of points backwards
        index = 1

        while True:
            try:
                # Get negative index to go through points backwards
                x_point = subplot_x_points[-index]
                y_point = subplot_y_points[-index]
            except IndexError:
                # If index is out of range
                break

            # If x point is smaller than min x, break the loop
            if x_point < min_x:
                break

            # Otherwise, add to points
            x_within_boundaries.append(x_point)
            y_within_boundaries.append(y_point)

            index += 1


        return x_within_boundaries, y_within_boundaries
        
    def set_center(self, x_center):
        """Set the center of the graph in x."""

        self.x_center = x_center



class HoverButton(Button):
    """A button that does a certain action when hovered over (e.g. gets colored when hovered over.)"""

    def __init__(self, master, hoverbackground = None, hoverforeground = None, disabledbackground = None, *args, **kwargs):

        super().__init__(master=master, *args, **kwargs)

        self.default_background = self["background"]
        self.default_foreground = self["foreground"]

        # Set hover background color
        if hoverbackground != None:
            self.hover_background = hoverbackground
        else:
            self.hover_background = self.default_background

        # Set hover foreground color
        if hoverforeground != None:
            self.hover_foreground = hoverforeground
        else:
            self.hover_foreground = self.default_foreground

        # Set disabled background color
        if disabledbackground != None:
            self.disabled_background = disabledbackground
        else:
            self.disabled_background = self.default_background

        # Check if button is currently in disabled state
        if self["state"] == DISABLED:
            # Disable button to set color
            self.disable()

        # Bind enter and leave button actions
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)


    def disable(self):
        """Puts the button in a disabled state (cannot be clicked)."""

        # Set button to disabled and set background to disabled background
        self.configure(state=DISABLED, background=self.disabled_background, foreground=self["disabledforeground"])


    def enable(self):
        """Puts the button in an enabled state (can be clicked)."""

        # Set button to active and set background to disabled background
        self.configure(state=NORMAL, background=self.default_background, foreground=self.default_foreground)

    
    def on_enter(self, e):
        """Runs when the mouse cursor enters the bounding box of the button."""

        # Make sure to revert to default colors if disabled
        if self["state"] == DISABLED: 
            self.disable()
        else:   
            self.configure(background = self.hover_background, foreground = self.hover_foreground)


    def on_leave(self, e):
        """Runs when the mouse cursor leaves the bounding box of the button."""
        
        # Make sure to revert to default colors if disabled
        if self["state"] == DISABLED: 
            self.disable()
        else:   
            self.configure(background = self.default_background, foreground = self.default_foreground)