from tests.base import BaseTestCase
from app.models import Comment
from app.flask_app import app


class CommentTest(BaseTestCase):
    def register_and_login(self, username="testuser", password="Password123"):
        self.app.post(
            "/register",
            data=dict(username=username, password=password,
                      confirm_password=password),
            follow_redirects=True,
        )
        self.app.post(
            "/login",
            data=dict(username=username, password=password),
            follow_redirects=True,
        )

    def test_add_comment_logged_in(self):
        self.register_and_login()

        response = self.app.post(
            "/movie/1087192",
            data=dict(timestamp="00:01:23", content="Test comment!"),
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test comment!", response.data)

    def test_add_comment_invalid_timestamp(self):
        self.register_and_login()

        response = self.app.post(
            "/movie/1087192",
            data=dict(timestamp="bad input", content="Should not work"),
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Use HH:MM:SS or MM:SS format", response.data)

    def test_add_comment_empty_content(self):
        self.register_and_login()

        response = self.app.post(
            "/movie/1087192",
            data=dict(timestamp="00:00:10", content=""),
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"This field is required", response.data)

    def test_delete_own_comment(self):
        self.register_and_login()

        # Post comment
        self.app.post(
            "/movie/1087192",
            data=dict(timestamp="00:00:05", content="Delete me"),
            follow_redirects=True,
        )

        # Grab comment ID from database
        with app.app_context():
            comment = Comment.query.filter_by(content="Delete me").first()
            self.assertIsNotNone(comment)
            comment_id = comment.id

        # Delete comment
        response = self.app.post(
            f"/comment/{comment_id}/delete", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Delete me", response.data)

    def test_cannot_delete_others_comment(self):
        # User A
        self.register_and_login(username="userA")
        self.app.post(
            "/movie/1087192",
            data=dict(timestamp="00:00:10", content="User A comment"),
            follow_redirects=True,
        )
        self.app.get("/logout", follow_redirects=True)

        # User B
        self.register_and_login(username="userB")
        with app.app_context():
            comment = Comment.query.filter_by(content="User A comment").first()
            comment_id = comment.id
        self.assertIsNotNone(comment)

        # Try to delete User A’s comment
        response = self.app.post(
            f"/comment/{comment_id}/delete", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b"You don&#39;t have permission to delete", response.data)
