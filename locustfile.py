from locust import HttpUser, task, between
import json

class GatewayUser(HttpUser):
    wait_time = between(0.1, 0.5)
    host = "http://127.0.0.1:8001"

    @task
    def chat(self):
        self.client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "load test"}], "temperature": 0.5},
            headers={"x-api-key": f"loadtest-{self.environment.runner.user_count}"},
        )