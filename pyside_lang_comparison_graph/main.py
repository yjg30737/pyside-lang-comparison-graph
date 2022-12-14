import os
import signal
import subprocess
import operator

import psutil
from psutil._common import bytes2human
import re
from num2words import num2words
import platform

from PySide6.QtCharts import QChartView, QChart, QBarSeries, QBarCategoryAxis, QBarSet, QValueAxis
from PySide6.QtCore import QThread, QSettings, Signal
from PySide6.QtGui import QPainter, QRegularExpressionValidator, Qt, QPdfWriter, QPixmap, QColor, QTextCursor, \
    QTextCharFormat, QBrush, QFont
from PySide6.QtWidgets import QMainWindow, QHBoxLayout, QLabel, QLineEdit, QSpacerItem, QSizePolicy, QPushButton, \
    QVBoxLayout, QWidget, QApplication, QFileDialog, QTextBrowser, QSplitter, QHeaderView, QTableWidget, \
    QTableWidgetItem, QAbstractItemView, QDialog, QMessageBox

from settingsDialog import SettingsDialog


class TestThread(QThread):
    # str is text
    # QColor is color of text
    # QFont is font of text
    updated = Signal(str, QColor, QFont)
    curTestFinished = Signal()

    def __init__(self, n, langs_test_available_dict: dict, res_lst: list):
        super().__init__()
        # thread control variable
        self.__stopped = False
        self.__stoppedCurrentTest = False

        # process (subprocess.Popen)
        self.__p = ''

        # number of calculation
        self.__n = n

        # variable which are related to languages
        self.__langs_test_available_dict = langs_test_available_dict
        self.__command_dict = {
            'Python': ['python', 'a.py'],
            'R': ['Rscript', 'a.R'],
            'Go': ['go', 'run', 'a.go'],
            'Rust': ['cargo', 'run', '--release', '--'],
            'Julia': ['julia', 'a.jl']
        }
        self.__res_lst = res_lst
        self.__res_lst.clear()

        # common font to emphasize the log about start/finish
        self.__fnt = QFont('Arial', 10)
        self.__fnt.setBold(True)

    def stop(self):
        self.__stopped = True
    
    # stop current language's test
    def stopCurrentLangTest(self, n):
        self.__stoppedCurrentTest = True

    def run(self):
        for k, v in self.__langs_test_available_dict.items():
            if v:
                self.__p = subprocess.Popen(self.__command_dict[k] + [self.__n],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     text=True,
                                     encoding='utf-8',
                                     errors='replace'
                                     )

                self.updated.emit(f"{k} Test Started!", QColor(0, 155, 0), self.__fnt)
                while True:
                    # stop
                    if self.__stopped:
                        self.updated.emit(f"Test Stopped", QColor(155, 0, 0), self.__fnt)
                        self.__stopped = False
                        return
                    realtime_output = self.__p.stdout.readline()
                    if realtime_output == '' and self.__p.poll() is not None or self.__stoppedCurrentTest:
                        break
                    if realtime_output:
                        # log with default color and text
                        self.updated.emit(realtime_output.strip(), QColor(0, 0, 0), QApplication.font())
                    self.__res_lst.append(realtime_output)
                if self.__stoppedCurrentTest:
                    self.__curLangTestTimedOut(k)
                else:
                    self.__curLangTestFinished(k)

    def __curLangTestFinished(self, k):
        self.curTestFinished.emit()
        self.updated.emit(f'{k} Test Finished!', QColor(0, 0, 200), self.__fnt)

    def currentProcessPid(self):
        return self.__p.pid


