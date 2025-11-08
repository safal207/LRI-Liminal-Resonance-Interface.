from datetime import datetime

import time
from datetime import datetime, timezone
from typing import Iterable, Optional

from lri.lss import CoherenceResult, DriftEvent, LSS, RedisSessionStorage
from lri.types import Affect, Intent, LCE, Meaning, Policy


class FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, tuple[str, Optional[float]]] = {}

    def get(self, key: str) -> str | None:
        self._evict()
        value = self._store.get(key)
        return value[0] if value else None

    def set(self, key: str, value: str, *, px: Optional[int] = None) -> str:
        expires_at = (time.time() + px / 1000.0) if px else None
        self._store[key] = (value, expires_at)
        return "OK"

    def delete(self, *keys: str) -> int:
        removed = 0
        for key in keys:
            if key in self._store:
                del self._store[key]
                removed += 1
        return removed

    def scan_iter(self, match: str) -> Iterable[str]:
        self._evict()
        prefix = match[:-1] if match.endswith("*") else match
        for key in list(self._store.keys()):
            if match == "*" or key.startswith(prefix):
                yield key

    def _evict(self) -> None:
        now = time.time()
        for key, (_, expires_at) in list(self._store.items()):
            if expires_at is not None and expires_at <= now:
                del self._store[key]


def make_lce(intent_type: str, pad: tuple[float, float, float], topic: str) -> LCE:
    return LCE(
        intent=Intent(type=intent_type),
        affect=Affect(pad=pad),
        meaning=Meaning(topic=topic),
        policy=Policy(consent="team"),
    )


def test_store_and_metrics_calculation() -> None:
    store = LSS(coherence_window=5)
    store.store("thread-a", make_lce("ask", (0.1, 0.1, 0.1), "sync"))
    store.store("thread-a", make_lce("tell", (0.2, 0.1, 0.05), "sync"))

    session = store.get_session("thread-a")
    assert session is not None
    assert session.metadata.message_count == 2

    metrics = store.get_metrics("thread-a")
    assert metrics is not None
    assert 0 <= metrics.coherence.overall <= 1
    assert metrics.coherence.intent_similarity > 0


def test_drift_event_emission() -> None:
    store = LSS(coherence_window=5, drift_min_coherence=0.6, drift_drop_threshold=0.15)
    captured: list = []
    store.on("drift", lambda event: captured.append(event))

    store.store("thread-b", make_lce("ask", (0.9, 0.8, 0.8), "status"))
    store.store("thread-b", make_lce("tell", (0.1, 0.1, 0.1), "status"))
    store.store("thread-b", make_lce("plan", (0.9, -0.9, 0.6), "unrelated"))

    assert captured
    assert captured[0].thread_id == "thread-b"
    assert captured[0].type == "coherence_drop"


def test_manual_metrics_update() -> None:
    store = LSS()
    store.store("thread-c", make_lce("ask", (0.1, 0.1, 0.1), "topic1"))
    store.store("thread-c", make_lce("tell", (0.1, 0.1, 0.1), "topic1"))

    override = CoherenceResult(overall=0.9, intent_similarity=0.85, affect_stability=0.9, semantic_alignment=0.95)
    manual_event = DriftEvent(
        thread_id="thread-c",
        type="topic_shift",
        severity="low",
        timestamp=datetime.now(timezone.utc),
        details={"note": "manual override"},
    )
    updated = store.update_metrics("thread-c", coherence=override, drift_events=[manual_event])

    assert updated is not None
    assert updated.coherence.overall == 0.9
    assert updated.previous_coherence is not None
    assert isinstance(updated.updated_at, datetime)
    assert updated.drift_events
    assert updated.drift_events[0].thread_id == "thread-c"


def test_get_stats_reflects_sessions() -> None:
    store = LSS()
    store.store("thread-d", make_lce("ask", (0.2, 0.1, 0.0), "alpha"))
    store.store("thread-e", make_lce("tell", (0.2, 0.1, 0.0), "beta"))

    stats = store.get_stats()
    assert stats["session_count"] == 2
    assert stats["total_messages"] == 2
    assert 0 <= stats["average_coherence"] <= 1


def test_redis_storage_roundtrip() -> None:
    redis = FakeRedis()
    store = LSS(storage=RedisSessionStorage(redis))
    store.store("redis-thread", make_lce("ask", (0.1, 0.1, 0.1), "redis"))

    assert redis.get("lss:session:redis-thread") is not None
    session = store.get_session("redis-thread")
    assert session is not None
    assert session.thread_id == "redis-thread"


def test_redis_storage_respects_ttl() -> None:
    redis = FakeRedis()
    store = LSS(session_ttl=10, storage=RedisSessionStorage(redis))
    store.store("redis-ttl", make_lce("tell", (0.0, 0.0, 0.0), "ttl"))

    time.sleep(0.03)
    assert store.get_session("redis-ttl") is None
