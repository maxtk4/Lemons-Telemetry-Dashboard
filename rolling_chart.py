from collections import deque

from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg


class StreamingLineChart(QWidget):
    """
    Live plot with stationary x-axis where 0 seconds is always at the right edge.
    Displays last `window_seconds` of data.
    """

    def __init__(self, window_seconds=30, data_label="Value", scale=11, parent=None):
        super().__init__(parent)

        self.window_seconds = window_seconds
        self.t0 = None
        self.data = deque()

        # pyqtgraph setup
        self.plot_widget = pg.PlotWidget()
        self.curve = self.plot_widget.plot()

        self.plot_widget.setLabel("bottom", "Time (relative)", "s")
        self.plot_widget.setLabel("left", data_label)

        self.plot_widget.showGrid(x=True, y=True)

        # color changes
        self.plot_widget.setBackground('w')

        black_pen = pg.mkPen(color='k')
        self.curve = self.plot_widget.plot(pen=black_pen)

        label_styles = {'color': 'black', 'font-size': '10pt'}
        self.plot_widget.setLabel("bottom", "Time (relative)", "s", **label_styles)
        self.plot_widget.setLabel("left", data_label, **label_styles)

        for axis_name in ['bottom', 'left']:
            axis = self.plot_widget.getAxis(axis_name)
            axis.setPen(black_pen)       # Colors the axis line and ticks
            axis.setTextPen(black_pen)   # Colors the numbers/text on the ticks

        self.plot_widget.showGrid(x=False, y=False)

        # fixed ranges
        self.plot_widget.setXRange(-window_seconds, 0, padding=0)
        
        self.plot_widget.getPlotItem().layout.setContentsMargins(0, 0, 0, 0)
    
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)


    def add_point(self, timestamp: float, value: float):
        """
        timestamp : absolute time (e.g. time.time())
        value     : measurement
        """

        if self.t0 is None:
            self.t0 = timestamp

        t_rel = timestamp - self.t0

        self.data.append((t_rel, value))

        cutoff = t_rel - self.window_seconds
        while self.data and self.data[0][0] < cutoff:
            self.data.popleft()

        self._update_plot(t_rel)


    def _update_plot(self, current_time):

        if not self.data:
            return

        # convert times so "now" is always 0
        x = [t - current_time for t, _ in self.data]
        y = [v for _, v in self.data]

        self.curve.setData(x, y)

        # y autoscale
        ymin = min(y)
        ymax = max(y)

        if ymin == ymax:
            ymin -= 0.5
            ymax += 0.5

        self.plot_widget.setYRange(
            ymin - 1,
            ymax + 1,
            padding=0
        )

if __name__ == "__main__":
    import sys
    import time
    import random

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer


    app = QApplication(sys.argv)

    chart = StreamingLineChart(window_seconds=30)
    chart.resize(600, 300)
    chart.show()


    def generate_data():

        timestamp = time.time()

        value = (
            0.8 * random.uniform(-1, 1)
            + 0.2 * random.random()
        )

        chart.add_point(timestamp, value)


    timer = QTimer()
    timer.timeout.connect(generate_data)

    timer.start(20)  # 50 Hz

    sys.exit(app.exec())