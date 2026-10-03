from locust import HttpUser, task, between
import uuid

class GatewayUser(HttpUser):
    wait_time = between(1.0, 2.0) 
    host = "http://127.0.0.1:8001"

    def on_start(self):
        self.api_key = f"loadtest-{uuid.uuid4().hex[:8]}"

    @task
    def chat(self):
        self.client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "load test"}], "temperature": 0.5},
            headers={"x-api-key": self.api_key},
        )