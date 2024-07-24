import requests
from dsp import LM


class Claude(LM):
    def __init__(self, model, api_key):
        self.model = model
        self.api_key = api_key
        self.provider = "default"

        self.base_url = "https://api.anthropic.com/v1/messages"

    def basic_request(self, prompt: str, **kwargs):
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "messages-2023-12-15",
            "content-type": "application/json",
        }

        data = {
            **kwargs,
            "temperature": 0.0,
            "max_tokens": 2048,
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }

        response = requests.post(self.base_url, headers=headers, json=data)
        response = response.json()

        self.history.append(
            {
                "prompt": prompt,
                "response": response,
                "kwargs": kwargs,
            }
        )
        return response

    def __call__(
        self, prompt, only_completed=True, return_sorted=False, **kwargs
    ):
        response = self.request(prompt, **kwargs)

        completions = [result["text"] for result in response["content"]]

        return completions
