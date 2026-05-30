"""Tiny OpenAI-compatible mock server for Lab 3."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


STATE = {
    "mode": "healthy",
    "request_counter": 0,
    "failure_counter": 0,
    "every_n": 2,
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


def should_fail_request() -> bool:
    with STATE_LOCK:
        STATE["request_counter"] += 1
        counter = int(STATE["request_counter"])
        mode = str(STATE["mode"])
        every_n = max(int(STATE.get("every_n", 2)), 1)
        failed = False
        if mode == "alternating_503":
            failed = counter % 2 == 1
        elif mode == "every_nth_503":
            failed = counter % every_n == 0
        if failed:
            STATE["failure_counter"] += 1
        return failed


def snapshot_state() -> dict:
    with STATE_LOCK:
        return dict(STATE)


def set_failure_mode(payload: dict) -> None:
    mode = payload.get("mode", "healthy")
    every_n = int(payload.get("every_n", 2))
    if mode not in {"healthy", "alternating_503", "every_nth_503"}:
        raise ValueError(f"unsupported failure mode: {mode}")
    with STATE_LOCK:
        STATE["mode"] = mode
        STATE["request_counter"] = 0
        STATE["failure_counter"] = 0
        STATE["every_n"] = max(every_n, 1)


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

    def maybe_send_503(self) -> bool:
        if not should_fail_request():
            return False
        self.send_json(
            503,
            {
                "error": "deterministic intermittent failure",
                "state": snapshot_state(),
            },
        )
        return True

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/v1/models":
            self.send_json(
                200,
                {
                    "object": "list",
                    "data": [{"id": "retry-mock", "object": "model"}],
                },
            )
            return
        if self.path == "/mock-state":
            self.send_json(200, snapshot_state())
            return
        self.send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        payload = self.read_json()
        if self.path == "/control/failure-mode":
            try:
                set_failure_mode(payload)
            except ValueError as exc:
                self.send_json(400, {"error": str(exc)})
                return
            self.send_json(200, snapshot_state())
            return

        if self.path == "/control/reset":
            set_failure_mode({"mode": "healthy", "every_n": 2})
            self.send_json(200, snapshot_state())
            return

        if self.path == "/v1/embeddings":
            if self.maybe_send_503():
                return
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
            if self.maybe_send_503():
                return
            messages = payload.get("messages", [])
            user_content = messages[-1].get("content", "") if messages else ""
            self.send_json(
                200,
                {
                    "id": "chatcmpl-retries",
                    "object": "chat.completion",
                    "model": payload.get("model", "retry-mock"),
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": (
                                    "Retries and jitter lab mock answer. "
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
