# to get the list of available COM ports to connect to
from serial.tools import list_ports

# import necessary tools from Qt
from PySide6.QtGui import (
    QPixmap,
)
from PySide6.QtWidgets import (
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QComboBox,
    QPushButton,
    QRadioButton,
)

class TopBar(QWidget):
    def __init__(self):
        # call the parent class's constructor to set up all of the things necessary for a QWidget (provided by Qt)
        super().__init__()

        # define a horizontal box layout to contain all of the items in the top bar
        layout = QHBoxLayout()

        # create a QLabel() and then populate it with a QPixmap contianing the logo
        logo_widget = QLabel()
        logo = QPixmap()
        logo.load('./images/RiceLogo-500pxWide.jpg')
        logo_widget.setPixmap(logo) #this image is already saved at the correct size, so it doesn't need to be scaled, which would lose quality
        layout.addWidget(logo_widget)

        # create a verticle box layout for the title acronym and the title below the acronym
        title_layout = QVBoxLayout()
        title = QLabel("Lemons@Rice")
        title.setObjectName("title") #set the object name so the QSS style sheet can apply to make the text large
        subtitle = QLabel("Pit Lane Telemetry Monitor for Rice University 24 Hours of Lemons Car 2025-2026")
        subtitle.setObjectName("small") #set the object name so it can be made smaller
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        # add the small verticle box layout to the main horizontal box layout
        layout.addLayout(title_layout)

        # create a QGridLayout to hold the four relevant items for the connection interface
        connection_layout = QGridLayout()

        # this combobox reads all of the port options to provide them as options to the user
        self.port = QComboBox()
        # create a radio button to toggle between the two relevant baud rates, for telemetry radio and for USB cable
        self.baud = QRadioButton("USB COM port - 115200 Baud")
        # connect the baud radio button to the method that changes the text for it, as well as the method to update the list of ports
        self.baud.clicked.connect(self.change_baud)
        self.baud.clicked.connect(self.get_ports)

        self.connect_button = QPushButton("Connect")
        self.connect_button.setCheckable(True)

        self.heartbeat_time = QLabel("Heartbeat Time: 0ms")
        self.heartbeat_time.setObjectName("small")
        
        connection_layout.addWidget(self.port,0,0)
        connection_layout.addWidget(self.baud,1,0)
        connection_layout.addWidget(self.connect_button,0,2)
        connection_layout.addWidget(self.heartbeat_time,1,2)

        # add the grid layout to the main horizontal layout
        layout.addLayout(connection_layout)

        self.setLayout(layout)
        self.setMaximumHeight(100)

    def get_ports(self):
        """
        Method to update the list of ports in the comports drop down-- gets all of the ports using a provided python method
        """
        # get a list of all the ports available on the computer
        ports = list_ports.comports()

        # clear all of the currently listed ports so we don't double list them
        self.port.clear()
        # iterate through the new list of ports and add them as items to the dropdown QComboBox
        for port in ports:
            self.port.addItem(str(port.device))
    
    def change_baud(self):
        """
        Toggles the baud between that for USB and for telemetry connections, based on whether the radiobutton is checked or not
        """
        self.baud.setText("Telemetry Radio - 57600 Baud" if self.baud.isChecked() else "USB COM port - 115200 Baud")