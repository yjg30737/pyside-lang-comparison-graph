import shutil

from PySide6.QtWidgets import QDialog, QHBoxLayout, QCheckBox, QVBoxLayout, QPushButton, QTableWidgetItem, \
    QAbstractItemView, QGroupBox, QSpinBox

import typing

from PySide6.QtWidgets import QHeaderView, QTableWidget, QWidget, QGridLayout
from PySide6.QtCore import Qt, Signal, QSettings


class CheckBox(QWidget):
    checkedSignal = Signal(int, Qt.CheckState)

    def __init__(self, r_idx, flag):
        super().__init__()
        self.__r_idx = r_idx
        self.__initUi(flag)

    def __initUi(self, flag):
        chkBox = QCheckBox()
        chkBox.setChecked(flag)
        chkBox.stateChanged.connect(self.__sendCheckedSignal)

        lay = QGridLayout()
        lay.addWidget(chkBox)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setAlignment(chkBox, Qt.AlignCenter)

        self.setLayout(lay)

    def __sendCheckedSignal(self, flag):
        self.checkedSignal.emit(self.__r_idx, flag)

    def isChecked(self):
        f = self.layout().itemAt(0).widget().isChecked()
        return Qt.Checked if f else Qt.Unchecked

    def setChecked(self, f):
        if isinstance(f, Qt.CheckState):
            self.getCheckBox().setCheckState(f)
        elif isinstance(f, bool):
            self.getCheckBox().setChecked(f)

    def getCheckBox(self):
        return self.layout().itemAt(0).widget()


