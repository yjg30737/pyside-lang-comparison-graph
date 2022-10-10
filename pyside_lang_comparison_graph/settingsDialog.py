from PySide6.QtWidgets import QDialog, QGroupBox, QHBoxLayout, QCheckBox, QVBoxLayout, QWidget, QPushButton


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.__initVal()
        self.__initUi()

    def __initVal(self):
        self.__langs = ['Python', 'R', 'Go', 'Rust', 'Julia']

    def __initUi(self):
        langGrpBox = QGroupBox()
        langGrpBox.setTitle('Languages to Test')
        lay = QVBoxLayout()
        for lang in self.__langs:
            chkBox = QCheckBox(lang)
            # default
            chkBox.setChecked(True)
            lay.addWidget(chkBox)
        langGrpBox.setLayout(lay)

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
        lay.addWidget(langGrpBox)
        lay.addWidget(bottomWidget)

        self.setLayout(lay)
