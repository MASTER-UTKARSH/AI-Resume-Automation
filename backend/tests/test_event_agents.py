import unittest
import asyncio
from backend.app.database.session import SessionLocal, init_db
from backend.app.database.models import User, Workflow, AgentRun
from backend.app.core.event_bus import event_bus
from backend.app.core.model_router import model_router

class TestEventAgents(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        init_db()
        self.db = SessionLocal()
        self.user = self.db.query(User).first()
        if not self.user:
            self.user = User(email="test.user@juet.in", full_name="Test User")
            self.db.add(self.user)
            self.db.commit()

    async def asyncTearDown(self):
        self.db.close()

    async def test_event_bus_publish_subscribe(self):
        received = []

        def sample_listener(data):
            received.append(data)

        event_bus.subscribe("TEST_EVENT", sample_listener)
        await event_bus.publish("TEST_EVENT", {"status": "ok", "value": 42})

        # Give event loop small tick for local async queue
        await asyncio.sleep(0.05)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["value"], 42)

    async def test_model_router_and_telemetry(self):
        health = model_router.get_provider_health()
        self.assertIn("GLM", health)
        self.assertIn("Qwen", health)
        self.assertIn("Groq", health)
        self.assertIn("Ollama", health)

        # Route a drafting task
        provider = model_router.route("writing")
        self.assertEqual(provider, "GLM")

        # Route a reasoning task
        provider = model_router.route("reasoning")
        self.assertEqual(provider, "Qwen")

        # Execute generation
        res = await model_router.generate_response("Tailor resume for AI engineer", task_type="writing")
        self.assertIn("provider", res)
        self.assertIn("latency_ms", res)
        self.assertIn("content", res)

if __name__ == "__main__":
    unittest.main()
