# import the serial library for using the radio
import serial
from serial.tools import list_ports
# import the sys library for accessing command-line arguments
import sys
# import time for delays
import time

class Vehicle:
    """
    Class which handles the link to the microcontroller transmitting data from the vehicle

    Initiated with the port and baud rate the radio is connected to
    """
    def __init__(self, port, baud):
        # serial port variables
        self.port = port
        self.baud = baud

        self.initialize_port()

        # vehicle data variables
        

    def initialize_port(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            print(f'Connected to serial port {self.ser.name} at {self.ser.baudrate} baud')

            # wait to ensure serial port fully initializes
            time.sleep(2)

        except serial.SerialException as e:
            print(f'Error connecting to serial port: {e}')

    def update(self, debug=False):
        # loop through all of the data which is in the receive buffer
        while self.ser.in_waiting > 0:
            # get one line from the receive buffer and strip unwanted whitespace
            response = self.ser.readline().strip()

            # if selected, print out response to the console
            if debug:
                print(f'Received data: {response}')

    def send_data(self, message):
        # send data through the serial port
        self.ser.write(message)

        print(f'Sent data: {message}')

    def parse_data(self, data):
        return None

    def close_port(self):
        # close the serial port to release it back to the computer
        if self.ser.is_open:
            self.ser.close()

            print("Vehicle serial port closed")

# if this script is called directly, initiate a text-based interface for debugging
if __name__ == "__main__":

    if len(sys.argv) == 3:
        # basically, when calling the file, the user can specify the port and baud rate as command line arguments
        vehicle = Vehicle(port=sys.argv[1], baud=sys.argv[2])
    else:
        # this line gets the available serial ports from the computer
        ports = list_ports.comports()
        
        # print out the available serial ports, to ask the user which one to use
        print("Active COM Ports:")
        for i in range(len(ports)):
            # formatting string, f-strings are cool, read the python documentation
            print(f"{i+1}\t-\t{ports[i]}")
        # get the input from the user, and convert it to an integer (if they don't enter an integer, the entire program crashes, but whatever)
        port_num = int(input("Select target: ")) - 1

        # get the baudrate from the CLI
        baud = int(input('Input baudrate (ex. 57600): '))
        # pass in the required arguments to the link_handler initialization (this is designed for radios using the SiK protocol,
        # like the RFD900x, so defaults to 57600 baud)
        vehicle = Vehicle(port=ports[port_num].device, baud=baud)

    # wrap the read data function in a try block so it can be exited cleanly
    try:
        print("Reading data from serial port:")
        while True:
            vehicle.update(debug=True)

            # wait 1 second before reading data again
            time.sleep(1)

    # make sure to relinquish control over the serial port
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt, exiting program")
        vehicle.close_port()