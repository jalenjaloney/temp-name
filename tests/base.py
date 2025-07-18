import unittest
from sqlalchemy import text
from app.flask_app import app, db
from app.models import User

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        # Enable test mode, turn off CSRF, use in-memory DB
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app = app.test_client()

        # Init tables before each test
        with app.app_context():
            db.create_all()

            # Create media table for raw SQL access
            db.session.execute(text("""
                CREATE TABLE media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tmdb_id INTEGER,
                    media_type TEXT,
                    title TEXT
                )
            """))

            # Add dummy row to media
            db.session.execute(text("""
                INSERT INTO media (tmdb_id, media_type, title)
                VALUES (1087192, 'movie', 'Dummy Movie')
            """))
            db.session.commit()

    def tearDown(self):
        # Drop tables after each test
        with app.app_context():
            db.drop_all()