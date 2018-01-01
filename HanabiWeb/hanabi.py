import os
import re

from flask import Flask
from flask_restful import Resource, Api, abort

from . import hanabi_cache

app = Flask(__name__)
api = Api(app)


_DATA_STORES = os.path.join(os.path.expanduser('~'), '.hanabigames')


def _validate_game_id(game_id):
    """
    Test whether a game ID is valid. If it is not, raise a 403 Forbidden.
    """
    try:
        int(str(game_id))
    except ValueError:
        abort(403, message="Malformed game ID {}".format(game_id))


def _game_data_path(game_id):
    """
    Find the path to the data file for a given game.

    This fully trusts game_id, and is not safe on unsanitised input.
    """
    return os.path.join(_DATA_STORES, "{}.dat".format(game_id))


def ls(directory):
    onlyfiles = [f
                 for f in os.listdir(directory)
                 if os.path.isfile(os.path.join(directory, f))]
    return onlyfiles


def _get_new_game_index():
    files = ls(_DATA_STORES)
    indices = [int(name.rstrip('.dat'))
               for name in files
               if re.match(r"[0-9]+\.dat$", name)]
    if not indices:
        return 0
    indices.sort()
    return indices[-1] + 1


class Hand(Resource):
    def get(self, game_id, player_id):
        return {'hello': 'world'}


class Play(Resource):
    def post(self, game_id, player_id, card):
        pass


class Game(Resource):
    def get(self, game_id, player_id=None):
        """
        Return the state of the game as viewed by the given player.

        If no player is specified, return the state of the game as viewed by a
        spectator.

        :param game_id: Lookup ID for the given game.
        :param player_id: Lookup ID for a certain player in this game.
        :return: Dictionary of game state.
            {players: [players],
             hands: {player1: [cards], player2: [cards]},
             discards: [cards],
             knowledge: {used: 5, available: 3},
             lives: {used: 0, available: 3}}
        """
        _validate_game_id(game_id)
        data_path = _game_data_path(game_id)

        data = hanabi_cache.GameDataStore(data_path)

        if player_id is None:
            return data.get()

    def put(self, players):
        """
        Create a new game, returning the game ID.
        """
        new_id = _get_new_game_index()
        data_path = _game_data_path(new_id)
        data = hanabi_cache.GameDataStore(data_path)
        data.create(players)


api.add_resource(Hand, '/hanabi')


@app.route("/hanabi")
def hello():
    return "Hello, World!"

if __name__ == "__main__":
    app.run(debug=True)