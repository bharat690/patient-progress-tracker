import unittest

from app.core.rate_limit import InMemoryRateLimiter
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


class AuthSecurityTests(unittest.TestCase):
    def test_password_hash_round_trip(self):
        password = "P@ssw0rd123!"
        hashed = get_password_hash(password)

        self.assertNotEqual(hashed, password)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("wrong-password", hashed))

    def test_access_token_round_trip(self):
        token = create_access_token(42)
        payload = decode_access_token(token)

        self.assertEqual(payload["sub"], "42")
        self.assertIn("exp", payload)

    def test_rate_limiter_blocks_after_limit(self):
        limiter = InMemoryRateLimiter()
        key = "test-user"
        limit_value = "2/second"

        self.assertTrue(limiter.allow(key, limit_value))
        self.assertTrue(limiter.allow(key, limit_value))
        self.assertFalse(limiter.allow(key, limit_value))


if __name__ == "__main__":
    unittest.main()
