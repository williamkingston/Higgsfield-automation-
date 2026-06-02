from src.empire_ops import notify


class _Resp:
    def __init__(self, ok):
        self.ok = ok
        self.status_code = 200 if ok else 500


def test_no_webhook_returns_false(monkeypatch):
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    assert notify.post_slack("hi") is False


def test_posts_when_webhook_present(monkeypatch):
    calls = {}

    def fake_post(url, data=None, headers=None, timeout=None):
        calls["url"] = url
        calls["data"] = data
        return _Resp(ok=True)

    monkeypatch.setattr(notify.requests, "post", fake_post)
    assert notify.post_slack("digest ready", webhook_url="https://hooks.slack/x") is True
    assert calls["url"] == "https://hooks.slack/x"
    assert "digest ready" in calls["data"]


def test_returns_false_on_http_error(monkeypatch):
    monkeypatch.setattr(notify.requests, "post", lambda *a, **k: _Resp(ok=False))
    assert notify.post_slack("x", webhook_url="https://hooks.slack/x") is False
