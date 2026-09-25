from enum import StrEnum

from pydantic import BaseModel, Field

from bimddc_grid.GridUtils import GridUtils


class GridLineDirection(StrEnum):
    X = "X"
    Y = "Y"
    Z = "Z"


class GridLine(BaseModel):
    direction: GridLineDirection
    name: str | None = None
    pos: float


class Grid(BaseModel):
    X: list[GridLine] = Field(default_factory=list)
    Y: list[GridLine] = Field(default_factory=list)
    Z: list[GridLine] = Field(default_factory=list)

    def insert_by_pos(
        self,
        dir: GridLineDirection,
        pos: float,
    ) -> GridLine:
        self.ensure_first_axe(dir)

        exists = GridUtils.find_axe_by_pos(
            self,
            dir=dir,
            pos=pos,
        )

        if exists is not None:
            return exists

        line = GridLine(
            direction=dir,
            pos=pos,
            name=GridUtils.gen_new_name(
                self,
                dir=dir,
                pos=pos,
            ),
        )

        getattr(self, dir.value).append(line)

        return line

    def insert_relative(
        self,
        dir: GridLineDirection,
        name: str,
        distance: float,
    ) -> GridLine:
        """
        Insert a new grid axis at a relative distance from an
        existing axis.

        Parameters
        ----------
        dir:
            Direction of the grid axis.

        name:
            Name of the reference axis.

        distance:
            Relative distance from the reference axis.

            Positive value:
                reference position + distance

            Negative value:
                reference position - distance

        Returns
        -------
        GridLine
            The existing or newly created grid axis.

        Raises
        ------
        ValueError
            If the reference axis does not exist.
        """

        self.ensure_first_axe(dir)

        lines = getattr(self, dir.value)

        reference = next(
            (line for line in lines if line.name == name),
            None,
        )

        if reference is None:
            raise ValueError(
                f"Grid axis '{name}' does not exist in direction '{dir.value}'."
            )

        new_pos = reference.pos + distance

        return self.insert_by_pos(
            dir=dir,
            pos=new_pos,
        )

    def ensure_first_axe(
        self,
        dir: GridLineDirection,
    ) -> GridLine:
        exists = GridUtils.find_axe_by_pos(
            self,
            dir=dir,
            pos=0.0,
        )

        if exists is not None:
            return exists

        first_axe = GridLine(
            direction=dir,
            name={
                GridLineDirection.X: "0",
                GridLineDirection.Y: "A",
                GridLineDirection.Z: "0.0",
            }[dir],
            pos=0.0,
        )

        getattr(self, dir.value).append(first_axe)

        return first_axe

    def delete_line_by_name(
        self,
        dir: GridLineDirection,
        name: str,
    ) -> None:
        lines = getattr(self, dir.value)

        index = next(
            (i for i, line in enumerate(lines) if line.name == name),
            None,
        )

        if index is not None:
            lines.pop(index)

    def delete_line_by_pos(
        self,
        dir: GridLineDirection,
        pos: float,
    ) -> None:
        lines = getattr(self, dir.value)

        index = next(
            (i for i, line in enumerate(lines) if line.pos == pos),
            None,
        )

        if index is not None:
            lines.pop(index)
        self.ensure_first_axe(dir)
