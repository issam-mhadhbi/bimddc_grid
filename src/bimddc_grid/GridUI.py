import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from bimddc_grid.Grid import Grid, GridLineDirection

# ============================================================
# Axis editor
# ============================================================


class AxisEditor(QWidget):
    def __init__(
        self,
        grid: Grid,
        direction: str,
        parent=None,
    ):
        super().__init__(parent)

        self.grid = grid
        self.direction = GridLineDirection(direction.upper())

        # True:
        #     reference follows the last inserted axis.
        #
        # False:
        #     user selected the reference manually
        #     (only until the next insertion).
        self.auto_reference = True

        # Actual last inserted axis.
        self.last_inserted_axis = None

        self.build_ui()
        self.build_shortcuts()
        self.refresh()

    # ========================================================
    # Helpers
    # ========================================================

    def get_axes(self):
        """Return the model axis list for this editor."""

        return getattr(
            self.grid,
            self.direction.value,
        )

    # ========================================================
    # Keep first axis at zero
    # ========================================================

    def normalize_first_axis(self):
        """
        Keep the first axis at position 0.

        If the first axis is already at zero, nothing happens.

        Otherwise all axes are translated by the same amount.
        This preserves all distances between axes.
        """

        axes = self.get_axes()

        if not axes:
            return

        first_axis = axes[0]

        offset = first_axis.pos

        if abs(offset) < 1e-12:
            first_axis.pos = 0.0
            return

        for axis in axes:
            axis.pos -= offset

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        layout = QVBoxLayout(self)

        # ----------------------------------------------------
        # Insert group
        # ----------------------------------------------------

        insert_group = QGroupBox(f"Insert {self.direction.value} Axis")

        form = QFormLayout(insert_group)

        # ----------------------------------------------------
        # Mode
        # ----------------------------------------------------

        mode_layout = QHBoxLayout()

        self.absolute_radio = QRadioButton("Absolute")
        self.relative_radio = QRadioButton("Relative")

        self.relative_radio.setChecked(True)

        mode_layout.addWidget(self.absolute_radio)

        mode_layout.addWidget(self.relative_radio)

        form.addRow(
            "Position mode:",
            mode_layout,
        )

        # ----------------------------------------------------
        # Distance
        # ----------------------------------------------------

        self.position_spin = QDoubleSpinBox()

        self.position_spin.setRange(
            -1_000_000.0,
            1_000_000.0,
        )

        self.position_spin.setDecimals(3)
        self.position_spin.setSingleStep(0.1)

        form.addRow(
            "Distance:",
            self.position_spin,
        )

        # ----------------------------------------------------
        # Reference
        # ----------------------------------------------------

        self.reference_combo = QComboBox()

        form.addRow(
            "Reference axis:",
            self.reference_combo,
        )

        # ----------------------------------------------------
        # Insert
        # ----------------------------------------------------

        self.add_button = QPushButton("Insert Axis")

        self.add_button.setDefault(True)
        self.add_button.setAutoDefault(True)

        form.addRow(
            "",
            self.add_button,
        )

        layout.addWidget(insert_group)

        # ----------------------------------------------------
        # Table
        # ----------------------------------------------------

        self.table = QTableWidget()

        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels(
            [
                "Name",
                "Position",
                "Direction",
            ]
        )

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.table)

        # ----------------------------------------------------
        # Delete
        # ----------------------------------------------------

        delete_layout = QHBoxLayout()

        delete_layout.addStretch()

        self.delete_button = QPushButton("Delete Selected")

        delete_layout.addWidget(self.delete_button)

        layout.addLayout(delete_layout)

        # ----------------------------------------------------
        # Signals
        # ----------------------------------------------------

        self.absolute_radio.toggled.connect(self.update_mode)

        self.relative_radio.toggled.connect(self.update_mode)

        self.reference_combo.currentIndexChanged.connect(self.reference_changed)

        self.add_button.clicked.connect(self.insert_axis)

        self.delete_button.clicked.connect(self.delete_axis)

    # ========================================================
    # Keyboard shortcuts
    # ========================================================

    def build_shortcuts(self):

        # ----------------------------------------------------
        # Return
        # ----------------------------------------------------

        self.enter_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Return),
            self,
        )

        self.enter_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)

        self.enter_shortcut.activated.connect(self.insert_axis)

        # ----------------------------------------------------
        # Numpad Enter
        # ----------------------------------------------------

        self.numpad_enter_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Enter),
            self,
        )

        self.numpad_enter_shortcut.setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )

        self.numpad_enter_shortcut.activated.connect(self.insert_axis)

    # ========================================================
    # Mode
    # ========================================================

    def update_mode(self, checked):

        if not checked:
            return

        # ----------------------------------------------------
        # Absolute
        # ----------------------------------------------------

        if self.absolute_radio.isChecked():
            self.reference_combo.setEnabled(False)

            return

        # ----------------------------------------------------
        # Relative
        # ----------------------------------------------------

        self.reference_combo.setEnabled(bool(self.get_axes()))

        self.auto_reference = True

        self.set_reference_to_last()

    # ========================================================
    # Reference changed manually
    # ========================================================

    def reference_changed(self, index):

        if index < 0:
            return

        # Ignore changes generated internally.
        if self.reference_combo.signalsBlocked():
            return

        # User explicitly selected a reference.
        # This is only valid until the next insertion.
        self.auto_reference = False

    # ========================================================
    # Set reference
    # ========================================================

    def set_reference(self, axis):

        if axis is None:
            return

        name = str(axis.name)

        index = self.reference_combo.findText(name)

        if index < 0:
            return

        self.reference_combo.blockSignals(True)

        self.reference_combo.setCurrentIndex(index)

        self.reference_combo.blockSignals(False)

    # ========================================================
    # Set reference to last inserted axis
    # ========================================================

    def set_reference_to_last(self):

        axes = self.get_axes()

        # ----------------------------------------------------
        # Last inserted axis still exists
        # ----------------------------------------------------

        if self.last_inserted_axis is not None and self.last_inserted_axis in axes:
            self.set_reference(self.last_inserted_axis)

            return

        # ----------------------------------------------------
        # Last inserted axis was deleted.
        #
        # Use the last existing axis.
        # ----------------------------------------------------

        if axes:
            self.last_inserted_axis = axes[-1]

            self.set_reference(self.last_inserted_axis)

            return

        # ----------------------------------------------------
        # No axes
        # ----------------------------------------------------

        self.reference_combo.clear()

        self.last_inserted_axis = None

    # ========================================================
    # Insert
    # ========================================================

    def insert_axis(self):

        distance = self.position_spin.value()

        axes_before = self.get_axes()

        try:
            # =================================================
            # First axis
            # =================================================
            #
            # The first axis must ALWAYS be at zero.
            #
            # Even if the user enters another distance,
            # the first axis is created at 0.
            # =================================================

            if not axes_before:
                axis = self.grid.insert_by_pos(
                    self.direction,
                    0.0,
                )

            # =================================================
            # Absolute insertion
            # =================================================

            elif self.absolute_radio.isChecked():
                axis = self.grid.insert_by_pos(
                    self.direction,
                    distance,
                )

            # =================================================
            # Relative insertion
            # =================================================

            else:
                reference = self.reference_combo.currentText()

                if not reference:
                    return

                axis = self.grid.insert_relative(
                    self.direction,
                    reference,
                    distance,
                )

        except ValueError as error:
            print(f"Grid insertion error: {error}")

            return

        # ----------------------------------------------------
        # Make sure first axis remains zero.
        # ----------------------------------------------------

        self.normalize_first_axis()

        # ----------------------------------------------------
        # Remember actual returned axis.
        # ----------------------------------------------------

        self.last_inserted_axis = axis

        # ----------------------------------------------------
        # After EVERY insertion the reference must go back
        # to the last inserted axis, even if the user chose
        # another reference manually before inserting.
        # ----------------------------------------------------

        self.auto_reference = True

        # ----------------------------------------------------
        # Refresh (rebuilds combo and selects last inserted)
        # ----------------------------------------------------

        self.refresh()

        # ----------------------------------------------------
        # Reset distance
        # ----------------------------------------------------

        self.position_spin.setValue(0.0)

        self.position_spin.setFocus()

        self.position_spin.selectAll()

    # ========================================================
    # Delete
    # ========================================================

    def delete_axis(self):

        row = self.table.currentRow()

        if row < 0:
            return

        axes = self.get_axes()

        if row >= len(axes):
            return

        # ----------------------------------------------------
        # Get the actual selected axis.
        # ----------------------------------------------------

        deleted_axis = axes[row]

        # ----------------------------------------------------
        # DELETE IT FOR REAL, through the model's own API.
        #
        # There is NO special protection for row 0.
        # Therefore the zero axis can be deleted normally.
        # ----------------------------------------------------

        self.grid.delete_line_by_name(
            self.direction,
            deleted_axis.name,
        )

        # ----------------------------------------------------
        # If the deleted axis was the last inserted axis,
        # invalidate that reference.
        # ----------------------------------------------------

        if self.last_inserted_axis is deleted_axis:
            self.last_inserted_axis = None

        # ----------------------------------------------------
        # If axes remain, make the new first axis zero.
        #
        # Example:
        #
        # Before:
        #
        # 0      4      8
        # |------|------|
        #
        # Delete 0:
        #
        # 4      8
        #
        # Normalize:
        #
        # 0      4
        # |------|------|
        #
        # The distance between axes is preserved.
        # ----------------------------------------------------

        self.normalize_first_axis()

        # ----------------------------------------------------
        # Refresh
        # ----------------------------------------------------

        self.refresh()

    # ========================================================
    # Refresh
    # ========================================================

    def refresh(self):

        axes = self.get_axes()

        # ----------------------------------------------------
        # Guarantee first axis at zero.
        # ----------------------------------------------------

        self.normalize_first_axis()

        # Re-read because positions may have changed.
        axes = self.get_axes()

        # ----------------------------------------------------
        # Table
        # ----------------------------------------------------

        self.table.setRowCount(len(axes))

        for row, axis in enumerate(axes):
            self.table.setItem(
                row,
                0,
                QTableWidgetItem(str(axis.name)),
            )

            self.table.setItem(
                row,
                1,
                QTableWidgetItem(f"{axis.pos:.3f}"),
            )

            self.table.setItem(
                row,
                2,
                QTableWidgetItem(axis.direction.value),
            )

        # ----------------------------------------------------
        # Save current reference
        # ----------------------------------------------------

        old_reference = self.reference_combo.currentText()

        # ----------------------------------------------------
        # Rebuild reference combo
        # ----------------------------------------------------

        self.reference_combo.blockSignals(True)

        self.reference_combo.clear()

        for axis in axes:
            self.reference_combo.addItem(str(axis.name))

        # ====================================================
        # Automatic reference: always the last inserted axis
        # ====================================================

        if self.auto_reference:
            if self.last_inserted_axis is not None and self.last_inserted_axis in axes:
                index = self.reference_combo.findText(str(self.last_inserted_axis.name))

                if index >= 0:
                    self.reference_combo.setCurrentIndex(index)

            elif axes:
                # Last inserted axis no longer exists.
                self.last_inserted_axis = axes[-1]

                self.reference_combo.setCurrentIndex(self.reference_combo.count() - 1)

        # ====================================================
        # Manual reference (e.g. after a deletion)
        # ====================================================

        else:
            index = self.reference_combo.findText(old_reference)

            if index >= 0:
                self.reference_combo.setCurrentIndex(index)

            elif self.reference_combo.count():
                self.reference_combo.setCurrentIndex(0)

        self.reference_combo.blockSignals(False)

        # ----------------------------------------------------
        # Enable / disable reference
        # ----------------------------------------------------

        self.reference_combo.setEnabled(self.relative_radio.isChecked() and bool(axes))

        # ----------------------------------------------------
        # Resize
        # ----------------------------------------------------

        self.table.resizeColumnsToContents()

    # ========================================================
    # Get selected axis
    # ========================================================

    def get_selected_axis(self):

        row = self.table.currentRow()

        if row < 0:
            return None

        axes = self.get_axes()

        if row >= len(axes):
            return None

        return axes[row]


