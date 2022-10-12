import subprocess
import operator
import psutil
from psutil._common import bytes2human
import re
from num2words import num2words
import platform

from PySide6.QtCharts import QChartView, QChart, QBarSeries, QBarCategoryAxis, QBarSet, QValueAxis
from PySide6.QtCore import QThread
from PySide6.QtGui import QPainter, QRegularExpressionValidator, Qt, QPdfWriter, QPixmap
from PySide6.QtWidgets import QMainWindow, QHBoxLayout, QLabel, QLineEdit, QSpacerItem, QSizePolicy, QPushButton, \
    QVBoxLayout, QWidget, QApplication, QFileDialog, QTextBrowser, QSplitter, QHeaderView, QTableWidget, \
    QTableWidgetItem, QAbstractItemView, QDialog, QMessageBox

from settingsDialog import SettingsDialog


class Thread(QThread):
    def __init__(self, n, res_lst: list):
        super().__init__()
        self.__n = n
        self.__res_lst = res_lst
        self.__res_lst.clear()

    def run(self):
        p = subprocess.run(['Rscript', 'a.R', self.__n], capture_output=True, text=True)
        self.__res_lst.append(p.stdout)
        p = subprocess.run(['go', 'run', 'a.go', self.__n], capture_output=True, text=True)
        self.__res_lst.append(p.stdout)
        p = subprocess.run(['python', 'a.py', self.__n], capture_output=True, text=True)
        self.__res_lst.append(p.stdout)
        p = subprocess.run(['cargo', 'run', '--release', '--', self.__n], capture_output=True, text=True)
        self.__res_lst.append(p.stdout)
        p = subprocess.run(['julia', 'a.jl', self.__n], capture_output=True, text=True)
        self.__res_lst.append(p.stdout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__initVal()
        self.__initUi()
        
    def __initVal(self):
        self.__langs_to_test = []
        self.__res_lst = []
        self.__t_deleted = False
        # Thread for running test
        self.__t = ''

    def __initUi(self):
        self.setWindowTitle('Language Comparison')

        n_default = 10000000

        self.__timesLineEdit = QLineEdit()
        self.__timesLineEdit.setText(f'{n_default:,}')
        self.__timesLineEdit.textEdited.connect(self.__textEdited)

        self.__timesNameLbl = QLabel(num2words(n_default))
        self.__timesNameLbl.setMaximumWidth(300)

        v = QRegularExpressionValidator()
        v.setRegularExpression('^\d{1,3}(,\d{3})*(\d+)?$')
        self.__timesLineEdit.setValidator(v)

        settingsBtn = QPushButton('Settings')
        settingsBtn.clicked.connect(self.__settings)

        self.__runTestBtn = QPushButton('Run Test')
        self.__runTestBtn.clicked.connect(self.__run)

        saveBtn = QPushButton('Save')
        saveBtn.clicked.connect(self.__save)

        lay = QHBoxLayout()
        lay.addWidget(QLabel('Times'))
        lay.addWidget(self.__timesLineEdit)
        lay.addWidget(self.__timesNameLbl)
        lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.MinimumExpanding))
        lay.addWidget(settingsBtn)
        lay.addWidget(self.__runTestBtn)
        lay.addWidget(saveBtn)
        lay.setContentsMargins(0, 0, 0, 0)

        topWidget = QWidget()
        topWidget.setLayout(lay)
        topWidget.setFixedHeight(topWidget.sizeHint().height())

        self.__series = QBarSeries()
        barset = QBarSet('Time')
        self.__series.append(barset)
        self.__series.setLabelsVisible(True)

        self.__axisX = QBarCategoryAxis()

        self.__axisY = QValueAxis()

        self.__chart = QChart()
        self.__chart.layout().setContentsMargins(0, 0, 0, 0)
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
        self.__loadingLbl.setMaximumHeight(self.__loadingLbl.sizeHint().height())
        self.__loadingLbl.hide()

        lay = QVBoxLayout()

        self.__tableWidget = QTableWidget()
        self.__tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.__tableWidget.setColumnCount(1)
        self.__tableWidget.setHorizontalHeaderLabels(['Time'])
        self.__tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.__tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        pcInfo = f'CPU: {platform.processor()}\n' \
                 f'RAM: {bytes2human(psutil.virtual_memory().total)}'
        self.__pcInfo = QTextBrowser()
        self.__pcInfo.setText(pcInfo)

        lay.addWidget(QLabel('Table'))
        lay.addWidget(self.__tableWidget)
        lay.addWidget(QLabel('Device'))
        lay.addWidget(self.__pcInfo)

        leftWidget = QWidget()
        leftWidget.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(QLabel('Chart'))
        lay.addWidget(self.__chartView)

        rightWidget = QWidget()
        rightWidget.setLayout(lay)

        bottomWidget = QSplitter()
        bottomWidget.addWidget(leftWidget)
        bottomWidget.addWidget(rightWidget)
        bottomWidget.setChildrenCollapsible(False)
        bottomWidget.setHandleWidth(1)
        bottomWidget.setStyleSheet(
            "QSplitterHandle {background-color: lightgray;}")
        bottomWidget.setSizes([300, 700])

        lay = QVBoxLayout()
        lay.addWidget(topWidget)
        lay.addWidget(self.__loadingLbl)
        lay.addWidget(bottomWidget)

        mainWidget = QWidget()
        mainWidget.setLayout(lay)

        self.setCentralWidget(mainWidget)

    def __settings(self):
        dialog = SettingsDialog()
        reply = dialog.exec()
        if reply == QDialog.Accepted:
            self.__langs_to_test = dialog.getLangsToTest()
            print(self.__langs_to_test)

    def __run(self):
        n = self.__timesLineEdit.text().replace(',', '')

        # disable the button when running to prevent error
        self.__runTestBtn.setEnabled(False)
        
        self.__t_deleted = False
        self.__t = Thread(n, self.__res_lst)
        self.__t.finished.connect(self.__setThreadDeletedFlagForPreventingRuntimeError)
        self.__t.started.connect(self.__loadingLbl.show)
        self.__t.finished.connect(self.__loadingLbl.hide)
        self.__t.finished.connect(self.__setChart)
        self.__t.start()

    def __setThreadDeletedFlagForPreventingRuntimeError(self):
        self.__t_deleted = True
        self.__t.deleteLater()

    def __textEdited(self, text):
        if text:
            n = int(text.replace(',', ''))
            self.__timesLineEdit.setText(f'{n:,}')
            n_text = num2words(n)
            self.__timesNameLbl.setText(n_text)
            if self.__timesNameLbl.fontMetrics().boundingRect(n_text).width() > self.__timesNameLbl.maximumWidth():
                reduced_n_text = n-(n % pow(10, len(str(n))-2))
                self.__timesNameLbl.setText(f"about {num2words(reduced_n_text)}")

    def __setChart(self):
        # enable the button which was disabled when running
        self.__runTestBtn.setEnabled(True)

        self.__tableWidget.clearContents()
        lst = []
        for res in self.__res_lst:
            fs = re.findall(r'([\w]+):\s([\d\\.]+)\sseconds', res)
            for f in fs:
                k, v = f
                lst.append([k, float(v)])

        lst = sorted(lst, key=operator.itemgetter(1))
        barSet = self.__series.barSets()[0]
        barSet.remove(0, 5)
        langs = [item[0] for item in lst]

        self.__axisX.clear()
        self.__axisX.append(langs)
        self.__axisY.setRange(0, max([float(item[1]) for item in lst]))

        self.__tableWidget.setRowCount(len(langs))
        self.__tableWidget.setVerticalHeaderLabels(langs)

        for i in range(len(lst)):
            v = lst[i][1]
            barSet <<= float(v)
            item = QTableWidgetItem(str(v))
            item.setTextAlignment(Qt.AlignCenter)
            self.__tableWidget.setItem(i, 0, item)

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

    def closeEvent(self, e):
        if isinstance(self.__t, QThread):
            if self.__t_deleted:
                e.accept()
            else:
                QMessageBox.critical(self, 'Warning',
                                           'You can\'t close while running test.')
                e.ignore()
        else:
            e.accept()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


