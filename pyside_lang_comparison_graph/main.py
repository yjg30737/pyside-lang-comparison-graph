import subprocess
import operator
import math
import re

from PySide6.QtCharts import QChartView, QChart, QBarSeries, QBarCategoryAxis, QBarSet, QValueAxis
from PySide6.QtGui import QPainter, QRegularExpressionValidator
from PySide6.QtWidgets import QMainWindow, QHBoxLayout, QLabel, QLineEdit, QSpacerItem, QSizePolicy, QPushButton, \
    QVBoxLayout, QWidget, QApplication


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__initUi()

    def __initUi(self):
        self.__timesLineEdit = QLineEdit()
        self.__timesLineEdit.setText('10000000')
        v = QRegularExpressionValidator()
        v.setRegularExpression('[0-9]*')
        self.__timesLineEdit.setValidator(v)
        btn = QPushButton('Run Test')
        btn.clicked.connect(self.__run)

        lay = QHBoxLayout()
        lay.addWidget(QLabel('Times'))
        lay.addWidget(self.__timesLineEdit)
        lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.MinimumExpanding))
        lay.addWidget(btn)
        lay.setContentsMargins(0, 0, 0, 0)

        topWidget = QWidget()
        topWidget.setLayout(lay)

        self.__series = QBarSeries()
        self.__series.append(QBarSet('Time'))

        self.__axisX = QBarCategoryAxis()

        self.__axisY = QValueAxis()

        self.__chart = QChart()
        self.__chart.addSeries(self.__series)

        self.__chart.setAxisX(self.__axisX)
        self.__chart.setAxisY(self.__axisY)

        self.__series.attachAxis(self.__axisX)
        self.__series.attachAxis(self.__axisY)

        chartView = QChartView()
        chartView.setRenderHints(QPainter.Antialiasing)
        chartView.setChart(self.__chart)

        lay = QVBoxLayout()
        lay.addWidget(topWidget)
        lay.addWidget(chartView)

        mainWidget = QWidget()
        mainWidget.setLayout(lay)

        self.setCentralWidget(mainWidget)

    def __run(self):
        n = self.__timesLineEdit.text()
        p = subprocess.run(['a.bat', str(n)], capture_output=True, text=True)

        fs = re.findall(r'([\w]+):\s([\d\\.]+)\sseconds', p.stdout)
        lst = []
        for f in fs:
            k, v = f
            lst.append([k, v])
        lst = sorted(lst, key=operator.itemgetter(1))
        barSet = self.__series.barSets()[0]
        barSet.remove(0, 5)
        self.__axisX.clear()
        self.__axisX.append([item[0] for item in lst])
        self.__axisY.setRange(0, max([math.ceil(float(item[1])) for item in lst]))
        for item in lst:
            barSet <<= float(item[1])

        self.__axisX.setTitleText('Language')
        self.__axisY.setTitleText('Seconds')


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


