import logging

from flask import current_app

logging = logging.getLogger(__name__)

class CommonFunc:

    @staticmethod
    def get_config_val(str_key):
        if current_app.config[str_key]:
            return current_app.config[str_key]
        else:
            return None