"""
Utility functions for storing and retrieving Hanabi server data.
"""

import yaml

from . import card


# Field names for each field
players_key = "players"
hands_key = "hands"
discards_key = "discards"
knowledge_key = "knowledge"
lives_key = "lives"
deck_key = "deck"
played_key = "played"

_fieldnames = (players_key,
               hands_key,
               discards_key,
               knowledge_key,
               lives_key,
               played_key,
               deck_key)


class GameDataStore:
    """
    Store complete information about a Hanabi game in a file.
    """

    def __init__(self, path):
        self.filepath = path

    def get(self):
        with open(self.filepath) as f:
            data = yaml.load(f)
        return data

    def get_from_perspective(self, player):
        """
        Get the state of the game as seen by the given player.
        """
        data = self.get()
        if player not in data[players_key]:
            err = "Player {} not in player list for this game.".format(player)
            raise ValueError(err)
        # The given player can't see their own hand, or the deck, but can see
        # everything else.
        del data[hands_key][player]
        del data[deck_key]
        return data

    def replace(self, data):
        with open(self.filepath, "w") as f:
            yaml.dump(data, f)

    def replace_field(self, field, data):
        existing = self.get()
        existing[field] = data
        self.replace(existing)

    def create(self, players):
        """
        Create a new Hanabi game, storing the data in the given file.
        """
        deck_arrangement = card.get_deck_arrangement()
        data = {players_key: players,
                hands_key: {p: [] for p in players},
                discards_key: [],
                knowledge_key: {"used": 0, "available": 8},
                lives_key: {"used": 0, "available": 3},
                deck_key: deck_arrangement,
                played_key: []}

        # Deal out the cards
        if len(players) == 2 or len(players) == 3:
            cards_per_person = 5
        elif len(players) == 4 or len(players) == 5:
            cards_per_person = 4

        for p in players:
            for _ in range(cards_per_person):
                data[hands_key][p].append(data[deck_key].pop())

        self.replace(data)
