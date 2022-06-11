# This Python file uses the following encoding: utf-8
import os
import sys
from pathlib import Path

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QCheckBox, QScrollArea, QPushButton, QStackedWidget, QMainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.load_ui()
        self.init_ui()

    def load_ui(self):
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "form.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.window = loader.load(ui_file, self)
        ui_file.close()
        self.window.show()

    def init_ui(self):
        stack = self.findChild(QStackedWidget, "main_widget")
        current = stack.setCurrentIndex(0)

        self.init_buttons()
        self.init_scroll_areas()

    def init_scroll_areas(self):
        scroll = self.findChild(QScrollArea, "drink_type").widget()
        vbox = scroll.layout()
        for i in range(10):
            vbox.addWidget(QCheckBox("Text"))

        scroll = self.findChild(QScrollArea, "glass_type").widget()
        vbox = scroll.layout()
        for i in range(10):
            vbox.addWidget(QCheckBox("Text"))

    def init_buttons(self):
        btn_next = self.findChild(QPushButton, "btn_next")
        btn_next.clicked.connect(self.next_page)
        btn_back = self.findChild(QPushButton, "btn_back")
        btn_back.clicked.connect(self.previous_page)
        btn_back.setEnabled(False)

    def next_page(self):
        stack = self.findChild(QStackedWidget, "main_widget")
        current = stack.currentIndex()
        stack.setCurrentIndex(current + 1)

        btn_next = self.findChild(QPushButton, "btn_next")
        btn_back = self.findChild(QPushButton, "btn_back")
        if not btn_back.isEnabled():
            btn_back.setEnabled(True)

        if current + 2 == stack.count():
            btn_next.setEnabled(False)
        elif not btn_next.isEnabled():
            btn_next.setEnabled(True)

    def previous_page(self):
        stack = self.findChild(QStackedWidget, "main_widget")
        current = stack.currentIndex()
        stack.setCurrentIndex(current - 1)

        btn_next = self.findChild(QPushButton, "btn_next")
        btn_back = self.findChild(QPushButton, "btn_back")
        if not btn_next.isEnabled():
            btn_next.setEnabled(True)

        if current == 1:
            btn_back.setEnabled(False)
        elif not btn_back.isEnabled():
            btn_back.setEnabled(True)


if __name__ == "__main__":
    app = QApplication([])
    widget = MainWindow()
    sys.exit(app.exec())
