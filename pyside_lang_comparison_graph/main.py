import copy
import subprocess
import operator
import math
import re


from PySide6.QtCharts import QChartView, QChart, QBarSeries, QBarCategoryAxis, QBarSet, QValueAxis
from PySide6.QtCore import QThread
from PySide6.QtGui import QPainter, QRegularExpressionValidator, Qt, QPdfWriter, QPixmap
from PySide6.QtWidgets import QMainWindow, QHBoxLayout, QLabel, QLineEdit, QSpacerItem, QSizePolicy, QPushButton, \
    QVBoxLayout, QWidget, QApplication, QFileDialog


class Thread(QThread):
    def __init__(self, arg, res_lst: list):
        super().__init__()
        self.__arg = arg
        self.__res_lst = res_lst
        self.__res_lst.clear()

    def run(self):
        p = subprocess.run(self.__arg, capture_output=True, text=True)
        self.__res_lst.append(p.stdout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__res_lst = []
        self.__initUi()

    def __initUi(self):
        self.setWindowTitle('Language Comparison')

        self.__timesLineEdit = QLineEdit()
        self.__timesLineEdit.setText('10000000')
        v = QRegularExpressionValidator()
        v.setRegularExpression('[0-9]*')
        self.__timesLineEdit.setValidator(v)
        runTestBtn = QPushButton('Run Test')
        runTestBtn.clicked.connect(self.__run)
        saveBtn = QPushButton('Save')
        saveBtn.clicked.connect(self.__save)

        lay = QHBoxLayout()
        lay.addWidget(QLabel('Times'))
        lay.addWidget(self.__timesLineEdit)
        lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.MinimumExpanding))
        lay.addWidget(runTestBtn)
        lay.addWidget(saveBtn)
        lay.setContentsMargins(0, 0, 0, 0)

        topWidget = QWidget()
        topWidget.setLayout(lay)

        self.__series = QBarSeries()
        barset = QBarSet('Time')
        self.__series.append(barset)

        self.__axisX = QBarCategoryAxis()

        self.__axisY = QValueAxis()

        self.__chart = QChart()
        self.__chart.addSeries(self.__series)

        self.__chart.setAxisX(self.__axisX)
        self.__chart.setAxisY(self.__axisY)

        self.__series.attachAxis(self.__axisX)
        self.__series.attachAxis(self.__axisY)

        self.__chartView = QChartView()
        self.__chartView.setRenderHints(QPainter.Antialiasing)
        self.__chartView.setChart(self.__chart)

        self.__loadingLbl = QLabel('Loading...')
        self.__loadingLbl.setAlignment(Qt.AlignCenter)
        self.__loadingLbl.hide()

        lay = QVBoxLayout()
        lay.addWidget(topWidget)
        lay.addWidget(self.__loadingLbl)
        lay.addWidget(self.__chartView)

        mainWidget = QWidget()
        mainWidget.setLayout(lay)

        self.setCentralWidget(mainWidget)

    def __run(self):
        n = self.__timesLineEdit.text()

        self.__t = Thread(['a.bat', n], self.__res_lst)
        self.__t.finished.connect(self.__t.deleteLater)
        self.__t.started.connect(self.__loadingLbl.show)
        self.__t.finished.connect(self.__loadingLbl.hide)
        self.__t.finished.connect(self.__setChart)
        self.__t.start()

    def __setChart(self):
        fs = re.findall(r'([\w]+):\s([\d\\.]+)\sseconds', self.__res_lst[0])
        lst = []
        for f in fs:
            k, v = f
            lst.append([k, float(v)])
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

    def __save(self):
        filename = QFileDialog.getSaveFileName(self, 'Save', '.', 'PNG (*.png);; '
                                                                  'JPEG (*.jpg;*.jpeg);;'
                                                                  'PDF (*.pdf)')
        ext = filename[1].split('(')[0].strip()
        filename = filename[0]
        if filename:
            # pdf file
            if ext == 'PDF':
                writer = QPdfWriter(filename)
                writer.setResolution(100)
                p = QPainter()
                p.begin(writer)
                self.__chartView.render(p)
                p.setRenderHint(QPainter.SmoothPixmapTransform)
                p.end()
            # image file
            else:
                dpr = self.__chartView.devicePixelRatioF()
                # dpr, *2 is for high quality image
                pixmap = QPixmap(int(self.__chartView.width() * dpr * 2),
                                 int(self.__chartView.height() * dpr * 2))
                # make the background transparent
                pixmap.fill(Qt.transparent)
                p = QPainter(pixmap)
                p.setRenderHint(QPainter.Antialiasing)
                p.begin(pixmap)
                self.__chartView.render(p)
                p.end()
                pixmap.save(filename, ext)

            path = filename.replace('/', '\\')
            subprocess.Popen(r'explorer /select,"' + path + '"')


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


