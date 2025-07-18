from tests.base import BaseTestCase
from app.models import User
from app.flask_app import db


class AuthTest(BaseTestCase):
    # Helper method to register user
    def register_user(self, username="testuser", password="Password123"):
        return self.app.post(
            "/register",
            data=dict(username=username, password=password,
                      confirm_password=password),
            follow_redirects=True,
        )

    # Helper method to log in user
    def login_user(self, username="testuser", password="Password123"):
        return self.app.post(
            "/login",
            data=dict(username=username, password=password),
            follow_redirects=True,
        )

    # Helper method to log out current user
    def logout_user(self):
        return self.app.get("/logout", follow_redirects=True)

    # Make sure register page loads properly
    def test_register_page_loads(self):
        response = self.app.get("/register")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Register", response.data)

    # Test a user can register and gets right success message
    def test_register_user(self):
        response = self.register_user()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Account created for testuser!", response.data)

    # Check the login page loads properly
    def test_login_page_loads(self):
        response = self.app.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Login", response.data)

    # Test a registered user can successfully log in
    def test_login_user(self):
        self.register_user()
        response = self.login_user()
        self.assertIn(b"Welcome testuser", response.data)

    # Register, log in, and log out flow
    def test_register_login_logout_flow(self):
        self.register_user(username="flowuser", password="flowpass")
        response = self.login_user(username="flowuser", password="flowpass")
        self.assertIn(b"Welcome flowuser", response.data)

        response = self.logout_user()
        self.assertIn(b"Login", response.data)
