import pytest

from app.db.database import connect, initialize
from app.db.seed import seed_demo_data


@pytest.fixture
def demo_db(tmp_path):
    connection = connect(f"sqlite:///{tmp_path / 'test.sqlite3'}")
    initialize(connection)
    seed_demo_data(connection)
    yield connection
    connection.close()
