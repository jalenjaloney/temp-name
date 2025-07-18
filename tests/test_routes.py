from tests.base import BaseTestCase


class RouteTest(BaseTestCase):
    def test_catalogue_page(self):
        # GET request to home (catalogue) page should succeed and show site
        # name
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"STAMPER", response.data)