# ============================================================
# Grid dialog
# ============================================================


class GridDialog(QDialog):
    """
    Dialog that edits a Grid.

    It never mutates the Grid instance passed in. Instead it
    works on a deep copy, and the caller only gets that copy
    back (via get_grid()) if the dialog was accepted.

    If the dialog is rejected/closed, the original instance
    is left completely untouched.
    """

    def __init__(
        self,
        grid: Grid,
        parent=None,
    ):

        super().__init__(parent)

        self.setWindowTitle("Create Structural Grid")

        self.resize(
            750,
            600,
        )

        # ----------------------------------------------------
        # Keep the original untouched, edit a deep copy.
        # ----------------------------------------------------

        self.original_grid = grid
        self.grid = grid.model_copy(deep=True)

        self.build_ui()

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        layout = QVBoxLayout(self)

        # ----------------------------------------------------
        # Tabs
        # ----------------------------------------------------

        self.tabs = QTabWidget()

        self.x_editor = AxisEditor(
            self.grid,
            "x",
        )

        self.y_editor = AxisEditor(
            self.grid,
            "y",
        )

        self.z_editor = AxisEditor(
            self.grid,
            "z",
        )

        self.tabs.addTab(
            self.x_editor,
            "X Axes",
        )

        self.tabs.addTab(
            self.y_editor,
            "Y Axes",
        )

        self.tabs.addTab(
            self.z_editor,
            "Z Levels",
        )

        layout.addWidget(self.tabs)

        # ----------------------------------------------------
        # Dialog buttons
        # ----------------------------------------------------

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        self.buttons.accepted.connect(self.accept)

        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)

    # ========================================================
    # Result
    # ========================================================

    def get_grid(self) -> Grid:
        """
        Return the modified grid.

        Only meaningful after exec() returned True (i.e. the
        user pressed OK). The original grid passed to the
        constructor is never modified either way.
        """

        return self.grid


# ============================================================
# Example
# ============================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    original_grid = Grid()

    dialog = GridDialog(original_grid)

    if dialog.exec():
        result = dialog.get_grid()

        print("Accepted. Grid:")
        print("X =", result.X)
        print("Y =", result.Y)
        print("Z =", result.Z)
    else:
        print("Cancelled. Original grid left untouched:")
        print("X =", original_grid.X)
        print("Y =", original_grid.Y)
        print("Z =", original_grid.Z)

    sys.exit(app.exec())
