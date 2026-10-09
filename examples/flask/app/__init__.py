from flask import Flask
from dotenv import load_dotenv

load_dotenv()

from .mpesa import mpesa  # noqa: E402  (import after load_dotenv)
from .routes import bp  # noqa: E402


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(bp)

    @app.teardown_appcontext
    def _teardown(exception=None):
        # Cancel the rate limiter's background cleanup task.
        mpesa.destroy()

    return app