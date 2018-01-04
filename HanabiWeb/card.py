import enum
import random


@enum.unique
class HanabiColour(enum.Enum):
    Red = 1
    Green = 2
    White = 3
    Yellow = 4
    Blue = 5


class HanabiCard(dict):
    def __str__(self):
        return "{} {}".format(self['rank'], self['colour'])

    def __repr__(self):
        return "HanabiCard({}, {})".format(self.get('colour'), self.get('rank'))

    def __init__(self, colour=None, rank=None):
        dict.__init__(self)
        self['colour'] = colour
        self['rank'] = rank


def _random_derangement(n):
    """
    Return a tuple random derangement of (0, 1, 2, ..., n-1).
    """
    while True:
        v = list(range(n))
        for j in range(n - 1, -1, -1):
            p = random.randint(0, j)
            if v[p] == j:
                break
            else:
                v[j], v[p] = v[p], v[j]
        else:
            if v[0] != 0:
                return tuple(v)


def get_deck_arrangement():
    """
    Return a derangement of the cards in the deck.
    """
    deck_length = (3 + 2 * 3 + 1) * 5
    all_cards = [HanabiCard(colour=c, rank=r)
                 for c in HanabiColour.__members__
                 for r in range(1, 6)]
    all_cards.extend([HanabiCard(colour=c, rank=r)
                      for c in HanabiColour.__members__
                      for r in range(1, 5)])
    all_cards.extend([HanabiCard(colour=c, rank=1)
                      for c in HanabiColour.__members__])
    derangement = _random_derangement(deck_length)
    return [all_cards[i] for i in derangement]