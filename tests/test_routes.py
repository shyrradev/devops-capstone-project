"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL, json=account.serialize(), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL, json=account.serialize(), content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_read_account(self):
        """It should read every persisted account field."""
        account = self._create_accounts(1)[0]
        response = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), account.serialize())

    def test_read_missing_account(self):
        """It should return 404 for an unknown account."""
        self.assertEqual(self.client.get(f"{BASE_URL}/0").status_code, 404)

    def test_list_accounts(self):
        """It should list all accounts and handle an empty database."""
        self.assertEqual(self.client.get(BASE_URL).get_json(), [])
        accounts = self._create_accounts(3)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 3)
        self.assertEqual(
            {item["id"] for item in response.get_json()},
            {account.id for account in accounts},
        )

    def test_update_account(self):
        """It should persist updates without changing the identifier."""
        account = self._create_accounts(1)[0]
        data = account.serialize()
        data["name"] = "Updated Customer"
        response = self.client.put(f"{BASE_URL}/{account.id}", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), data)
        self.assertEqual(self.client.get(f"{BASE_URL}/{account.id}").get_json(), data)

    def test_update_missing_account(self):
        """It should reject updates to unknown accounts."""
        response = self.client.put(f"{BASE_URL}/0", json=AccountFactory().serialize())
        self.assertEqual(response.status_code, 404)

    def test_update_invalid_account(self):
        """It should reject malformed updates."""
        account = self._create_accounts(1)[0]
        url = f"{BASE_URL}/{account.id}"
        self.assertEqual(self.client.put(url, json={}).status_code, 400)
        self.assertEqual(
            self.client.put(url, data="bad", content_type="text/plain").status_code, 415
        )

    def test_delete_account(self):
        """It should delete accounts and allow repeated deletion."""
        account = self._create_accounts(1)[0]
        url = f"{BASE_URL}/{account.id}"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b"")
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(BASE_URL).get_json(), [])

    def test_security_headers(self):
        """It should include Talisman security headers."""
        response = self.client.get("/health")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")
        self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])

    def test_cors(self):
        """It should permit noncredentialed cross-origin API calls."""
        response = self.client.get(BASE_URL, headers={"Origin": "https://example.org"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"], "https://example.org"
        )
        response = self.client.options(
            BASE_URL,
            headers={
                "Origin": "https://example.org",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("POST", response.headers["Access-Control-Allow-Methods"])
