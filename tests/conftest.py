import os

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as requiring MQTT broker"
    )


@pytest.fixture(autouse=True)
def load_env():
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))
