from flask import Blueprint

bp = Blueprint('main', __name__)

@bp.route('/')
def hello_dhl():
    return 'Hello, DHL!'