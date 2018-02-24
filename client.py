#!/usr/bin/env python3

import os
import enum

import requests

from HanabiWeb import card


def get_game_id():
    input_str = None
    while input_str is None:
        try:
            input_str = input("Please enter an integer game ID: ")
            int(input_str)
        except ValueError:
            input_str = None
    return int(input_str)


_DEFAULT_PLAYER_FILE = os.path.join(os.path.expanduser("~"),
                                    ".hanabi", "name.txt")
_DEFAULT_SERVER_FILE = os.path.join(os.path.expanduser("~"),
                                    ".hanabi", "server.txt")


def get_player():
    with open(_DEFAULT_PLAYER_FILE) as f:
        default_player = f.readlines()[0].strip()
    input_str = input("Enter your player name (default is {}): ".format(
                      default_player))
    if not input_str:
        return default_player
    return input_str


def get_server():
    with open(_DEFAULT_SERVER_FILE) as f:
        default_server = f.readlines()[0].strip()
    input_str = input("Enter the server (default is {}): ".format(
                      default_server))
    if not input_str:
        return default_server
    return input_str


def print_welcome():
    print("Hanabi client.")
    print("Command-line version. Press Ctrl+C to exit.")


class Actions(enum.Enum):
    PRINT_GAMESTATE = 0
    PLAY = 1
    DISCARD = 2
    HISTORY = 3
    ALL_HISTORY = 4
    INFORM = 5


_recognised_actions = {'print': (Actions.PRINT_GAMESTATE, 0),
                       'play': (Actions.PLAY, 1),
                       'discard': (Actions.DISCARD, 1),
                       'history': (Actions.HISTORY, 0),
                       'all_history': (Actions.ALL_HISTORY, 0),
                       'inform': (Actions.INFORM, 1)}


def get_action():
    """
    Generator yielding the actions the user takes.

    Yields e.g. ((Actions.PLAY, 1), ["inputstr"]), indicating that one of the
    elements of the list is an argument.
    """
    while True:
        words = input("Please enter your action ({}): >".format(','.join(_recognised_actions))).strip().split()
        if not words:
            continue
        if words[0] in _recognised_actions:
            act = _recognised_actions[words[0]]
            remaining = words[1:act[1]+1]
            yield (_recognised_actions[words[0]], remaining)


def request_gamestate(server, player, gameid):
    """
    Requests the current game state from the player's perspective.

    If successful, returns a dictionary as output by the REST API for the
    /game/<id>/<player> endpoint.
    """
    print("Requesting game state...")
    url = server + '/game/{id}/{player}'.format(id=gameid, player=player)
    r = requests.get('http://' + url)
    js = r.json()
    return js


def get_top(cards, colour):
    """
    Get the top card played of the given colour string.
    """
    iter = [card.rank
            for card in cards
            if card.colour.lower() == colour.lower()]

    if not iter:
        return 0
    return max(iter)


def request_history(server, game_id, player=None):
    """
    Request the history from the server from the point of view of a player.

    TODO: this API currently doesn't filter based on who is requesting. The
    server needs to be fixed to do that.
    """
    print("Requesting history...")
    url = server + '/history/{}'.format(game_id)
    if player is not None:
        url += '/{}'.format(player)
    r = requests.get('http://' + url)
    return r.json()


def print_history(history):
    """
    Print the history object retrieved from the server.
    """
    print('\n'.join(history))


