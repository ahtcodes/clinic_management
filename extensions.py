from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO


# =========================================================
# DATABASE
# =========================================================

db = SQLAlchemy()


# =========================================================
# MIGRATION
# =========================================================

migrate = Migrate()


# =========================================================
# LOGIN MANAGER
# =========================================================

login_manager = LoginManager()


# =========================================================
# SOCKET.IO
# =========================================================

socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading"
)