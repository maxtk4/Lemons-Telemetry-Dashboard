from collections import deque

from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg


class StreamingLineChart(QWidget):
    """
    Two-stream live plot with:
    - Stationary time axis (0 at right)
    - Independent Y axes
    - Independent data stream updates
    - Color-matched axes and curves
    """

    def __init__(
        self,
        window_seconds=30,
        label1="Value 1",
        label2="Value 2",
        color1='k',
        color2='r',
        parent=None
    ):
        super().__init__(parent)

        self.window_seconds = window_seconds
        self.t0 = None

        self.data1 = deque()
        self.data2 = deque()

        # --- Plot setup ---
        self.plot_widget = pg.PlotWidget()
        self.plot_item = self.plot_widget.getPlotItem()
        self.plot_widget.setBackground('w')

        # Pens
        self.pen1 = pg.mkPen(color=color1, width=2)
        self.pen2 = pg.mkPen(color=color2, width=2)

        # --- LEFT AXIS (Stream 1) ---
        self.curve1 = self.plot_item.plot(pen=self.pen1)
        self.plot_item.setLabel("left", label1, color=color1)

        left_axis = self.plot_item.getAxis('left')
        left_axis.setPen(self.pen1)
        left_axis.setTextPen(self.pen1)

        # --- RIGHT AXIS (Stream 2) ---
        self.plot_item.showAxis('right')
        self.plot_item.setLabel('right', label2, color=color2)

        right_axis = self.plot_item.getAxis('right')
        right_axis.setPen(self.pen2)
        right_axis.setTextPen(self.pen2)

        self.vb2 = pg.ViewBox()
        self.plot_item.scene().addItem(self.vb2)
        right_axis.linkToView(self.vb2)

        self.vb2.setXLink(self.plot_item)

        self.curve2 = pg.PlotCurveItem(pen=self.pen2)
        self.vb2.addItem(self.curve2)

        # Sync views
        self.plot_item.vb.sigResized.connect(self._update_views)

        # Bottom axis
        self.plot_widget.setLabel("bottom", "Time (relative)", "s")
        self.plot_widget.setXRange(-window_seconds, 0, padding=0)

        self.plot_widget.getPlotItem().layout.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

    def _update_views(self):
        self.vb2.setGeometry(self.plot_item.vb.sceneBoundingRect())
        self.vb2.linkedViewChanged(self.plot_item.vb, self.vb2.XAxis)

    # -----------------------------
    # Data input methods
    # -----------------------------
    def add_point_stream1(self, timestamp: float, value: float):
        self._add_point(timestamp, value, stream=1)

    def add_point_stream2(self, timestamp: float, value: float):
        self._add_point(timestamp, value, stream=2)

    def add_point(self, timestamp: float, value1: float, value2: float):
        """Optional convenience method"""
        self.add_point_stream1(timestamp, value1)
        self.add_point_stream2(timestamp, value2)

    def _add_point(self, timestamp, value, stream):
        if self.t0 is None:
            self.t0 = timestamp

        t_rel = timestamp - self.t0
        cutoff = t_rel - self.window_seconds

        if stream == 1:
            self.data1.append((t_rel, value))
            while self.data1 and self.data1[0][0] < cutoff:
                self.data1.popleft()

        elif stream == 2:
            self.data2.append((t_rel, value))
            while self.data2 and self.data2[0][0] < cutoff:
                self.data2.popleft()

        self._update_plot(t_rel)

    # -----------------------------
    # Plot update
    # -----------------------------
    def _update_plot(self, current_time):

        # Shared X axis uses whichever stream has data
        base_data = self.data1 if self.data1 else self.data2
        if not base_data:
            return

        x = [t - current_time for t, _ in base_data]

        # --- Stream 1 ---
        if self.data1:
            y1 = [v for _, v in self.data1]
            self.curve1.setData(x[:len(y1)], y1)

            ymin, ymax = min(y1), max(y1)
            if ymin == ymax:
                ymin -= 0.5
                ymax += 0.5
            self.plot_item.vb.setYRange(ymin - 1, ymax + 1, padding=0)

        # --- Stream 2 ---
        if self.data2:
            y2 = [v for _, v in self.data2]
            self.curve2.setData(x[:len(y2)], y2)

            ymin2, ymax2 = min(y2), max(y2)
            if ymin2 == ymax2:
                ymin2 -= 0.5
                ymax2 += 0.5
            self.vb2.setYRange(ymin2 - 1, ymax2 + 1, padding=0)

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
        t = time.time()

        temp = 20 + random.uniform(-1, 1)
        pressure = 100 + random.uniform(-10, 10)

        chart.add_point_stream1(t, temp)
        chart.add_point_stream2(t, pressure)


    timer = QTimer()
    timer.timeout.connect(generate_data)

    timer.start(20)  # 50 Hz

    sys.exit(app.exec())