import enum


@enum.unique()
class HanabiColour(enum.Enum):
    Red = enum.auto()
    Green = enum.auto()
    White = enum.auto()
    Yellow = enum.auto()
    Blue = enum.auto()


class HanabiCard:
    def __str__(self):
        return "{} {}".format(self.rank, self.colour)

    def __init__(self):
        self.colour = None
        self.rank = None

