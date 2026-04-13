# import the serial library for using the radio
import serial
from serial.tools import list_ports
# import the sys library for accessing command-line arguments
import sys
# import time for delays
import time
# used for logging information
import csv
from pathlib import Path

# rolling list of length 240 items for GPS location tracking
from collections import deque

# for unpacking bytes to floats
import struct

def sublist(main_list, sublist):
    # Convert to string representation
    main_str = ','.join(map(str, main_list))
    sub_str = ','.join(map(str, sublist))

    return main_str.find(sub_str)


class Vehicle:
    """
    Class which handles the link to the microcontroller transmitting data from the vehicle

    Initiated with the port and baud rate the radio is connected to
    """

    def __init__(self, port=None, baud=None):
        # serial port variables
        self.port = port
        self.baud = baud

        self.initialized = False if self.port == None else True

        if self.initialized:
            self.initialize_port()

        self.rx_buffer = bytearray()

        current_time = time.time()
        self.log_folder = f"./logs/{current_time}"
        
        # Create a folder to hold the log files for this particular vehicle class
        Path(self.log_folder).mkdir(parents=True, exist_ok=True)

        with open(self.log_folder +"/imu.csv", 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Time','X dot','Y dot','Z dot','Omega X', 'Omega Y', 'Omega Z', 'Temperature'])
        with open(self.log_folder +"/gps.csv", 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Time','Lat','Lon','Heading','Altitude', 'Speed', 'Satellites', 'HDOP'])
        with open(self.log_folder +"/car.csv", 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Time','Speed','Engine RPM','Tire Pressure','Coolant Temperature','Battery Voltage','Fuel Gauge', 'Oil Pressure'])

        # vehicle data variables
        
        # Interrupt driven values
        # self.mph = 0.0
        self.rpm = 0.0
        # ADC specific values
        self.car_time = current_time
        self.coolant_temperature = 0.0
        self.battery_voltage = 0.0
        self.fuel_gauge = 0.0
        self.oil_pressure = 0.0

        # IMU data variables
        self.imu_time = current_time
        self.accel = [0.0,0.0,0.0]
        self.gyro = [0.0,0.0,0.0]
        self.magnetometer = [0.0,0.0,0.0]

        # GPS related variables
        self.gps_time = current_time
        self.hdg = 0.0
        self.lat = 0.0
        self.lon = 0.0
        self.hdop = 100
        self.gps_speed = 0.0
        self.gps_altitude = 0.0
        self.num_satellites = 0

        self.last_heartbeat = current_time
        self.heartbeat_time = 0
        self.electronics_temperature = 0.0

        # Driver Input Sensors
        self.driver_time = current_time
        self.steering_angle = 0.0
        self.throttle = 0.0
        self.brake = 0.0

        self.location_history = deque(maxlen=240)


    def initialize_port(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            print(f'Connected to serial port {self.ser.name} at {self.ser.baudrate} baud')

            # wait to ensure serial port fully initializes
            time.sleep(2)

        except serial.SerialException as e:
            print(f'Error connecting to serial port: {e}')

    def process_serial_data(self):
        """
        Reads all available bytes from the serial port (self.ser) and processes
        them to find complete messages.
        
        Returns:
            list: A list of complete messages (as bytes objects) found in this cycle.
        """
        # Create a list to hold messages found in this single run
        messages_found = []

        # Read all available data from the serial port
        try:
            # Check how many bytes are waiting
            waiting = self.ser.in_waiting
            if waiting > 0:
                # Read all waiting bytes and add them to our persistent buffer
                new_bytes = self.ser.read(waiting)
                self.rx_buffer.extend(new_bytes)
        
        except serial.SerialException as e:
            print(f"Serial read error: {e}")
            # Handle the error appropriately, e.g., close/reopen port
            return [] # Return empty list on error
        except Exception as e:
            # Handle other potential errors, e.g., port not open
            print(f"Error: {e}")
            return []

        # Process the buffer to find complete messages
        while True:
            # Find the first occurrence of our start byte
            start_index = self.rx_buffer.find(0xFE)
            
            if start_index == -1:
                # No start byte found. The buffer contains only partial/garbage data. We'll stop processing and wait for more data to arrive.
                break 

            # If we found a start byte, discard any data before it
            if start_index > 0:
                print(f"Discarding {start_index} bytes of garbage: {self.rx_buffer[:start_index].hex()}")
                self.rx_buffer = self.rx_buffer[start_index:]
            
            # Now, self.rx_buffer[0] == 0xFE. Check if we have the length byte.
            if len(self.rx_buffer) < 2:
                # We have the start byte, but not the length byte yet. Stop processing and wait for more data.
                break

            # We have the start byte (1) and length byte (1). This assumes the 2nd byte is the *payload* length.
            payload_len = self.rx_buffer[1]
            
            # Calculate the total length of the messag Total Length = Start Byte (1) + Length Byte (1) + Payload (payload_len)
            total_message_len = payload_len
            
            # Check if the *entire* message has arrived in our buffer
            if len(self.rx_buffer) < total_message_len:
                # We have the header, but not the full payload yet. Stop processing and wait for the rest of the message.
                break

            # If we're here, we have a full, complete message!
            
            # Extract the message (as a new bytes object)
            message = bytes(self.rx_buffer[0:total_message_len])
            messages_found.append(message)
            
            # Remove this processed message from the buffer
            self.rx_buffer = self.rx_buffer[total_message_len:]
            
            # Loop again immediately to see if another complete message is already in the buffer.
        
        return messages_found

    def process_message(self, msg):
        # First, the checksum
        if (msg[-2] != 0xAB or msg[-1] != 0xCD):
            print(f"Checksum failed, message: {msg}")
            return False
        

        if msg[2] == 0x01:
            # We have a new heartbeat message
            self.last_heartbeat = time.time()
            print('Heartbeat Received')
        elif msg[2] == 0x02:
            self.gps_time = time.time()
            # GPS Data
            print('GPS Data Received')
            self.lat = struct.unpack('<d', bytes(msg[3:11]))[0]
            self.lon = struct.unpack('<d', bytes(msg[11:19]))[0]
            self.gps_speed = struct.unpack('<d', bytes(msg[19:27]))[0]
            self.hdg = struct.unpack('<d', bytes(msg[27:35]))[0]
            self.gps_altitude = struct.unpack('<d', bytes(msg[35:43]))[0]
            self.num_satellites = int.from_bytes(bytes(msg[43:47]), 'little') # uint32_t is little endian on ESP32
            self.hdop = struct.unpack('<d', bytes(msg[47:55]))[0]

            with open(self.log_folder +"/gps.csv", 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows([self.gps_time,
                                  self.lat,
                                  self.lon,
                                  self.hdg,
                                  self.gps_altitude,
                                  self.gps_speed,
                                  self.num_satellites,
                                  self.hdop])
                
            self.location_history.append([self.lat,self.lon]) # O(1) time complexity for adding new items and removing old ones

        elif msg[2] == 0x03:
            print('IMU Data Received')
            # IMU Data
            self.imu_time = time.time()

            # Temperature bytes (float)
            self.electronics_temperature = struct.unpack('<f', bytes(msg[3:7]))[0]

            # Acceleration bytes (three floats)
            self.accel = [struct.unpack('<f', bytes(msg[7:11]))[0],
                            struct.unpack('<f', bytes(msg[11:15]))[0],
                            struct.unpack('<f', bytes(msg[15:19]))[0]]
            
            # Gyroscope bytes (three floats)
            self.gyro = [struct.unpack('<f', bytes(msg[19:23]))[0],
                            struct.unpack('<f', bytes(msg[23:27]))[0],
                            struct.unpack('<f', bytes(msg[27:31]))[0]]
            
            with open(self.log_folder +"/imu.csv", 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows([self.imu_time,
                                  self.accel[0],
                                  self.accel[1],
                                  self.accel[2],
                                  self.gyro[0],
                                  self.gyro[1],
                                  self.gyro[2],
                                  self.electronics_temperature])
        
        elif msg[2] == 0x04:
            print('Pressure Data Received')
            # Pressure Data

            # # Temperature bytes (float)
            # self.dps310_temperature = struct.unpack('<f', bytes(msg[3:7]))[0]
            # # Pressure bytes (float)
            # self.ambient_pressure = struct.unpack('<f', bytes(msg[7:11]))[0]
        elif msg[2] == 0x05:
            print('Car Data Received')

            self.battery_voltage = int.from_bytes(bytes(msg[3:5]), 'little')
            self.fuel_gauge = int.from_bytes(bytes(msg[5:7]), 'little')
            self.oil_pressure = int.from_bytes(bytes(msg[7:9]), 'little')
            self.coolant_temperature = int.from_bytes(bytes(msg[9:11]), 'little')

            self.rpm = 60000000/struct.unpack('<f', bytes(msg[11:15]))[0] # data arrives as period measured in us
            # self.mph = struct.unpack('<f', bytes(msg[15:19]))[0]/1000000 * 1.12 # convert to pulses per second, then scale from 2/(m/s) to get mph

            self.car_time = time.time()

            
        return True

    def update(self, debug=False):
        # get tenth of a second precision on heartbeat times
        self.heartbeat_time = round((time.time() - self.last_heartbeat)*100)/100
        # print(f"Heartbeat Time: {self.heartbeat_time}; Time: {time.time()}")

        if self.initialized:
            # loop through all of the data which is in the receive buffer
            # Process serial data and get any new messages
            new_messages = self.process_serial_data()
            
            if new_messages:
                for msg in new_messages:
                    # Process each message
                    print(f"  > Processing message: {msg.hex()}")
                    self.process_message(msg)
        else:
            return None

    def send_data(self, message):
        # send data through the serial port
        self.ser.write(message)

        print(f'Sent data: {message}')

    def parse_data(self, data):
        return None

    def close_port(self):
        # close the serial port to release it back to the computer
        if self.ser and self.ser.is_open:
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

    # make sure to relinquish control over the serial port
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt, exiting program")
        vehicle.close_port()