# This Python file uses the following encoding: utf-8
import os
import sys
from pathlib import Path

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QScrollArea, QWidget


class Widget(QWidget):
    def __init__(self):
        super(Widget, self).__init__()
        self.load_ui()
        self.init_ui()

    def load_ui(self):
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "form.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        loader.load(ui_file, self)
        ui_file.close()

    def init_ui(self):
        scroll = self.findChild(QScrollArea, "drink_type").widget()
        vbox = scroll.layout()
        for i in range(10):
            vbox.addWidget(QCheckBox("Text"))

        scroll = self.findChild(QScrollArea, "glass_type").widget()
        vbox = scroll.layout()
        for i in range(10):
            vbox.addWidget(QCheckBox("Text"))


if __name__ == "__main__":
    app = QApplication([])
    widget = Widget()
    widget.show()
    sys.exit(app.exec())
