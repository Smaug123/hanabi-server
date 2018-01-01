"""
Utility functions for storing and retrieving Hanabi server data.
"""

import yaml


# Field names for each field
_players = "players"
_hands = "hands"
_discards = "discards"
_knowledge = "knowledge"
_lives = "lives"

_fieldnames = [_players, _hands, _discards, _knowledge, _lives]


class GameDataStore:
    """
    Store complete information about a Hanabi game in a file.
    """

    def __init__(self, path):
        self.filepath = path

    def get(self):
        with open(self.filepath) as f:
            data = yaml.safe_load(f)
        return data

    def replace(self, data):
        with open(self.filepath) as f:
            yaml.dump(data, f)

    def replace_field(self, field, data):
        existing = self.get()
        existing[field] = data
        self.replace(existing)

    def append_to_field(self, field, data):
        existing = self.get()
        existing[field].append(data)
        self.replace(existing)

    def add_player(self, player_name):
        self.append_to_field(_players, player_name)

    def create(self, players):
        """
        Create a new Hanabi game, storing the data in the given file.
        :return:
        """
        data = {_players: players,
                _hands: [],
                _discards: [],
                _knowledge: {"used": 0, "available": 8},
                _lives: {"used": 0, "available": 3}}
        self.replace(data)
