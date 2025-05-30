from flask import Blueprint

bp = Blueprint('main', __name__)

@bp.get('/')
def hello_dhl():
    return 'Hello, DHL!'