from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from dhl.config import TestConfig
from dhl.views.main_views import bp as main_bp

import logging


db = SQLAlchemy()
migrate = Migrate()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app(configuration=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    # 설정 적용
    if configuration is None:
        app.config.from_object(TestConfig)
    else:
        app.config.from_object(configuration)

    # 블루프린트 등록
    app.register_blueprint(main_bp)

    ## db instance initialize
    db.init_app(app)
    migrate.init_app(app, db)
    from . import models

    return app