import math


class GridUtils:
    @staticmethod
    def find_axe_by_pos(
        grid: "Grid",
        dir: str,
        pos: float,
    ):
        for axis in getattr(grid, dir):
            if axis.pos == pos:
                return axis

        return None

    @staticmethod
    def find_axe_by_name(
        grid: "Grid",
        dir: str,
        name: str | None,
    ):
        for axis in getattr(grid, dir):
            if axis.name == name:
                return axis

        return None

    @classmethod
    def gen_new_name(
        cls,
        grid: "Grid",
        dir: str,
        pos: float | None = None,
    ) -> str:
        if dir == "X":
            max_index = max(
                (
                    int(axis.name)
                    for axis in grid.X
                    if axis.name is not None and axis.name.isdigit()
                ),
                default=-1,
            )

            return str(max_index + 1)

        if dir == "Y":
            max_index = max(
                (
                    cls._label_to_index(axis.name)
                    for axis in grid.Y
                    if cls._is_valid_alphabet_label(axis.name)
                ),
                default=-1,
            )

            return cls._index_to_label(max_index + 1)

        if dir == "Z":
            if pos is None:
                raise ValueError("pos is required when generating a Z axis name")

            return str(pos)

        raise ValueError(f"Unsupported grid direction: {dir}")

    @staticmethod
    def _index_to_label(index: int) -> str:
        result = ""

        index += 1

        while index:
            index, remainder = divmod(index - 1, 26)
            result = chr(65 + remainder) + result

        return result

    @staticmethod
    def _label_to_index(label: str) -> int:
        index = 0

        for char in label.upper():
            index = index * 26 + (ord(char) - ord("A") + 1)

        return index - 1

    @staticmethod
    def _is_valid_alphabet_label(
        value: str | None,
    ) -> bool:
        if not isinstance(value, str):
            return False

        value = value.strip().upper()

        if not value:
            return False

        return value.isalpha() and value.isascii()