class TestMonitorThread(QThread):
    timeElapsed = Signal(int)

    def __init__(self):
        super().__init__()
        self.__stopped = False

    def stop(self, pid=None):
        if pid:
            os.kill(pid, signal.SIGINT)
        self.__stopped = True

    def run(self) -> None:
        while True:
            if self.__stopped or psutil.virtual_memory().percent > 100:
                self.__stopped = False
                return

    def resetTime(self):
        self.__resetFlag = True


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__initVal()
        self.__initSettings()
        self.__initUi()
        
    def __initVal(self):
        self.__langs_test_available_dict = {}
        self.__res_lst = []
        self.__t_deleted = False
        # Thread for running test
        self.__testThread = ''
        self.__usageMoniterThread = ''

    def __initSettings(self):
        # [Languages]
        self.__settingsStruct = QSettings('settings.ini', QSettings.IniFormat)
        self.__settingsStruct.beginGroup('Languages')
        for k in self.__settingsStruct.allKeys():
            v = int(self.__settingsStruct.value(k, 1))
            self.__langs_test_available_dict[k] = v
        self.__settingsStruct.endGroup()

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

        self.__settingsBtn = QPushButton('Settings')
        self.__settingsBtn.clicked.connect(self.__settings)

        self.__runTestBtn = QPushButton('Run Test')
        self.__runTestBtn.clicked.connect(self.__run)

        self.__saveBtn = QPushButton('Save')
        self.__saveBtn.clicked.connect(self.__save)
        self.__saveBtn.setEnabled(False)

        lay = QHBoxLayout()
        lay.addWidget(QLabel('Times'))
        lay.addWidget(self.__timesLineEdit)
        lay.addWidget(self.__timesNameLbl)
        lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.MinimumExpanding))
        lay.addWidget(self.__settingsBtn)
        lay.addWidget(self.__runTestBtn)
        lay.addWidget(self.__saveBtn)
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

        self.__initResultInfoWidgetOnChart()

        self.__logLbl = QLabel()
        self.__logLbl.setText('Running the test...')
        self.__logBrowser = QTextBrowser()

        self.__stopBtn = QPushButton('Stop')
        self.__stopBtn.clicked.connect(self.__stop)

        lay = QHBoxLayout()
        lay.addWidget(self.__stopBtn)
        lay.setContentsMargins(0, 0, 0, 0)
        btnWidget = QWidget()
        btnWidget.setLayout(lay)
        
        lay = QVBoxLayout()
        lay.addWidget(self.__logLbl)
        lay.addWidget(self.__logBrowser)
        lay.addWidget(btnWidget)
        
        self.__middleWidget = QWidget()
        self.__middleWidget.setLayout(lay)
        self.__middleWidget.setMaximumHeight(self.__middleWidget.sizeHint().height())
        self.__middleWidget.hide()

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

        lay = QVBoxLayout()
        lay.addWidget(QLabel('Table'))
        lay.addWidget(self.__tableWidget)
        lay.addWidget(QLabel('Device'))
        lay.addWidget(self.__pcInfo)

        tablesWidget = QWidget()
        tablesWidget.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(QLabel('Chart'))
        lay.addWidget(self.__chartView)

        chartWidget = QWidget()
        chartWidget.setLayout(lay)

        tableChartWidget = QSplitter()
        tableChartWidget.addWidget(tablesWidget)
        tableChartWidget.addWidget(chartWidget)
        tableChartWidget.setChildrenCollapsible(False)
        tableChartWidget.setHandleWidth(1)
        tableChartWidget.setStyleSheet(
            "QSplitterHandle {background-color: lightgray;}")
        tableChartWidget.setSizes([300, 700])

        bottomWidget = QSplitter()
        bottomWidget.setOrientation(Qt.Vertical)
        bottomWidget.addWidget(self.__middleWidget)
        bottomWidget.addWidget(tableChartWidget)
        bottomWidget.setChildrenCollapsible(False)
        bottomWidget.setHandleWidth(1)
        bottomWidget.setStyleSheet(
            "QSplitterHandle {background-color: lightgray;}")
        bottomWidget.setSizes([300, 700])

        lay = QVBoxLayout()
        lay.addWidget(topWidget)
        lay.addWidget(bottomWidget)

        mainWidget = QWidget()
        mainWidget.setLayout(lay)

        self.setCentralWidget(mainWidget)

    def __initResultInfoWidgetOnChart(self):
        self.__totalLbl = QLabel(f'Count of Calculation: {self.__timesLineEdit.text()} ({self.__timesNameLbl.text()})')
        lay = QVBoxLayout()
        lay.addWidget(self.__totalLbl)
        resultInfoWidget = QWidget()
        resultInfoWidget.setLayout(lay)
        resultInfoWidget.setStyleSheet('QWidget { background-color: transparent; }')
        scene = self.__chartView.scene()
        scene.addWidget(resultInfoWidget)
        self.__chartView.setScene(scene)

    def __settings(self):
        dialog = SettingsDialog()
        reply = dialog.exec()
        if reply == QDialog.Accepted:
            self.__langs_test_available_dict = dialog.getLangsDict()

    def __run(self):
        n = self.__timesLineEdit.text().replace(',', '')
        
        self.__usageMoniterThread = TestMonitorThread()
        
        self.__testThread = TestThread(n, self.__langs_test_available_dict, self.__res_lst)

        self.__testThread.curTestFinished.connect(self.__usageMoniterThread.resetTime)
        self.__usageMoniterThread.timeElapsed.connect(self.__testThread.stopCurrentLangTest)
        
        self.__testThread.started.connect(self.__handleTestStarted)
        self.__testThread.started.connect(self.__prepareLogBrowser)
        self.__testThread.updated.connect(self.__updateLog)
        self.__testThread.finished.connect(self.__handleTestFinished)
        self.__testThread.start()

    def __prepareLogBrowser(self):
        if self.__middleWidget.isVisible():
            self.__logBrowser.clear()
        else:
            self.__middleWidget.show()

    def __updateLog(self, line, color, font):
        cur = self.__logBrowser.textCursor()
        fmt = QTextCharFormat()
        fmt.setFont(font)
        fmt.setForeground(QBrush(color))
        cur.setCharFormat(fmt)
        self.__logBrowser.moveCursor(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
        self.__logBrowser.moveCursor(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        self.__logBrowser.setTextCursor(cur)
        self.__logBrowser.append(line)
        vBar = self.__logBrowser.verticalScrollBar()
        vBar.setValue(vBar.maximum())

    def __stop(self):
        self.__testThread.stop()
        pid = self.__testThread.currentProcessPid()
        self.__usageMoniterThread.stop(pid)

    def __handleTestStarted(self):
        # set thread deleted flag for preventing runtime error
        self.__t_deleted = False
        # disable the button when running in order to prevent error
        self.__logLbl.setText('Running the test...')
        self.__timesLineEdit.setEnabled(False)
        self.__runTestBtn.setEnabled(False)
        self.__settingsBtn.setEnabled(False)
        self.__saveBtn.setEnabled(False)
        self.__stopBtn.setEnabled(True)
        self.__usageMoniterThread.start()
        self.__axisX.clear()

    def __isTestFinished(self):
        return self.__usageMoniterThread.isRunning()

    # enable the button after test is over
    def __handleTestFinished(self):
        self.__timesLineEdit.setEnabled(True)
        self.__runTestBtn.setEnabled(True)
        self.__settingsBtn.setEnabled(True)
        self.__stopBtn.setEnabled(False)
        if self.__isTestFinished():
            self.__logLbl.setText('Finished')
            self.__usageMoniterThread.stop()
            self.__updateLog('Finished!', QColor(0, 0, 0), QApplication.font())
            self.__setChart()
            self.__saveBtn.setEnabled(True)
        else:
            self.__logLbl.setText('Stopped')

        # set thread deleted flag for preventing runtime error
        self.__t_deleted = True
        self.__usageMoniterThread.deleteLater()
        self.__testThread.deleteLater()

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
        try:
            self.__tableWidget.clearContents()
            lst = []
            for res in self.__res_lst:
                fs = re.findall(r'([\w]+):\s([\d\\.]+)\sseconds', res)
                for f in fs:
                    k, v = f
                    lst.append([k, float(v)])

            lst = sorted(lst, key=operator.itemgetter(1))
            barSet = self.__series.barSets()[0]
            barSet.remove(0, barSet.count())
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

            self.__totalLbl.setText(
                f'Count of Calculation: {self.__timesLineEdit.text()} ({self.__timesNameLbl.text()})')


        except Exception as e:
            print(e)

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
        if isinstance(self.__testThread, QThread):
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


