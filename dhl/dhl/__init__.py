from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from dhl.views.main_views import bp as main_bp

db = SQLAlchemy()


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    # 설정 적용
    if config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_object(config)

    ## db instance initialize
    db.init_app(app)

    # 블루프린트 등록
    app.register_blueprint(main_bp)

    return app