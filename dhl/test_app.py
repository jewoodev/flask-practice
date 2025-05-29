from dhl import create_app
from dhl.config import TestConfig

app = create_app(TestConfig)