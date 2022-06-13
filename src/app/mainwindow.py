import os
import sys
from pathlib import Path

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QFile, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QCompleter,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
)

from entity.query import Query

sys.path.append(os.fspath(Path(__file__).resolve().parent.parent))

from src.cbr.cbr import CBR


class MainWindow:
    def __init__(self):
        self.cbr = CBR()
        self.alc_types = self.cbr.case_library.alc_types.copy()
        self.taste_types = self.cbr.case_library.taste_types.copy()
        self.ingredients = self.cbr.case_library.ingredients.copy()
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

        self._init_buttons()
        self._init_scroll_areas()
        self._init_line_edits()
        self._init_score()

    def _init_buttons(self):
        self.window.btn_search.clicked.connect(self._go_to_results_page)
        self.window.btn_reset.clicked.connect(self._go_to_home_page)
        self.window.btn_add_ingr.clicked.connect(
            lambda: self._include_to_list(
                self.window.list_ingredient_includes, self.window.input_ingredient, self.ingredients
            )
            if self.window.input_ingredient.text().strip() != ""
            else None
        )
        self.window.btn_exclude_ingr.clicked.connect(
            lambda: self._include_to_list(
                self.window.list_ingredient_excludes, self.window.input_ingredient, self.ingredients
            )
            if self.window.input_ingredient.text().strip() != ""
            else None
        )

    def _init_scroll_areas(self):
        drink_types = self.window.drink_type
        drink_types.addItem("Any")
        for drink in self.cbr.case_library.drink_types:
            drink_types.addItem(drink)

        glass_types = self.window.glass_type
        glass_types.addItem("Any")
        for glass in self.cbr.case_library.glass_types:
            glass_types.addItem(glass)

    def _init_line_edits(self):
        self._init_completers()

        self.window.input_include_alc.returnPressed.connect(
            lambda: self._include_to_list(self.window.list_alc_includes, self.window.input_include_alc, self.alc_types)
        )
        self.window.list_alc_includes.itemDoubleClicked.connect(
            lambda: self._remove_from(self.window.list_alc_includes, self.window.input_include_alc, self.alc_types)
        )

        self.window.input_basic_taste.returnPressed.connect(
            lambda: self._include_to_list(
                self.window.list_taste_includes, self.window.input_basic_taste, self.taste_types
            )
        )
        self.window.list_taste_includes.itemDoubleClicked.connect(
            lambda: self._remove_from(self.window.list_taste_includes, self.window.input_basic_taste, self.taste_types)
        )

        self.window.list_ingredient_includes.itemDoubleClicked.connect(
            lambda: self._remove_from(
                self.window.list_ingredient_includes, self.window.input_ingredient, self.ingredients
            )
        )
        self.window.list_ingredient_excludes.itemDoubleClicked.connect(
            lambda: self._remove_from(
                self.window.list_ingredient_excludes, self.window.input_ingredient, self.ingredients
            )
        )

    def _init_completers(self):
        alc_completer = QCompleter(self.alc_types, self.window)
        alc_completer.setCaseSensitivity(Qt.CaseInsensitive)
        alc_completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self.window.input_include_alc.setCompleter(alc_completer)

        taste_completer = QCompleter(self.taste_types, self.window)
        taste_completer.setCaseSensitivity(Qt.CaseInsensitive)
        taste_completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self.window.input_basic_taste.setCompleter(taste_completer)

        ingredients_completer = QCompleter(self.ingredients, self.window)
        ingredients_completer.setCaseSensitivity(Qt.CaseInsensitive)
        ingredients_completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self.window.input_ingredient.setCompleter(ingredients_completer)

    def _include_to_list(self, widget_list: QListWidgetItem, line_edit: QLineEdit, types):
        text = line_edit.text().strip()
        items = widget_list.findItems(text, Qt.MatchExactly)
        if text not in types and not items:
            button = QMessageBox.critical(
                self.window,
                "Error",
                f"There is no alcohol named {text}.",
                buttons=QtWidgets.QMessageBox.Close,
                defaultButton=QtWidgets.QMessageBox.Close,
            )
        else:
            if not items:
                QListWidgetItem(text, widget_list)
                types.remove(text)
                completer = QCompleter(types, self.window)
                completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
                line_edit.setCompleter(completer)
            line_edit.clear()

    def _remove_from(self, list_widget: QListWidget, line_edit: QLineEdit, types):
        item = list_widget.takeItem(list_widget.currentRow())
        types.append(item.text())
        completer = QCompleter(sorted(types), self.window)
        completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        line_edit.setCompleter(completer)
        del item

    def _go_to_results_page(self):
        query = Query()
        query.category = self.window.drink_type.currentText()
        query.glass = self.window.glass_type.currentText()
        query.alc_types = [self.window.list_alc_includes.item(i).text() for i in
                       range(self.window.list_alc_includes.count())]
        query.basic_tastes = [self.window.list_taste_includes.item(i).text() for i in
                         range(self.window.list_taste_includes.count())]
        query.ingredients = [self.window.list_ingredient_includes.item(i).text() for i in
                              range(self.window.list_ingredient_includes.count())]
        query.exc_ingredients = [self.window.list_ingredient_excludes.item(i).text() for i in
                              range(self.window.list_ingredient_excludes.count())]
        self.cbr.retrieve(query)
        retrieved_case, adapted_case = self.cbr.adapt()
        self.window.main_widget.setCurrentIndex(1)
        self.window.retrieved_case.setPlainText(str(retrieved_case))
        self.window.adapted_case.setPlainText(str(adapted_case))

    def _go_to_home_page(self):
        self._reset()
        self.window.main_widget.setCurrentIndex(0)

    def _reset(self):
        self.alc_types = self.cbr.case_library.alc_types.copy()
        self.taste_types = self.cbr.case_library.taste_types.copy()
        self.ingredients = self.cbr.case_library.ingredients.copy()
        self._init_completers()
        self.window.lineEdit_new_name.clear()
        self.window.drink_type.setCurrentIndex(0)
        self.window.glass_type.setCurrentIndex(0)
        self.window.list_alc_includes.clear()
        self.window.list_taste_includes.clear()
        self.window.list_ingredient_includes.clear()
        self.window.list_ingredient_excludes.clear()

    def _init_score(self):
        self.window.score_slider.valueChanged.connect(self._update_score)

    def _update_score(self):
        self.window.score_label.setText(f"Score: {self.window.score_slider.value() / 10}")


if __name__ == "__main__":
    app = QApplication([])
    widget = MainWindow()
    sys.exit(app.exec())
