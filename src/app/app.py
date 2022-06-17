import logging
import os
import sys
import time
import webbrowser as wb
from pathlib import Path

from PySide6 import QtGui
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

sys.path.append(os.fspath(Path(__file__).resolve().parent.parent.parent))

from definitions import LOG_FILE, USER_MANUAL_FILE
from src.entity.query import Query
from src.cbr.cbr import CBR


def _open_user_manual():
    print(f"Opening User Manual...")
    wb.open_new(r"file://{}".format(USER_MANUAL_FILE))


class MainWindow:
    def __init__(self):
        self.cbr = CBR()
        self.alc_types = self.cbr.case_library.alc_types.copy()
        self.taste_types = self.cbr.case_library.taste_types.copy()
        self.ingredients = self.cbr.case_library.ingredients.copy()
        self.window = None
        self.load_ui()
        self.init_ui()
        self.logger = logging.getLogger("GUI")
        self.logger.setLevel(logging.INFO)

        logging.basicConfig(
            filename=LOG_FILE,
            format="%(asctime)s [%(name)s] - %(levelname)s: %(message)s",
            filemode="w",
            level=logging.INFO,
        )

    def load_ui(self):
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "app.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.window = loader.load(ui_file)
        ui_file.close()
        pixmap = QtGui.QPixmap(os.path.join(os.path.dirname(__file__), "icon.ico"))
        self.window.setWindowIcon(pixmap)
        self.window.showMaximized()

    def init_ui(self):
        self._init_buttons()
        self._init_scroll_areas()
        self._init_line_edits()
        self._init_score()
        self._init_sliders()
        self.window.user_manual.triggered.connect(_open_user_manual)

    def _init_sliders(self):
        self.window.score_slider.setValue(50)
        self.window.score_slider.setEnabled(False)

    def _init_buttons(self):
        self.window.btn_run.clicked.connect(self._send_query)
        self.window.btn_evaluate.clicked.connect(self._send_evaluation)
        self.window.btn_evaluate.setEnabled(False)
        self.window.btn_add_alcohol.clicked.connect(
            lambda: self._include_to_list(
                self.window.list_alc_includes, self.window.input_include_alc, self.alc_types, "alcohol"
            )
        )
        self.window.btn_add_taste.clicked.connect(
            lambda: self._include_to_list(
                self.window.list_taste_includes, self.window.input_basic_taste, self.taste_types, "basic taste"
            )
        )
        self.window.btn_add_ingr.clicked.connect(
            lambda: self._include_to_list(
                self.window.list_ingredient_includes, self.window.input_ingredient, self.ingredients, "ingredient"
            )
            if self.window.input_ingredient.text().strip() != ""
            else None
        )
        self.window.btn_exclude_ingr.clicked.connect(
            lambda: self._include_to_list(
                self.window.list_ingredient_excludes, self.window.input_ingredient, self.ingredients, "ingredient"
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
            lambda: self._include_to_list(
                self.window.list_alc_includes, self.window.input_include_alc, self.alc_types, "alcohol"
            )
        )
        self.window.list_alc_includes.itemDoubleClicked.connect(
            lambda: self._remove_from(self.window.list_alc_includes, self.window.input_include_alc, self.alc_types)
        )

        self.window.input_basic_taste.returnPressed.connect(
            lambda: self._include_to_list(
                self.window.list_taste_includes, self.window.input_basic_taste, self.taste_types, "basic taste"
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

    def _include_to_list(self, widget_list: QListWidgetItem, line_edit: QLineEdit, types, filter_type):
        text = line_edit.text().strip()
        items = widget_list.findItems(text, Qt.MatchExactly)
        if text not in types and not items:
            QMessageBox.critical(
                self.window,
                "Error",
                f"There is no {filter_type} named {text}.",
                buttons=QMessageBox.Close,
                defaultButton=QMessageBox.Close,
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

    def _send_query(self):
        recipe_name = self.window.lineEdit_new_name.text()
        if not recipe_name:
            self._show_warning("No name found", "Please enter a recipe name.")
        else:
            query = Query()
            query.category = self.window.drink_type.currentText()
            query.glass = self.window.glass_type.currentText()
            query.alc_types = [
                self.window.list_alc_includes.item(i).text() for i in range(self.window.list_alc_includes.count())
            ]
            query.basic_tastes = [
                self.window.list_taste_includes.item(i).text() for i in range(self.window.list_taste_includes.count())
            ]
            query.ingredients = [
                self.window.list_ingredient_includes.item(i).text()
                for i in range(self.window.list_ingredient_includes.count())
            ]
            query.exc_ingredients = []
            query.exc_alc_types = []
            alcoholic_ingredients = self.cbr.case_library.ingredients_onto["alcoholic"]
            for i in range(self.window.list_ingredient_excludes.count()):
                ingredient = self.window.list_ingredient_excludes.item(i).text()
                query.exc_ingredients.append(ingredient)
                alcohol = alcoholic_ingredients.get(ingredient, None)
                if alcohol is not None and alcohol not in query.alc_types:
                    query.exc_alc_types.append(alcohol)

            query.exc_ingredients = [
                self.window.list_ingredient_excludes.item(i).text()
                for i in range(self.window.list_ingredient_excludes.count())
            ]
            start_time = time.perf_counter()
            retrieved_case, adapted_case = self.cbr.run_query(query, recipe_name)
            self.logger.info(f"The system spent {time.perf_counter() - start_time} seconds to answer the query.")
            self._reset()
            self.window.retrieved_case.setPlainText(str(retrieved_case))
            self.window.adapted_case.setPlainText(str(adapted_case))
            self.window.btn_evaluate.setEnabled(True)
            self.window.score_slider.setEnabled(True)
            self.window.btn_run.setEnabled(False)

    def _reset(self):
        self.alc_types = self.cbr.case_library.alc_types.copy()
        self.taste_types = self.cbr.case_library.taste_types.copy()
        self.ingredients = self.cbr.case_library.ingredients.copy()
        self._init_completers()
        self._clear_line_edits()
        self.window.drink_type.setCurrentIndex(0)
        self.window.glass_type.setCurrentIndex(0)
        self._clear_item_lists()
        self.window.retrieved_case.clear()
        self.window.adapted_case.clear()
        self._reset_slider()

    def _clear_item_lists(self):
        self.window.list_alc_includes.clear()
        self.window.list_taste_includes.clear()
        self.window.list_ingredient_includes.clear()
        self.window.list_ingredient_excludes.clear()

    def _clear_line_edits(self):
        self.window.lineEdit_new_name.clear()
        self.window.input_include_alc.clear()
        self.window.input_basic_taste.clear()
        self.window.input_ingredient.clear()

    def _send_evaluation(self):
        score = self.window.score_slider.value() / 100
        self.cbr.evaluation(score)
        self._init_sliders()
        self.window.btn_evaluate.setEnabled(False)
        self.window.btn_run.setEnabled(True)
        self.window.retrieved_case.clear()
        self.window.adapted_case.clear()
        self._reset_slider()
        QMessageBox.information(
            self.window,
            "Evaluation completed",
            "Your evaluation has been registered.",
            buttons=QMessageBox.Close,
            defaultButton=QMessageBox.Close,
        )

    def _init_score(self):
        self.window.score_slider.valueChanged.connect(self._update_score)

    def _update_score(self):
        self.window.score_label.setText(f"Score: {self.window.score_slider.value() / 10}")

    def _show_warning(self, title, message):
        QMessageBox.warning(
            self.window,
            title,
            message,
            buttons=QMessageBox.Close,
            defaultButton=QMessageBox.Close,
        )

    def _reset_slider(self):
        self.window.score_label.setText(f"Score: 5.0")
        self.window.score_slider.setValue(50)


if __name__ == "__main__":
    app = QApplication([])
    widget = MainWindow()
    sys.exit(app.exec())
