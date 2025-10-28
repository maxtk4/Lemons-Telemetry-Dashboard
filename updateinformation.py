
import math # need this to do trigonometry

from PySide6.QtGui import (
    QPixmap,
    QPainter,
    QPen,
    QColor,
    QFont,
)
from PySide6.QtCore import (
    QPoint,
    QRect,
    QLine,
)


class UpdateInformation():
    @staticmethod
    def updateFlightView(data_source, target):
        """
        Main method for updating the flight view with information-- calls the update HUD method, and edits all the text-based
        information in the flight view
        """

        # go through all of the different text information displays, and get data from the data_source before formatting it into the display
        target.mph.setText('{:.1f}'.format(data_source.mph))
        target.rpm.setText('{:.1f}'.format(data_source.rpm))
        target.hdg.setText('{:.1f} degrees'.format(data_source.hdg))
        target.lat.setText('{:.5f}'.format(data_source.lat)) #latitude and longitutde are kind of irrelevant for text display, but they might be useful
        target.lon.setText('{:.5f}'.format(data_source.lon))

        # -------------------------------------------------------------------------
        #
        # change the gps status value and the GPS tooltip
        #
        # -------------------------------------------------------------------------

        # MAVLink reports GPS status as an integer mapping, so this dictionary and string formatting decodes this for the user
        gps_fix_type = {0: 'No GPS', 1: 'No Fix', 2: '2D Fix', 3: '3D Fix'}
        target.gps_status.setText(f'{gps_fix_type[data_source.gps_fix_type]}')

    @staticmethod
    def updateTopBar(data_source, target):
        """
        This method updates the information on the top bar, specifically the connection button

        If the heartbeat frequency drops too low, indicating that we have lost connection with the vehicle, it re-enables the button
         + this is to ensure that the UI doesn't get stuck in a connection that isn't working, however, it doesn't automatically terminate
           the connection, in case the user wants to wait and see if the current connection will resume working
        """
        # get the time since the last heartbeat from the data_source, this is already calculated and updated when the data source's
        # .update() method is called by updateFlightView
        time = data_source.heartbeat_time

        # access the QLabel displaying the heartbeat frequency, and modify the text to display the actual value
        target.heartbeat_time.setText('Heartbeat Time: {:.2f}'.format(time))

        # if the time since the last heartbeat is too high, the system reenables the 'connect' button
        if time > 3:
            target.connect_button.setText("Connect")
            target.connect_button.setDisabled(False)

    @staticmethod
    def updateMap(data_source, target, center = [500,400], zoom_factor = 0.5):
        """
        maps must have an aspect ratio of 8:5

        center = (x, y) defined on a width of 1000 by height of 625
        
        """
        # -------------------------------------------------------------------------
        #
        # get the map we are using from the QComboBox self.map_location
        #  - data_source, map_center_lat, map_center_lon, width, height
        #
        # -------------------------------------------------------------------------
        location = str(target.map_location.currentText())
        filename,map_top_lat,map_left_lon,map_bottom_lat,map_right_lon = target.map_locations_dict[location]

        # -------------------------------------------------------------------------
        #
        # Create a QPixmap and load in the image information
        #
        # -------------------------------------------------------------------------
        gps_map_data = QPixmap()
        gps_map_data.load("./maps/"+filename)
        # get the original size of the image used for the GPS map
        width = gps_map_data.width()
        height = gps_map_data.height()

        target_width, target_height = target.map_dimensions

        # create a rectangle bounding box of the 'zoomed in' location on the image
        crop_rect = QRect(int(center[0]*(width/target_width)-zoom_factor*(width/2)),
                          int(center[1]*(height/target_height)-zoom_factor*(height/2)),
                          int(zoom_factor*width), int(zoom_factor*height))
        # use to bounding box to crop into the image, and then scale to the correct width (and height) of 1000 (and 800)
        gps_map_data = gps_map_data.copy(crop_rect).scaledToWidth(1000)
        
        if data_source is not None:
            # find the coordinates of the top left corner on a 1000 (height) x 625 (width) scale
            top_y = center[1] - (target_height//2)*zoom_factor
            left_x = center[0] - (target_width//2)*zoom_factor

            # load the history of the location
            hist = data_source.location_history

            # prepare the QPainter object to draw on the map
            painter = QPainter(gps_map_data)
            # the QPen is necessary to set the parameters of the shapes drawn using the QPainter
            pen = QPen()
            pen.setWidth(2)
            pen.setColor(QColor(0,0,0)) # set it to draw the flight history in black
            painter.setPen(pen)

            for i in range(len(hist)):
                # check if there is a point after this one
                if i < len(hist)-1:
                    # get the latitude and longitude of the current point
                    lat_1 = hist[i][0]
                    lon_1 = hist[i][1]
                    # transform GPS coordinates to match up with the map
                    y_1 = (lat_1-map_top_lat)*(target_height/(map_bottom_lat-map_top_lat))
                    x_1 = (lon_1-map_left_lon)*(target_width/(map_right_lon-map_left_lon))  

                    # now we have coordinates from 0-625 and 0-1000 corresponding to the un-zoomed map (as floats)
                    # get the difference between these coordinates and the top left corner of the zoomed in rectangle
                    # then scale by 1/zoom_factor
                    y_1 = (y_1 - top_y)/zoom_factor
                    x_1 = (x_1 - left_x)/zoom_factor

                    # get the latitude and longitude of the next point
                    lat_2 = hist[i+1][0]
                    lon_2 = hist[i+1][1]
                    # transform the latitude and longitude to useful coordinates on the pixmap
                    y_2 = (lat_2-map_top_lat)*(target_height/(map_bottom_lat-map_top_lat))
                    x_2 = (lon_2-map_left_lon)*(target_width/(map_right_lon-map_left_lon))

                    # now we have coordinates from 0-625 and 0-1000 corresponding to the un-zoomed map (as floats)
                    # get the difference between these coordinates and the top left corner of the zoomed in rectangle
                    # then scale by 1/zoom_factor
                    y_2 = (y_2 - top_y)/zoom_factor
                    x_2 = (x_2 - left_x)/zoom_factor

                    # -------------------------------------------------------------------------
                    #
                    # Draw the lines using a QPainter created earlier in the method
                    #
                    # -------------------------------------------------------------------------
                    painter.drawLine(x_1, y_1, x_2, y_2)

            # -------------------------------------------------------------------------
            #
            # Draw a circle with an arrow to represent the current plane heading
            #
            # -------------------------------------------------------------------------

            # Draw thicker black background for white compass logo
            pen.setColor(QColor(0,0,0))
            pen.setWidth(8)
            # we need to assign the pen object to the painter again to actually change the color
            painter.setPen(pen)

            painter.drawEllipse(10, 10, 80, 80)
            
            # using the heading, calculate the location of each end of the compass's line
            # convert the heading to radians, since math.sin and math.cos are in radians
            hdg = (data_source.hdg+90)*(math.pi/180)
            tip = QPoint(50+35*math.cos(hdg), 50-35*math.sin(hdg))
            tail = QPoint(50-35*math.cos(hdg), 50+35*math.sin(hdg))

            # the drawLine method takes two points, the ones just created, and draws a line between them with properties defined by the pen
            painter.drawLine(tip, tail)

            # now draw the arrow point
            left = QPoint(50+20*math.cos(hdg)-5*math.sin(hdg), 50-20*math.sin(hdg)-5*math.cos(hdg))
            right = QPoint(50+20*math.cos(hdg)+5*math.sin(hdg), 50-20*math.sin(hdg)+5*math.cos(hdg))
            # after calculating the location of the end of each line in the arrow point, we can use those and the tip to draw the lines
            painter.drawLine(tip, left)
            painter.drawLine(tip, right)

            # this is to add some decoration to the circle in each cardinal direction
            painter.drawLine(QPoint(50,95), QPoint(50,85))
            painter.drawLine(QPoint(95,50), QPoint(85,50))
            painter.drawLine(QPoint(5,50), QPoint(15,50))
            # draw the last line
            painter.drawLine(QPoint(50,5), QPoint(50,15))

            # Draw white symbol
            pen.setColor(QColor(255,255,255))
            pen.setWidth(2.5)
            # we need to assign the pen object to the painter again to actually change the color
            painter.setPen(pen)

            painter.drawEllipse(10, 10, 80, 80)
            
            # using the heading, calculate the location of each end of the compass's line
            # convert the heading to radians, since math.sin and math.cos are in radians
            hdg = (data_source.hdg+90)*(math.pi/180)
            tip = QPoint(50+35*math.cos(hdg), 50-35*math.sin(hdg))
            tail = QPoint(50-35*math.cos(hdg), 50+35*math.sin(hdg))

            # the drawLine method takes two points, the ones just created, and draws a line between them with properties defined by the pen
            painter.drawLine(tip, tail)

            # now draw the arrow point
            left = QPoint(50+20*math.cos(hdg)-5*math.sin(hdg), 50-20*math.sin(hdg)-5*math.cos(hdg))
            right = QPoint(50+20*math.cos(hdg)+5*math.sin(hdg), 50-20*math.sin(hdg)+5*math.cos(hdg))
            # after calculating the location of the end of each line in the arrow point, we can use those and the tip to draw the lines
            painter.drawLine(tip, left)
            painter.drawLine(tip, right)

            # this is to add some decoration to the circle in each cardinal direction
            painter.drawLine(QPoint(50,95), QPoint(50,85))
            painter.drawLine(QPoint(95,50), QPoint(85,50))
            painter.drawLine(QPoint(5,50), QPoint(15,50))
            # change the color to red to indicate this direction is north
            pen.setColor(QColor(150,0,0))
            painter.setPen(pen)
            # draw the last line
            painter.drawLine(QPoint(50,5), QPoint(50,15))

            # make sure to close the painter at the end of each time this method is called, or Qt errors because there are
            # too many painters active at once
            painter.end()

        # once the map has been constructed and the information is drawn on it, set the gps_map label to have this pixmap
        target.gps_map.setPixmap(gps_map_data)