
import csv
from PySide6.QtGui import (
    QPixmap,
)
from PySide6.QtWidgets import (
    QLabel,
    QWidget,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QComboBox,
    QPushButton,
)

class Data(QWidget):
    def __init__(self):
        super().__init__()

        # create a QHBoxLayout to hold all of the elements within the flight view-- orients the main telemetry text display next to the GPS map
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)

        # -------------------------------------------------------------------------
        #
        # widgets and layouts for the informational display
        #
        # -------------------------------------------------------------------------

        # create a vertical box layout
        information_layout = QVBoxLayout()
        information_layout.setSpacing(0)

        # QFormLayout is useful for a bunch of labeled information, aka the telemetry data with labels pointing to the updating values
        car_info_layout = QGridLayout()
        car_info_layout.setSpacing(3)

        # since these need to be reference later, along with all of the labels above containing dynamic information, these need
        # to be fields of the object, initialized with self.<name>
        self.mph = QLabel("-- mph")
        self.rpm = QLabel("--")
        self.tire_pressure = QLabel("-- psi")
        self.coolant_temperature = QLabel("--")
        self.battery_voltage = QLabel("-- volts")
        self.fuel_guage = QLabel("--")
        self.oil_pressure = QLabel("--")
        self.intake_air_temperature = QLabel("--")
        self.intake_air_flow = QLabel("--")
        
        # this object name is purely to set the minimum length of the heading label, to prevent the
        # items moving around when the numbers change
        self.mph.setObjectName("mph")

        # create labels as an array to efficiently add them to the QGridLayout
        labels = [QLabel("Speed: "), QLabel("Engine RPM: "), QLabel("Tire Pressure: "), QLabel("Coolant Temperature: "),
                  QLabel("Battery Voltage: "), QLabel("Fuel Guage: "), QLabel("Oil Pressure: "), QLabel("Intake Air Temp: "),
                  QLabel("Intake Air Flow: ")]
        # iterate through the labels, setting the object name as 'small' and then adding to the appropriate row
        for i, label in enumerate(labels):
            label.setObjectName("small")
            car_info_layout.addWidget(label, i, 0)

        # add the information labels to the QGridLayout
        car_info_layout.addWidget(self.mph, 0, 1)
        car_info_layout.addWidget(self.rpm, 1, 1)
        car_info_layout.addWidget(self.tire_pressure, 2, 1)
        car_info_layout.addWidget(self.coolant_temperature, 3, 1)
        car_info_layout.addWidget(self.battery_voltage, 4, 1)
        car_info_layout.addWidget(self.fuel_guage, 5, 1)
        car_info_layout.addWidget(self.oil_pressure, 6, 1)
        car_info_layout.addWidget(self.intake_air_temperature, 7, 1)
        car_info_layout.addWidget(self.intake_air_flow, 8, 1)

        # add the "main_info_layout" QFormLayout to the information layout

        # Header for the GCar information
        information_layout.addWidget(QLabel("Engine Telemetry Information"))

        information_layout.addLayout(car_info_layout)

        # -------------------------------------------------------------------------
        #
        # widget and layout for the GPS Map
        #
        # -------------------------------------------------------------------------

        map_layout = QVBoxLayout()
        self.gps_map = QLabel()

        self.map_dimensions = (1000,625)
        self.map_center = [self.map_dimensions[0]//2, self.map_dimensions[1]//2]
        self.map_zoom_factor = 1

        map_layout.addWidget(self.gps_map)

        # -------------------------------------------------------------------------
        #
        # Layout for the information displayed at the bottom of the image
        #
        # -------------------------------------------------------------------------

        # it's called 'data_layout' because I am running out of names that are different versions of 'information'
        data_layout = QHBoxLayout()

        # -------------------------------------------------------------------------
        #
        # GPS Information
        #
        # -------------------------------------------------------------------------

        # Header for the GPS information
        information_layout.addWidget(QLabel("GPS Information"))
        
        # QFormLayout is useful for a bunch of labeled information, aka the telemetry data with labels pointing to the updating values
        gps_info_layout = QGridLayout()
        gps_info_layout.setSpacing(3)

        # since these need to be reference later, along with all of the labels above containing dynamic information, these need
        # to be fields of the object, initialized with self.<name>
        self.lat = QLabel("-- degrees")
        self.lon = QLabel("-- degrees")
        self.hdg = QLabel("--")
        self.hdop = QLabel("--")
        self.vdop = QLabel("--")
        self.num_satellites = QLabel("--")
        
        # this object name is purely to set the minimum length of the heading label, to prevent the
        # items moving around when the numbers change
        self.mph.setObjectName("mph")

        # create labels as an array to efficiently add them to the QGridLayout
        labels = [QLabel("Latitude: "), QLabel("Longitude: "), QLabel("Heading: "), QLabel("HDOP: "), QLabel("VDOP: "), QLabel("# of Satellites: ")]
        # iterate through the labels, setting the object name as 'small' and then adding to the appropriate row
        for i, label in enumerate(labels):
            label.setObjectName("small")
            gps_info_layout.addWidget(label, i, 0)

        # add the information labels to the QGridLayout
        gps_info_layout.addWidget(self.lat, 0, 1)
        gps_info_layout.addWidget(self.lon, 1, 1)
        gps_info_layout.addWidget(self.hdg, 2, 1)
        gps_info_layout.addWidget(self.hdop, 3, 1)
        gps_info_layout.addWidget(self.vdop, 4, 1)
        gps_info_layout.addWidget(self.num_satellites, 5, 1)

        information_layout.addLayout(gps_info_layout)

        # this creates a label to display the fix_type of the gps
        self.gps_status = QLabel("No Fix")
        # the object name is assigned to give the object a mimum width, to keep UI elements
        # from jumping when the length of the message changes
        information_layout.addWidget(self.gps_status)

        # -------------------------------------------------------------------------
        #
        # Map navigation buttons
        #
        # -------------------------------------------------------------------------

        # to navigate the map, create a set of buttons using a QGridLayout
        navigate_layout = QGridLayout()
        # because the qss style sheets don't provide access to all of the styling options, this is necessary to move the items closer together
        navigate_layout.setHorizontalSpacing(10)
        navigate_layout.setVerticalSpacing(1)

        # Create the push button items, and set their styling correctly
        self.map_up = QPushButton("^")
        self.map_up.setObjectName("navigation")
        self.map_up.setToolTip("Navigate map up")
        self.map_up.clicked.connect(self.map_up_pressed)

        self.map_down = QPushButton("⌄")
        self.map_down.setObjectName("navigation")
        self.map_down.setToolTip("Navigate map down")
        self.map_down.clicked.connect(self.map_down_pressed)

        self.map_left = QPushButton("<")
        self.map_left.setObjectName("navigation")
        self.map_left.setToolTip("Navigate map left")
        self.map_left.clicked.connect(self.map_left_pressed)

        self.map_right = QPushButton(">")
        self.map_right.setObjectName("navigation")
        self.map_right.setToolTip("Navigate map right")
        self.map_right.clicked.connect(self.map_right_pressed)

        self.map_zoom_in = QPushButton("+")
        self.map_zoom_in.setObjectName("navigation")
        self.map_zoom_in.setToolTip("Zoom in on map")
        self.map_zoom_in.clicked.connect(self.map_zoom_in_pressed)

        self.map_zoom_out = QPushButton("-")
        self.map_zoom_out.setObjectName("navigation")
        self.map_zoom_out.setToolTip("Zoom out on map")
        self.map_zoom_out.clicked.connect(self.map_zoom_out_pressed)

        # add each of the items into the QGridLayout by index
        navigate_layout.addWidget(self.map_zoom_in, 0, 0)
        navigate_layout.addWidget(self.map_zoom_out, 0, 2)
        navigate_layout.addWidget(self.map_left, 2, 0)
        navigate_layout.addWidget(self.map_right, 2, 2)
        navigate_layout.addWidget(self.map_up, 1, 1)
        navigate_layout.addWidget(self.map_down, 2, 1)

        #navigate_widget.setLayout(navigate_layout)
        data_layout.addLayout(navigate_layout)

        # Now create a QComboBox to select which GPS map screenshot is used for the display
        self.map_location = QComboBox()
        self.map_locations_dict = self.getMapLocations()
        data_layout.addWidget(self.map_location)

        # to set the size of this widget to ensure sufficient spacing for the GPS map image, we create a widget for it and assign the layout to the widget
        data_widget = QWidget()
        data_widget.setLayout(data_layout)
        data_widget.setMaximumSize(1000,150)

        map_layout.addWidget(data_widget)

        # -------------------------------------------------------------------------
        #
        # add the major subsections to the data view
        #
        # -------------------------------------------------------------------------

        # create a vertical box layout to hold the entire left side of the screen-- informaton layout and the HUD
        left_side_layout = QVBoxLayout()
        # in order to set the maximum height for the informational display, we need to create a new widget for it
        information_widget = QWidget()
        information_widget.setLayout(information_layout)

        left_side_layout.addWidget(information_widget)
        left_side_widget = QWidget()
        left_side_widget.setLayout(left_side_layout)

        # now add the two QVBoxLayouts to the main QHBoxLayout
        main_layout.addWidget(left_side_widget)

        main_layout.addLayout(map_layout)

        # finally, set the layout for the 'self' QWidget to be the data_layout, which contains as sub-layouts all of the items created
        self.setLayout(main_layout)

    def getMapLocations(self):
        """
        This loads the data for the maps in from a .csv configuration file, with the map names, filenames, and coordinates/size info
        """
        # create a blank dictionary to hold the return value
        map_locations = {}

        # open the csv file with a relative filepath
        with open('./maps/locations.csv', newline='') as csvfile:
            # now use python's built in csv module to read the csv file line by line
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                if row[0] != 'Name': #if we aren't on the first line, read in the information
                    # Name, Filename, Lat_1, Lon_1, Lat_2, Lon_2
                    map_locations[row[0]] = (row[1],float(row[2]),float(row[3]),float(row[4]),float(row[5]))
                    self.map_location.addItem(row[0]) # after parsing the data into the dictionary, using the names as keys, add to the QComboBox selector

        #finally, return the location dictionary {name --> filename, lat_1, lon_1, lat_2, lon_2}
        return map_locations
    
    def map_up_pressed(self):
        """
        This function provides functionality for when the up arrow is pressed on the map navigation
        """
        minimum = self.map_zoom_factor*(self.map_dimensions[1]/2)
        self.map_center[1] = max(self.map_center[1] - self.map_dimensions[1]*self.map_zoom_factor*0.1, minimum)

    def map_down_pressed(self):
        """
        This function provides functionality for when the down arrow is pressed on the map navigation
        """
        maximum = (self.map_dimensions[1])-self.map_zoom_factor*(self.map_dimensions[1]/2)
        self.map_center[1] = min(self.map_center[1] + self.map_dimensions[1]*self.map_zoom_factor*0.1, maximum)

    def map_left_pressed(self):
        """
        This function provides functionality for when the left arrow is pressed on the map navigation
        """
        minimum = self.map_zoom_factor*(self.map_dimensions[0]/2)
        self.map_center[0] = max(self.map_center[0] - self.map_dimensions[0]*self.map_zoom_factor*0.1, minimum)

    def map_right_pressed(self):
        """
        This function provides functionality for when the right arrow is pressed on the map navigation
        """
        maximum = (self.map_dimensions[0])-self.map_zoom_factor*(self.map_dimensions[0]/2)
        self.map_center[0] = min(self.map_center[0] + self.map_dimensions[0]*self.map_zoom_factor*0.1, maximum)

    def map_zoom_in_pressed(self):
        """
        This function provides functionality for when the 'zoom in' arrow is pressed on the map navigation
        """
        # modify the zoom value, with a lower limit at 0.1-- decrease by 10 percent
        self.map_zoom_factor = max(self.map_zoom_factor*0.9, 0.1)

    def map_zoom_out_pressed(self):
        """
        This function provides functionality for when the 'zoom out' arrow is pressed on the map navigation
        """
        # modify the zoom value, with an upper limit at 1-- increase by 11 percent
        self.map_zoom_factor = min(self.map_zoom_factor*1.11, 1)

        # calculate the minimum possible value for the 'y' value, and make sure that we adjust the center to match
        x_minimum = self.map_zoom_factor*(self.map_dimensions[0]/2)
        self.map_center[0] = max(self.map_center[0], x_minimum)

        # calculate the maximum possible value for the 'y' value, and make sure that we adjust the center to match
        x_maximum = (self.map_dimensions[0])-self.map_zoom_factor*(self.map_dimensions[0]/2)
        self.map_center[0] = min(self.map_center[0], x_maximum)

        # calculate the minimum possible value for the 'x' value, and make sure that we adjust the center to match
        y_minimum = self.map_zoom_factor*(self.map_dimensions[1]/2)
        self.map_center[1] = max(self.map_center[1], y_minimum)

        # calculate the maximum possible value for the 'x' value, and make sure that we adjust the center to match
        y_maximum = (self.map_dimensions[1])-self.map_zoom_factor*(self.map_dimensions[1]/2)
        self.map_center[1] = min(self.map_center[1], y_maximum)