class CheckBoxTableWidget(QTableWidget):
    checkedSignal = Signal(int, Qt.CheckState)

    def __init__(self, parent=None):
        self._default_check_flag = False
        super().__init__()
        self.__initUi()

    def __initUi(self):
        # Least column count (one for checkbox, one for another)
        self.setColumnCount(2)

    def setHorizontalHeaderLabels(self, labels: typing.Iterable[str]) -> None:
        lst = [_ for _ in labels if _]
        lst.insert(0, '') # 0 index vacant for checkbox
        super().setHorizontalHeaderLabels(lst)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

    def clearContents(self, start_r_idx=0):
        for i in range(start_r_idx, self.rowCount()):
            for j in range(1, self.columnCount()):
                self.takeItem(i, j)

    def setDefaultValueOfCheckBox(self, flag: bool):
        self._default_check_flag = flag

    def stretchEveryColumnExceptForCheckBox(self):
        if self.horizontalHeader():
            self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)

    def setRowCount(self, rows: int) -> None:
        super().setRowCount(rows)
        for row in range(0, rows):
            self.__setCheckBox(row)

    def __setCheckBox(self, r_idx):
        chkBox = CheckBox(r_idx, self._default_check_flag)
        chkBox.checkedSignal.connect(self.__sendCheckedSignal)

        self.setCellWidget(r_idx, 0, chkBox)

        if self._default_check_flag:
            self.checkedSignal.emit(r_idx, Qt.Checked)
        self.resizeColumnToContents(0)

    def __sendCheckedSignal(self, r_idx, flag: Qt.CheckState):
        self.checkedSignal.emit(r_idx, flag)

    def toggleState(self, state):
        for i in range(self.rowCount()):
            item = super().cellWidget(i, 0).getCheckBox()
            item.setChecked(state)

    def getCheckedRows(self):
        return self.__getCheckedStateOfRows(Qt.Checked)

    def getUncheckedRows(self):
        return self.__getCheckedStateOfRows(Qt.Unchecked)

    def __getCheckedStateOfRows(self, flag: Qt.Checked):
        flag_lst = []
        for i in range(self.rowCount()):
            item = super().cellWidget(i, 0)
            if item.isChecked() == flag:
                flag_lst.append(i)

        return flag_lst

    def setCheckedAt(self, idx, f):
        self.cellWidget(idx, 0).setChecked(f)

    def removeCheckedRows(self):
        self.__removeCertainCheckedStateRows(Qt.Checked)

    def removeUncheckedRows(self):
        self.__removeCertainCheckedStateRows(Qt.Unchecked)

    def __removeCertainCheckedStateRows(self, flag):
        flag_lst = self.__getCheckedStateOfRows(flag)
        flag_lst = reversed(flag_lst)
        for i in flag_lst:
            self.removeRow(i)


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.__initVal()
        self.__initSettings()
        self.__initUi()

    def __initVal(self):
        self.__langs_test_available_dict = {}
        self.__langs_app_dict = {'Python': 'python', 'R': 'r', 'Go': 'go', 'Rust': 'rustc', 'Julia': 'julia'}
        self.__timeoutEnabled = False
        self.__timeoutSeconds = 0

    def __initSettings(self):
        # [Languages]
        self.__settingsStruct = QSettings('settings.ini', QSettings.IniFormat)
        self.__settingsStruct.beginGroup('Languages')
        for k in self.__settingsStruct.allKeys():
            v = int(self.__settingsStruct.value(k, 1))
            self.__langs_test_available_dict[k] = v
        self.__settingsStruct.endGroup()

        # [Test]
        self.__settingsStruct.beginGroup('Test')
        self.__timeoutEnabled = self.__settingsStruct.value('TimeoutEnabled')
        self.__timeoutSeconds = self.__settingsStruct.value('TimeoutSeconds')
        self.__settingsStruct.endGroup()

    def __initUi(self):
        self.setWindowTitle('Settings')
        self.__langTableWidget = CheckBoxTableWidget()
        self.__langTableWidget.setRowCount(len(self.__langs_app_dict))
        self.__langTableWidget.setColumnCount(3)
        self.__langTableWidget.setHorizontalHeaderLabels(['Language', 'Installed'])
        self.__langTableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.__langTableWidget.stretchEveryColumnExceptForCheckBox()
        self.__langTableWidget.verticalHeader().setHidden(True)
        self.__langTableWidget.setShowGrid(False)
        self.__langTableWidget.setSelectionMode(QAbstractItemView.NoSelection)
        self.__langTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        for i in range(len(self.__langs_app_dict)):
            langName = list(self.__langs_app_dict.keys())[i]
            langItem = QTableWidgetItem(langName)
            langItem.setTextAlignment(Qt.AlignCenter)
            self.__langTableWidget.setItem(i, 1, langItem)
            btn = QPushButton()
            langAppName = list(self.__langs_app_dict.values())[i]
            if shutil.which(langAppName) != '':
                btn.setText('Installed')
                # todo make it enable to version check of each langs and update
                btn.setDisabled(True)
                if self.__langs_test_available_dict[langName]:
                    self.__langTableWidget.setCheckedAt(i, True)
            else:
                btn.setText('Install')
            self.__langTableWidget.setCellWidget(i, 2, btn)

        allChkBox = QCheckBox('Check All')
        allChkBox.stateChanged.connect(self.__langTableWidget.toggleState)
        allChkBox.setChecked(len(self.__langTableWidget.getCheckedRows()) == 5)

        lay = QVBoxLayout()
        lay.addWidget(allChkBox)
        lay.addWidget(self.__langTableWidget)

        langGrpBox = QGroupBox()
        langGrpBox.setTitle('Select Languages to Test')
        langGrpBox.setLayout(lay)

        self.__timeOutSpinBox = QSpinBox()
        self.__timeOutSpinBox.setRange(1, 100)
        self.__timeOutSpinBox.setValue(int(self.__timeoutSeconds))

        self.__setTimeOutCheckBox = QCheckBox('Set Timeout')
        self.__setTimeOutCheckBox.toggled.connect(self.__toggleTimeOutSpinBox)
        self.__setTimeOutCheckBox.setChecked(bool(self.__timeoutEnabled))

        self.__toggleTimeOutSpinBox(self.__setTimeOutCheckBox.isChecked())

        lay = QVBoxLayout()
        lay.addWidget(self.__setTimeOutCheckBox)
        lay.addWidget(self.__timeOutSpinBox)
        lay.setAlignment(Qt.AlignTop)

        testGrpBox = QGroupBox()
        testGrpBox.setTitle('Test Settings')
        testGrpBox.setLayout(lay)

        lay = QHBoxLayout()
        lay.addWidget(langGrpBox)
        lay.addWidget(testGrpBox)

        topWidget = QWidget()
        topWidget.setLayout(lay)

        self.__okBtn = QPushButton('OK')
        self.__okBtn.clicked.connect(self.accept)

        closeBtn = QPushButton('Close')
        closeBtn.clicked.connect(self.close)

        lay = QHBoxLayout()
        lay.addWidget(self.__okBtn)
        lay.addWidget(closeBtn)
        lay.setContentsMargins(0, 0, 0, 0)

        bottomWidget = QWidget()
        bottomWidget.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(topWidget)
        lay.addWidget(bottomWidget)

        self.setLayout(lay)

    def __toggleTimeOutSpinBox(self, f):
        self.__timeOutSpinBox.setEnabled(f)

    def __setLangsDict(self):
        checked_langs_lst = [self.__langTableWidget.item(i, 1).text() for i in self.__langTableWidget.getCheckedRows()]
        for k in self.__langs_test_available_dict.keys():
            if k in checked_langs_lst:
                self.__langs_test_available_dict[k] = 1
            else:
                self.__langs_test_available_dict[k] = 0
    def getLangsDict(self):
        return self.__langs_test_available_dict

    def accept(self) -> None:
        super().accept()
        self.__setLangsDict()
        dict = self.getLangsDict()
        for k, v in dict.items():
            self.__settingsStruct.setValue(k, v)
        self.__settingsStruct.setValue('Test/TimeoutEnabled', int(self.__setTimeOutCheckBox.isChecked()))
        self.__settingsStruct.setValue('Test/TimeoutSeconds', self.__timeOutSpinBox.value())