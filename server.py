import flask_limiter.util

from flask import Flask
from flask_limiter import Limiter
from flask_restful import Api

import HanabiWeb.hanabi


app = Flask(__name__)
api = Api(app)
limiter = Limiter(app,
                  key_func=flask_limiter.util.get_remote_address,
                  default_limits=["300 per day", "10 per minute"])


HanabiWeb.hanabi.Game.method_decorators.append(limiter.limit("2 per minute"))
api.add_resource(HanabiWeb.hanabi.Game,
                 '/game',
                 '/game/<int:game_id>',
                 '/game/<int:game_id>/<string:player>')

HanabiWeb.hanabi.Discard.method_decorators.append(limiter.limit("5 per minute"))
api.add_resource(HanabiWeb.hanabi.Discard,
                 '/discard/<int:game_id>/<string:player>')

HanabiWeb.hanabi.PlayCard.method_decorators.append(limiter.limit("5 per minute"))
api.add_resource(HanabiWeb.hanabi.PlayCard,
                 '/play/<int:game_id>/<string:player>')

HanabiWeb.hanabi.Inform.method_decorators.append(limiter.limit("5 per minute"))
api.add_resource(HanabiWeb.hanabi.Inform,
                 '/inform/<int:game_id>/<string:player>')

HanabiWeb.hanabi.History.method_decorators.append(limiter.limit('5 per minute'))
api.add_resource(HanabiWeb.hanabi.History,
                 '/history/<int:game_id>')

if __name__ == "__main__":
    app.run(debug=True)

