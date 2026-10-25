"""Real credentials/session boundaries with disposable account and workspace databases."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app import auth


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"STORESCOUT_DB_PATH": str(Path(self.tmp.name) / "state.sqlite3")})
        self.env.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.env.stop()
        self.tmp.cleanup()

    def register(self, client=None, email="person@example.test"):
        return (client or self.client).post('/api/v1/auth/register', json={"name":"Account Owner", "email":email, "password":"a-long-test-passphrase"})

    def test_session_login_logout_and_password_storage(self):
        self.assertEqual(self.client.get('/api/v1/projects/demo').status_code, 401)
        result = self.register()
        self.assertEqual(result.status_code, 201)
        self.assertIn('HttpOnly', result.headers['set-cookie'])
        self.assertIn('SameSite=lax', result.headers['set-cookie'])
        self.assertEqual(self.client.get('/api/v1/auth/me').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/projects/demo').status_code, 200)
        old = self.client.cookies.get(auth.COOKIE)
        with auth.database() as db:
            row = db.execute('SELECT password_hash FROM users').fetchone()
            self.assertNotEqual(row[0], 'a-long-test-passphrase')
            self.assertNotEqual(db.execute('SELECT token_hash FROM sessions').fetchone()[0], old)
        self.client.post('/api/v1/auth/logout')
        self.assertEqual(self.client.get('/api/v1/auth/me').status_code, 401)
        self.client.cookies.set(auth.COOKIE, old)
        self.assertEqual(self.client.get('/api/v1/projects/demo').status_code, 401)
        self.client.cookies.clear()
        self.assertEqual(self.client.post('/api/v1/auth/login', json={"email":"PERSON@example.test", "password":"a-long-test-passphrase"}).status_code, 200)

    def test_validation_wrong_password_and_throttling(self):
        self.assertEqual(self.client.post('/api/v1/auth/register', json={"name":"A", "email":"bad", "password":"short"}).status_code, 422)
        self.register()
        for _ in range(9):
            self.assertEqual(self.client.post('/api/v1/auth/login', json={"email":"person@example.test", "password":"wrong"}).status_code, 401)
        self.assertEqual(self.client.post('/api/v1/auth/login', json={"email":"person@example.test", "password":"wrong"}).status_code, 429)

    def test_account_isolation_expiry_and_origin(self):
        self.register()
        created = self.client.post('/api/v1/projects/demo/scenarios', json={"name":"Private plan", "assumptions":{}})
        self.assertEqual(created.status_code, 201, created.text)
        scenario_id = created.json()['data']['scenario_id']
        with TestClient(app) as other:
            self.assertEqual(self.register(other, 'other@example.test').status_code, 201)
            self.assertEqual(other.get('/api/v1/projects/demo/scenarios/' + scenario_id).status_code, 404)
            self.assertEqual(len(other.get('/api/v1/projects/demo/scenarios').json()['data']), 1)
        self.assertEqual(self.client.post('/api/v1/auth/logout', headers={'Origin':'https://unapproved.example'}).status_code, 403)
        with auth.database() as db:
            db.execute('UPDATE sessions SET expires=0')
        self.assertEqual(self.client.get('/api/v1/projects/demo').status_code, 401)
