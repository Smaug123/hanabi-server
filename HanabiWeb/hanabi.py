import os
import re

from flask_restful import Resource, abort, reqparse

from . import cache
from . import card

_DATA_STORES = os.path.join(os.path.expanduser('~'), '.hanabigames')
_EXTENSION = '.han'


_colours = card.HanabiColour.__members__.keys()


def _validate_game_id(game_id):
    """
    Test whether a game ID is valid. If it is not, raise a 403 Forbidden.
    """
    try:
        int(str(game_id))
    except ValueError:
        abort(403, message="Malformed game ID {}".format(game_id))


def _validate_game_exists(game_id):
    """
    Test whether a game exists. If not, raise 404 Not Found.

    This fully trusts game_id, and is not safe on unsanitised input.
    """
    data_path = _game_data_path(game_id)
    if not os.path.exists(data_path):
        abort(404, message="Game {} not found.".format(game_id))


def _validate_player_in_game(data, player):
    """
    Test whether the player is in the given game.
    """
    players = data[cache.players]
    if player not in players:
        abort(400,
              message="Player {} not found in game".format(player))


def _game_data_path(game_id):
    """
    Find the path to the data file for a given game.

    This fully trusts game_id, and is not safe on unsanitised input.
    """
    return os.path.join(_DATA_STORES, "{}{}".format(game_id, _EXTENSION))


def ls(directory, create=False):
    """
    List the contents of a directory, optionally creating it first.

    If create is falsy and the directory does not exist, then an exception
    is raised.
    """
    if create and not os.path.exists(directory):
        os.mkdir(directory)

    onlyfiles = [f
                 for f in os.listdir(directory)
                 if os.path.isfile(os.path.join(directory, f))]
    return onlyfiles


def _get_new_game_index():
    """
    Get an ID suitable for a new game, which does not clash with any others.
    """
    files = ls(_DATA_STORES, create=True)
    indices = [int(name.rstrip(_EXTENSION))
               for name in files
               if re.match(r"[0-9]+{}$".format(re.escape(_EXTENSION)), name)]
    if not indices:
        return 0
    indices.sort()
    return indices[-1] + 1


def _can_play(already_played, attempt_card):
    """
    Return True iff attempt_card can be played given that played are the played
    cards.
    """
    ordered_play = {c: 0 for c in card.HanabiColour.__members__}
    print(already_played)
    for c in card.HanabiColour.__members__:
        played_in_col = [p['rank'] for p in already_played if p['colour'] == c]
        if played_in_col:
            ordered_play[c] = sorted(played_in_col)[-1]

    if ordered_play[attempt_card['colour']] + 1 == attempt_card['rank']:
        return True
    return False


class Discard(Resource):
    def post(self, game_id, player):
        """
        Expects card_index as data.
        :param game_id:
        :param player:
        :return:
        """
        _validate_game_id(game_id)
        _validate_game_exists(game_id)

        data_path = _game_data_path(game_id)
        data_store = cache.GameDataStore(data_path)
        data = data_store.get()
        player_hand = data[cache.hands_key][player]

        parser = reqparse.RequestParser()
        parser.add_argument('card_index', type=int)
        args = parser.parse_args()

        if args.card_index < 0 or args.card_index >= len(player_hand):
            abort(400, message="Card {} not valid.".format(args.card_index))

        # Discard the card with given index.
        drawn_card = data[cache.deck_key].pop()
        data[cache.discards_key].append(player_hand[args.card_index])
        player_hand[args.card_index] = drawn_card
        if data[cache.knowledge_key]['used'] != 0:
            data[cache.knowledge_key]['used'] -= 1
            data[cache.knowledge_key]['available'] += 1

        data_store.replace(data)

        return True


class PlayCard(Resource):
    def post(self, game_id, player):
        """
        Expects card_index as data.
        """
        _validate_game_id(game_id)
        _validate_game_exists(game_id)

        data_path = _game_data_path(game_id)
        data_store = cache.GameDataStore(data_path)
        data = data_store.get()
        player_hand = data[cache.hands_key][player]

        parser = reqparse.RequestParser()
        parser.add_argument('card_index', type=int)
        args = parser.parse_args()

        if args.card_index < 0 or args.card_index >= len(player_hand):
            abort(400, message="Card {} not valid.".format(args.card_index))

        # Play the card with given index.
        card_to_play = player_hand[args.card_index]
        if _can_play(data[cache.played_key], card_to_play):
            data[cache.played_key].append(player_hand[args.card_index])
            retval = True
        else:
            retval = False
            data[cache.discards_key].append(player_hand[args.card_index])
            if data[cache.lives_key]["available"] > 0:
                data[cache.lives_key]["used"] += 1
                data[cache.lives_key]["available"] -= 1
            if data[cache.lives_key]["available"] <= 0:
                return "All lives exhausted. Game over."

        drawn_card = data[cache.deck_key].pop()
        player_hand[args.card_index] = drawn_card

        data_store.replace(data)

        return retval


class Game(Resource):
    def get(self, game_id, player=None):
        """
        Return the state of the game as viewed by the given player.

        If no player is specified, return the state of the game as viewed by a
        spectator.

        :param game_id: Lookup ID for the given game.
        :param player: Lookup ID for a certain player in this game.
        :return: Dictionary of game state.
            {players: [players],
             hands: {player1: [cards], player2: [cards]},
             discards: [cards],
             knowledge: {used: 5, available: 3},
             lives: {used: 0, available: 3}}
        """
        _validate_game_id(game_id)
        _validate_game_exists(game_id)

        data_path = _game_data_path(game_id)
        data = cache.GameDataStore(data_path)

        if player is None:
            return data.get()

        return data.get_from_perspective(player)

    def put(self):
        """
        Create a new game, returning the game ID.
        """
        parser = reqparse.RequestParser()
        parser.add_argument('players', type=str,
                            help='Player names, comma-separated')
        args = parser.parse_args()

        new_id = _get_new_game_index()
        data_path = _game_data_path(new_id)
        data = cache.GameDataStore(data_path)
        data.create(args['players'].split(','))

        return {'id': new_id}


