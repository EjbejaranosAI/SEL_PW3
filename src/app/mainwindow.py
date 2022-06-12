import os
import sys
from pathlib import Path

from PySide6 import QtWidgets
from PySide6.QtCore import QFile, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QCompleter,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
)

sys.path.append(os.fspath(Path(__file__).resolve().parent.parent))

from src.cbr.cbr import CBR


def _remove_from(list_widget: QListWidget):
    item = list_widget.takeItem(list_widget.currentRow())
    del item


class MainWindow:
    def __init__(self):
        self.cbr = CBR()
        self.alc_completer = None
        self.taste_completer = None
        self.ingredients_completer = None
        self.window = None
        self.load_ui()
        self.init_ui()

    def load_ui(self):
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "mainwindow.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.window = loader.load(ui_file)
        ui_file.close()
        self.window.showMaximized()

    def init_ui(self):
        self.window.main_widget.setCurrentIndex(0)
        self.window.query_buttons.setVisible(False)

        self.init_buttons()
        self.init_scroll_areas()
        self.init_line_edits()

    def init_scroll_areas(self):
        drink_types = self.window.drink_type
        drink_types.addItem("Any")
        for drink in self.cbr.case_library.drink_types:
            drink_types.addItem(drink)

        glass_types = self.window.glass_type
        glass_types.addItem("Any")
        for glass in self.cbr.case_library.glass_types:
            glass_types.addItem(glass)

    def init_buttons(self):
        self.window.btn_next.clicked.connect(self.next_page)
        self.window.btn_back.clicked.connect(self.previous_page)
        self.window.btn_back.setEnabled(False)

    def init_line_edits(self):
        self.init_completers()

        self.window.input_include_alc.setCompleter(self.alc_completer)
        self.window.input_include_alc.returnPressed.connect(
            lambda: self._include_to_list(
                self.window.list_alc_includes, self.window.input_include_alc, self.cbr.case_library.alc_types
            )
        )
        self.window.list_alc_includes.itemDoubleClicked.connect(lambda: _remove_from(self.window.list_alc_includes))

        self.window.input_exclude_alc.setCompleter(self.alc_completer)
        self.window.input_exclude_alc.returnPressed.connect(
            lambda: self._include_to_list(
                self.window.list_alc_excludes, self.window.input_exclude_alc, self.cbr.case_library.alc_types
            )
        )
        self.window.list_alc_excludes.itemDoubleClicked.connect(lambda: _remove_from(self.window.list_alc_excludes))

        self.window.lineEdit_basic_taste.setCompleter(self.taste_completer)
        self.window.lineEdit_basic_taste.returnPressed.connect(
            lambda: self._include_to_list(
                self.window.list_taste_includes, self.window.lineEdit_basic_taste, self.cbr.case_library.taste_types
            )
        )
        self.window.list_taste_includes.itemDoubleClicked.connect(lambda: _remove_from(self.window.list_taste_includes))

        self.window.lineEdit_ingredient.setCompleter(self.ingredients_completer)
        self.window.lineEdit_ingredient.returnPressed.connect(
            lambda: self._include_to_list(
                self.window.list_ingredient_includes, self.window.lineEdit_ingredient, self.cbr.case_library.ingredients
            )
        )
        self.window.list_ingredient_includes.itemDoubleClicked.connect(
            lambda: _remove_from(self.window.list_ingredient_includes)
        )

    def init_completers(self):
        self.alc_completer = QCompleter(self.cbr.case_library.alc_types, self.window)
        self.alc_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.taste_completer = QCompleter(self.cbr.case_library.taste_types, self.window)
        self.taste_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ingredients_completer = QCompleter(self.cbr.case_library.ingredients, self.window)
        self.ingredients_completer.setCaseSensitivity(Qt.CaseInsensitive)

    def _include_to_list(self, widget_list, line_edit, types):
        text = line_edit.text().strip()
        if text not in types:
            button = QMessageBox.critical(
                self.window,
                "Error",
                f"There is no alcohol named {text}.",
                buttons=QtWidgets.QMessageBox.Close,
                defaultButton=QtWidgets.QMessageBox.Close,
            )
        else:
            items = widget_list.findItems(text, Qt.MatchExactly)
            line_edit.clear()
            if not items:
                QListWidgetItem(text, widget_list)

    def next_page(self):
        current = self.window.main_widget.currentIndex()
        self.window.main_widget.setCurrentIndex(current + 1)

        btn_next = self.window.btn_next
        btn_back = self.window.btn_back
        if not btn_back.isEnabled():
            btn_back.setEnabled(True)

        if current + 2 == self.window.main_widget.count():
            btn_next.setEnabled(False)
        elif not btn_next.isEnabled():
            btn_next.setEnabled(True)

    def previous_page(self):
        stack = self.window.main_widget
        current = stack.currentIndex()
        stack.setCurrentIndex(current - 1)

        btn_next = self.window.btn_next
        btn_back = self.window.btn_back
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
