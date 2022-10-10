from PySide6.QtWidgets import QDialog, QGroupBox, QHBoxLayout, QCheckBox, QVBoxLayout, QPushButton, QTableWidgetItem, \
    QAbstractItemView, QLabel

import typing

from PySide6.QtWidgets import QHeaderView, QTableWidget, QWidget, QGridLayout
from PySide6.QtCore import Qt, Signal


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
            item = super().cellWidget(i, 0).layout().itemAt(0).widget()
            if item.checkState() != state:
                item.setCheckState(state)

    def getCheckedRows(self):
        return self.__getCheckedStateOfRows(Qt.Checked)

    def getUncheckedRows(self):
        return self.__getCheckedStateOfRows(Qt.Unchecked)

    def __getCheckedStateOfRows(self, flag: Qt.CheckState):
        flag_lst = []
        for i in range(self.rowCount()):
            item = super().cellWidget(i, 0)
            if item.checkState() == flag:
                flag_lst.append(i)

        return flag_lst

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
        self.__initUi()

    def __initVal(self):
        self.__langs = ['Python', 'R', 'Go', 'Rust', 'Julia']

    def __initUi(self):
        tableWidget = CheckBoxTableWidget()
        tableWidget.setRowCount(len(self.__langs))
        tableWidget.setHorizontalHeaderLabels(['Language', 'Installed'])
        tableWidget.verticalHeader().setHidden(True)
        tableWidget.setShowGrid(False)
        tableWidget.setSelectionMode(QAbstractItemView.NoSelection)
        tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        for i in range(len(self.__langs)):
            item = QTableWidgetItem(self.__langs[i])
            item.setTextAlignment(Qt.AlignCenter)
            tableWidget.setItem(i, 1, item)

        lay = QVBoxLayout()
        lay.addWidget(QLabel('Select Languages to Test'))
        lay.addWidget(tableWidget)

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
