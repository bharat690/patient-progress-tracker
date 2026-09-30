import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.auth import password_login_disabled, password_registration_disabled
from app.db.postgres import Base
from app.models.user import User
from app.services.google_auth import (
    GoogleAccountConflict,
    GoogleAuthNotConfigured,
    InvalidGoogleCredential,
    authenticate_google_user,
)


class GoogleAuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_creates_a_google_user_without_a_password(self):
        claims = {
            "sub": "google-user-1",
            "email": "New.User@example.com",
            "email_verified": True,
            "name": "New User",
        }

        with patch(
            "app.services.google_auth.id_token.verify_oauth2_token",
            return_value=claims,
        ) as verify:
            user = authenticate_google_user(
                self.session,
                "verified-id-token",
                "google-client-id",
            )

        self.assertEqual(user.email, "new.user@example.com")
        self.assertEqual(user.google_subject, "google-user-1")
        self.assertEqual(user.name, "New User")
        self.assertEqual(user.role, "doctor")
        self.assertTrue(user.is_active)
        self.assertIsNone(user.password_hash)
        verify.assert_called_once()
        self.assertEqual(verify.call_args.args[0], "verified-id-token")
        self.assertEqual(verify.call_args.args[2], "google-client-id")

    def test_links_existing_account_by_verified_email_and_preserves_user_id(self):
        existing = User(
            name="Existing User",
            email="existing@example.com",
            password_hash="legacy-hash",
            role="doctor",
            is_active=True,
        )
        self.session.add(existing)
        self.session.commit()
        existing_id = existing.id
        claims = {
            "sub": "google-user-2",
            "email": "EXISTING@example.com",
            "email_verified": True,
            "name": "Google Display Name",
        }

        with patch(
            "app.services.google_auth.id_token.verify_oauth2_token",
            return_value=claims,
        ):
            user = authenticate_google_user(
                self.session,
                "verified-id-token",
                "google-client-id",
            )

        self.assertEqual(user.id, existing_id)
        self.assertEqual(user.google_subject, "google-user-2")
        self.assertEqual(user.name, "Existing User")
        self.assertEqual(user.password_hash, "legacy-hash")

    def test_rejects_unverified_google_email(self):
        claims = {
            "sub": "google-user-3",
            "email": "unverified@example.com",
            "email_verified": False,
            "name": "Unverified User",
        }

        with (
            patch(
                "app.services.google_auth.id_token.verify_oauth2_token",
                return_value=claims,
            ),
            self.assertRaises(InvalidGoogleCredential),
        ):
            authenticate_google_user(
                self.session,
                "unverified-id-token",
                "google-client-id",
            )

        self.assertIsNone(
            self.session.query(User)
            .filter_by(email="unverified@example.com")
            .one_or_none()
        )

    def test_rejects_a_google_identity_already_linked_to_another_account(self):
        self.session.add(User(
            name="Existing User",
            email="existing@example.com",
            google_subject="another-google-user",
            role="doctor",
            is_active=True,
        ))
        self.session.commit()
        claims = {
            "sub": "google-user-4",
            "email": "existing@example.com",
            "email_verified": True,
        }

        with (
            patch(
                "app.services.google_auth.id_token.verify_oauth2_token",
                return_value=claims,
            ),
            self.assertRaises(GoogleAccountConflict),
        ):
            authenticate_google_user(
                self.session,
                "verified-id-token",
                "google-client-id",
            )

    def test_requires_google_client_configuration(self):
        with self.assertRaises(GoogleAuthNotConfigured):
            authenticate_google_user(
                self.session,
                "id-token",
                None,
            )

    def test_password_registration_and_login_are_retired(self):
        for endpoint in (
            password_registration_disabled,
            password_login_disabled,
        ):
            with self.subTest(endpoint=endpoint.__name__):
                with self.assertRaises(HTTPException) as error:
                    endpoint()
                self.assertEqual(error.exception.status_code, 410)


if __name__ == "__main__":
    unittest.main()
