"""Request-counting OpenAI-compatible mock for Lab 4 (idempotency)."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


STATE = {
    "request_counter": 0,
    "embedding_requests": 0,
    "chat_requests": 0,
}
STATE_LOCK = threading.Lock()


def embedding_for(text: str) -> list[float]:
    total = sum(ord(char) for char in text)
    length = max(len(text), 1)
    return [
        float((total % 97) / 97),
        float((length % 89) / 89),
        float((text.lower().count("r") % 13) / 13),
    ]


def bump(kind: str) -> None:
    with STATE_LOCK:
        STATE["request_counter"] += 1
        STATE[kind] = int(STATE.get(kind, 0)) + 1


def snapshot_state() -> dict:
    with STATE_LOCK:
        return dict(STATE)


def reset_state() -> None:
    with STATE_LOCK:
        STATE["request_counter"] = 0
        STATE["embedding_requests"] = 0
        STATE["chat_requests"] = 0


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/v1/models":
            self.send_json(
                200,
                {"object": "list", "data": [{"id": "idempotency-mock", "object": "model"}]},
            )
            return
        if self.path == "/mock-state":
            self.send_json(200, snapshot_state())
            return
        self.send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        payload = self.read_json()

        if self.path == "/control/reset":
            reset_state()
            self.send_json(200, snapshot_state())
            return

        if self.path == "/v1/embeddings":
            bump("embedding_requests")
            inputs = payload.get("input", [])
            if isinstance(inputs, str):
                inputs = [inputs]
            self.send_json(
                200,
                {
                    "object": "list",
                    "data": [
                        {
                            "object": "embedding",
                            "index": index,
                            "embedding": embedding_for(str(text)),
                        }
                        for index, text in enumerate(inputs)
                    ],
                    "model": payload.get("model", "text-embedding-3-small"),
                },
            )
            return

        if self.path == "/v1/chat/completions":
            bump("chat_requests")
            messages = payload.get("messages", [])
            user_content = messages[-1].get("content", "") if messages else ""
            self.send_json(
                200,
                {
                    "id": "chatcmpl-idempotency",
                    "object": "chat.completion",
                    "model": payload.get("model", "idempotency-mock"),
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": (
                                    "Idempotency lab mock answer. "
                                    f"Request length: {len(user_content)}."
                                ),
                            },
                            "finish_reason": "stop",
                        }
                    ],
                },
            )
            return

        self.send_json(404, {"error": "not found"})

    def log_message(self, format: str, *args: object) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8888), Handler).serve_forever()
