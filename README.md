# bimddc_grid
# Install : 
```bash
pip install git+https://github.com/issam-mhadhbi/bimddc-grid.git
```
## Usage : 
```python
import sys

from PySide6.QtWidgets import QApplication

from bimddc_grid import Grid, GridDialog, GridLineDirection , GridUtils

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
``
