from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from dhl.config import LocalConfig
from dhl.views.main_views import bp as main_bp

db = SQLAlchemy()

def create_app(configuration=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    # 설정 적용
    if configuration is None:
        app.config.from_object(LocalConfig)
    else:
        app.config.from_object(configuration)

    ## db instance initialize
    db.init_app(app)

    # 블루프린트 등록
    app.register_blueprint(main_bp)

    return app