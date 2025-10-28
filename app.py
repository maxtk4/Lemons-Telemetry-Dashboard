
from pathlib import Path #needed to reference the stylesheet
import os #needed to set the environment variable for usb link

# import necessary classes from Qt modules
from PySide6.QtCore import (
    QTimer,
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QMainWindow,
    QStackedLayout,
)


# import the main view classes
from data import Data

# import the top bar class
from topbar import TopBar

# import the information updater class (contains static methods for updating flight view
from updateinformation import UpdateInformation

# import the custom classes defined in the GCS file, which connect to a vehicle and get data from the vehicle
from connection import Vehicle

class MainWindow(QMainWindow):
    def __init__(self):
        """
        This application is designed as a sequence of widgets and layouts grouping those widgets together into larger and larger layouts
        
        The main sections are:
         - the top bar, which displays information about the ground control station, as well as the interface for connecting
           to vehicles and selecting port/method for connecting
         - the flight view, which displays a GPS map, and relevant telemetry data from the vehicle while in flight. This will also
           contain any necessary buttons/controls for triggering in flight actions
         - the calibration view [WIP] shows servo status and allows the user to change the values
        
        There is also a divider bar between the top bar and bottomview that is generated and included in the largest layout/widget
        """
        super().__init__()

        # this DataHandler __init__() without any parameters generates randomly updating data for testing
        self.vehicle = Vehicle()

        self.setWindowTitle("Rice University 24 Hour of Lemons Pit Telemetry")

        # create a QWidget and QLayout to hold all of the sub-layouts and widgets for the application
        app = QWidget()
        app_layout = QVBoxLayout()
        app_layout.setSpacing(0)
        
        # create a new top bar object, and connect the button for connecting to the connection method belonging to the mainwindow
        # object (this class)
        self.top_bar = TopBar()

        # connect to the connect_to_vehicle method
        self.top_bar.connect_button.clicked.connect(self.connect_to_vehicle)

        # this is a widget designed to split up the UI into top bar and flight view
        divider = QWidget()
        # get the screen dimensions to draw a bar of the correct length across the screen
        width,_ = QApplication.primaryScreen().size().toTuple()
        # set the size and color of the divider widget, doesn't quite reach the edges of the display
        divider.setFixedSize(width-20, 2)
        divider.setStyleSheet("background-color: black")

        app_layout.addWidget(self.top_bar)
        app_layout.addWidget(divider)

        # -------------------------------------------------------------------------
        #
        # Add a data_view to the main app widget's layout
        #
        # -------------------------------------------------------------------------
        
        # create a new flight view, and add it to the app layout
        self.data_view = Data()

        app_layout.addLayout(self.data_view)

        # -------------------------------------------------------------------------
        #
        # set the main app widget to have the layout defined above, and then set the central
        # widget of the window to be the app widget
        #
        # -------------------------------------------------------------------------
        app.setLayout(app_layout)
        self.setCentralWidget(app)

        # -------------------------------------------------------------------------
        #
        # define two timers-- one to get data and update the textual information in the gui,
        # one to redraw the map
        #  + the map is only redrawn at 5Hz instead of 20 to improve performance
        #
        # -------------------------------------------------------------------------
        self.update_timer = QTimer()
        self.update_timer.setInterval(50)
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start()

    def update(self):
        # update the data_source with whatever messages have been sent since last time this method was called
        self.vehicle.update()

        # call the static function for updating the top bar, since this is always visible
        UpdateInformation.updateTopBar(self.vehicle, self.top_bar)

        # call the static methods for updating the textual information in the flight view and top bar
        UpdateInformation.updateFlightView(self.vehicle, self.data_view)

        # call the static method defined to update the map, with the data source being the data source belonging to this instance
        # of the MainWindow object, and the target being the flight view also belonging to this MainWindow
        UpdateInformation.updateMap(self.vehicle, self.data_view, self.data_view.map_center, self.data_view.map_zoom_factor)
    
    def connect_to_vehicle(self):
        # -------------------------------------------------------------------------
        #
        # something to get a new connection when the connect button is pressed
        #   - get the state of the port and baud settings
        #   - set the vehicle object
        #   - set the data handler object as well
        #
        # -------------------------------------------------------------------------
        print("Attempting to Connect")
        try:
            if self.top_bar.baud.isChecked():
                baud = 57600
            else:
                baud = 115200
                print('Using USB Cable')

            # create a new vehicle to replace the dummy one currently stored by the MainWindow
            self.vehicle = Vehicle(port=str(self.top_bar.port.currentText()), baud=baud)

            self.data_view.vehicle = self.vehicle

            # change the state of the connection button to reflec tthe vehicle has been connected
            self.top_bar.connect_button.setText("Connected")
            self.top_bar.connect_button.setDisabled(True)

        except Exception as error:
            print("Failed to Connect")
            print("Error: ")
            print(error)


if __name__ == "__main__":
    app = QApplication()
    
    app.setStyleSheet(Path('app.qss').read_text())

    window = MainWindow()
    window.show()
    app.exec()