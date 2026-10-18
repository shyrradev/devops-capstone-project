"""Configuration and error contract regression tests."""
import importlib
import os
from unittest import TestCase
from unittest.mock import patch
from service import app, config
from service.common.error_handlers import internal_server_error


class TestConfiguration(TestCase):
    """Verify environment configuration and HTTP error responses."""

    def test_database_environment(self):
        """It should assemble a PostgreSQL URI from environment settings."""
        with patch.dict(
            os.environ,
            {
                "DATABASE_USER": "customer",
                "DATABASE_PASSWORD": "example",
                "DATABASE_HOST": "database",
                "DATABASE_NAME": "accounts",
            },
            clear=True,
        ):
            importlib.reload(config)
            self.assertEqual(
                config.DATABASE_URI,
                "postgresql://customer:example@database:5432/accounts",
            )
        importlib.reload(config)

    def test_method_not_allowed(self):
        """It should reject unsupported methods with JSON."""
        response = app.test_client().patch("/accounts")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.get_json()["status"], 405)

    def test_internal_error(self):
        """It should return a structured server error response."""
        with app.app_context():
            response, code = internal_server_error("Unexpected error")
            self.assertEqual(code, 500)
            self.assertEqual(response.get_json()["error"], "Internal Server Error")