def print_gamestate(state):
    cards_played = state['played']
    players = state['players']
    lives_available = state['lives']['available']
    lives_used = state['lives']['used']
    knowledge_available = state['knowledge']['available']
    knowledge_used = state['knowledge']['used']

    hands = state['hands']
    discarded = state['discards']

    print('----------------- Metadata ------------------------')
    print('Players: {}'.format(', '.join(players)))
    print('Lives: {} remaining, {} used'.format(lives_available, lives_used))
    print('Knowledge: {} remaining, {} used'.format(knowledge_available,
                                                    knowledge_used))
    print('------------------ Piles --------------------------')
    any_played = False
    for colour in card.HanabiColour:
        # Get top card of the pile
        top = get_top(cards_played, colour.name)
        if top:
            print('Top card {}: {}'.format(colour.name, top))
            any_played = True
    if not any_played:
        print("No cards played.")
    print('----------------- Discard -------------------------')
    any_discarded = False
    for colour in card.HanabiColour:
        disc = sorted([card['rank']
                       for card in discarded
                       if card['colour'].lower() == colour.name.lower()])
        if disc:
            print("Colour {}: {}".format(colour.name, disc))
            any_discarded = True
    if not any_discarded:
        print("No cards discarded.")
    print('------------------ Hands ------------------------')
    for player in sorted(players):
        if player in hands:
            hand = ['{} {}'.format(card['colour'], card['rank'])
                    for card in hands[player]]
            print('{}: {}'.format(player, ', '.join(hand)))
    print('-------------------------------------------------')


def validate_args(numargs, args):
    """
    Check that there are enough args in the list, and truncate accordingly.

    Raises ValueError if not.
    """
    if len(args) < numargs:
        raise ValueError("Not enough elements in list {}, need "
                         "{}.".format(args, numargs))

    return args


def request_discard(server, player, id, card):
    """
    Discard a card.

    The card is specified as a zero-indexed card from the left positionally in
    someone's hand.
    """
    url = server + '/discard/{id}/{player}'.format(id=id, player=player)
    r = requests.post('http://' + url, data={'card_index': card})
    return r.text


def request_play(server, player, id, card):
    """
    Play a card.

    The card is specified as a zero-indexed card from the left positionally in
    someone's hand.
    """
    url = server + '/play/{id}/{player}'.format(id=id, player=player)
    r = requests.post('http://' + url, data={'card_index': card})
    return r.text


def request_inform(server, requester, player, id, colour=None, rank=None):
    """
    Give a player information about a card.
    """
    data = {'recipient': player}
    if colour is None:
        assert(rank is not None)
        data['rank'] = rank
    if rank is None:
        assert(colour is not None)
        data['colour'] = colour.lower().capitalize()

    url = server + '/inform/{id}/{player}'.format(id=id, player=requester)
    r = requests.post('http://' + url, data=data)
    return r.text


if __name__ == '__main__':
    game_id = get_game_id()
    player = get_player()
    server = get_server()
    print_welcome()

    actions = get_action()

    while True:
        ((action, numargs), args) = next(actions)
        try:
            args = validate_args(numargs, args)
        except ValueError as e:
            print("{}".format(e))
            continue

        if action == Actions.PRINT_GAMESTATE:
            state = request_gamestate(server, player, game_id)
            print_gamestate(state)
        elif action == Actions.DISCARD:
            outcome = request_discard(server, player, game_id, args[0])
            if outcome.strip() != 'true':
                print('May have failed: {}'.format(outcome))
            state = request_gamestate(server, player, game_id)
            print_gamestate(state)
        elif action == Actions.PLAY:
            outcome = request_play(server, player, game_id, args[0])
            if outcome.strip() != 'true':
                print('May have failed: {}'.format(outcome))
            state = request_gamestate(server, player, game_id)
            print_gamestate(state)
        elif action == Actions.INFORM:
            recipient = args[0]
            which = input('Enter a colour string or a number: ')
            try:
                int(which)
            except ValueError:
                # which is a colour
                outcome = request_inform(server, player, recipient, game_id, colour=which)
            else:
                outcome = request_inform(server, player, recipient, game_id, rank=which)
            state = request_gamestate(server, player, game_id)
            print_gamestate(state)
        elif action == Actions.HISTORY:
            history = request_history(server, game_id, player=player)
            print_history(history)
        elif action == Actions.ALL_HISTORY:
            history = request_history(server, game_id)
            print_history(history)

# TODO: need to pip install requests[security] when installing this