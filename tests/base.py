import os
import unittest
from sqlalchemy import text
from app.query_db import create_media_db
from app.flask_app import app, db
from app.models import User

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        app.config["MEDIA_DB_PATH"] = os.path.abspath("media.db")
        create_media_db(app.config["MEDIA_DB_PATH"])
        # Enable test mode, turn off CSRF, use in-memory DB
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app = app.test_client()

        # Init tables before each test
        with app.app_context():
            db.create_all()

    def tearDown(self):
        # Drop tables after each test
        with app.app_context():
            db.drop_all()