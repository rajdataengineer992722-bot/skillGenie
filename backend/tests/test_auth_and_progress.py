import importlib
import os
import unittest
from pathlib import Path
from uuid import uuid4


class AuthAndProgressFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path("backend") / "test_artifacts"
        cls.temp_dir.mkdir(parents=True, exist_ok=True)
        os.environ["APP_ENV"] = "test"
        os.environ["DEBUG"] = "true"
        os.environ["DATABASE_PATH"] = str((cls.temp_dir / "test.db").resolve())
        os.environ["TRUSTED_HOSTS"] = "testserver,localhost,127.0.0.1"
        os.environ["CORS_ORIGINS"] = "http://localhost:5173"
        os.environ["SESSION_COOKIE_SECURE"] = "false"
        os.environ["OPENAI_API_KEY"] = ""

        import backend.config
        import backend.database
        import backend.dependencies
        import backend.services.auth_service
        import backend.services.tracking_service
        import backend.routes.auth
        import backend.routes.chat
        import backend.routes.learning
        import backend.routes.metrics
        import backend.main

        importlib.reload(backend.config)
        importlib.reload(backend.database)
        importlib.reload(backend.dependencies)
        importlib.reload(backend.services.auth_service)
        importlib.reload(backend.services.tracking_service)
        importlib.reload(backend.routes.auth)
        importlib.reload(backend.routes.chat)
        importlib.reload(backend.routes.learning)
        importlib.reload(backend.routes.metrics)
        cls.main = importlib.reload(backend.main)

        from fastapi.testclient import TestClient

        cls.client = TestClient(cls.main.app)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_register_login_plan_progress_and_chat_flow(self):
        email = f"prod.user.{uuid4().hex[:8]}@example.com"
        register_response = self.client.post(
            "/auth/register",
            json={
                "full_name": "Prod User",
                "email": email,
                "password": "StrongPass123",
            },
        )
        self.assertEqual(register_response.status_code, 200)
        self.assertIn("user", register_response.json())

        me_response = self.client.get("/auth/me")
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["user"]["email"], email)

        plan_response = self.client.post(
            "/plan",
            json={"role": "Frontend Developer", "goal": "Ship React features"},
        )
        self.assertEqual(plan_response.status_code, 200)
        plan_record = plan_response.json()["plan_record"]

        update_response = self.client.patch(
            f"/progress/{plan_record['id']}",
            json={"completed_steps": 1, "hours_spent": 2},
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertGreaterEqual(update_response.json()["plan"]["progress_percent"], 0)

        chat_response = self.client.post("/chat", json={"message": "How should I study?"})
        self.assertEqual(chat_response.status_code, 200)
        self.assertIn("response", chat_response.json())

        reset_request_response = self.client.post(
            "/auth/password-reset/request",
            json={"email": email},
        )
        self.assertEqual(reset_request_response.status_code, 200)
        reset_token = reset_request_response.json().get("reset_token")
        self.assertTrue(reset_token)

        reset_confirm_response = self.client.post(
            "/auth/password-reset/confirm",
            json={"token": reset_token, "password": "UpdatedPass123"},
        )
        self.assertEqual(reset_confirm_response.status_code, 200)

        dashboard_response = self.client.get("/dashboard")
        self.assertEqual(dashboard_response.status_code, 200)
        dashboard = dashboard_response.json()
        self.assertEqual(len(dashboard["plans"]), 1)
        self.assertGreaterEqual(dashboard["metrics"]["total_messages"], 1)

        logout_response = self.client.post("/auth/logout")
        self.assertEqual(logout_response.status_code, 200)
        unauthorized_me = self.client.get("/auth/me")
        self.assertEqual(unauthorized_me.status_code, 401)


if __name__ == "__main__":
    unittest.main()
