import asyncio
from pathlib import Path

import pytest

from police_thief_p2p.adapters.persistence import AtomicFileRepository
from police_thief_p2p.adapters.system.clocks import FakeClock
from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.services.gatekeeper import (
    DurableQuotaManager,
    FullGatekeeper,
    GatekeeperProfile,
    load_profiles,
)
from police_thief_p2p.services.gatekeeper.anomaly import AnomalyDetector
from police_thief_p2p.services.gatekeeper.limiter import ContinuousTokenBucket
from police_thief_p2p.services.gatekeeper.priority import (
    AdmissionOutcome,
    PrioritySemaphore,
)
from police_thief_p2p.services.orchestration.circuit import CircuitBreaker, CircuitState
from police_thief_p2p.shared.gatekeeper import ExternalCall, ExternalResult


def _profile(**changes: int) -> GatekeeperProfile:
    values = {
        "requests_per_minute": 30,
        "burst_capacity": 5,
        "concurrent_requests": 1,
        "retry_backoff_sec": 5,
        "max_retries": 3,
        "queue_depth": 100,
        "timeout_sec": 100,
        "daily_quota": 100,
        "session_quota": 100,
        "circuit_failure_threshold": 2,
        "circuit_cooldown_sec": 10,
        "repeated_call_limit": 10,
        "sustained_error_limit": 10,
    }
    values.update(changes)
    return GatekeeperProfile.model_validate(values)


def _gatekeeper(
    tmp_path: Path,
    clock: FakeClock,
    executor: object,
    profile: GatekeeperProfile | None = None,
) -> FullGatekeeper:
    async def sleep(seconds: float) -> None:
        clock.advance(seconds)

    quota = DurableQuotaManager(
        AtomicFileRepository(tmp_path / "quota"),
        clock,
        session_id="test-session",
    )
    return FullGatekeeper(
        {"gmail": profile or _profile()},
        {"gmail": executor},  # type: ignore[dict-item]
        clock=clock,
        quota=quota,
        rng=DeterministicRandomSource(7),
        sleep=sleep,
    )


def test_profiles_token_bucket_and_durable_quota(tmp_path: Path) -> None:
    document = (Path(__file__).parents[2] / "config/rate_limits.example.json").read_bytes()
    profiles = load_profiles(document)
    assert set(profiles.services) == {"mcp", "gmail", "remote_llm"}
    with pytest.raises(ValueError, match="size"):
        load_profiles(b" " * 131_073)
    clock = FakeClock()
    bucket = ContinuousTokenBucket(clock, requests_per_minute=30, capacity=1)
    assert bucket.consume_delay() == 0
    assert bucket.consume_delay() == 2
    clock.advance(2)
    bucket.consume_after_wait()
    repository = AtomicFileRepository(tmp_path / "quota")
    quota = DurableQuotaManager(repository, clock, session_id="session-1")
    assert quota.consume("gmail", daily_limit=2, session_limit=1)
    assert not quota.consume("gmail", daily_limit=2, session_limit=1)
    with pytest.raises(ValueError, match="confirmation"):
        quota.reset_session(confirmed=False)
    quota.reset_session(confirmed=True)
    assert quota.consume("gmail", daily_limit=2, session_limit=1)
    assert not DurableQuotaManager(repository, clock, session_id="session-2").consume(
        "gmail", daily_limit=2, session_limit=2
    )
    clock.advance(86_400)
    assert quota.usage("gmail") == (0, 0)
    assert quota.consume("gmail", daily_limit=2, session_limit=1)


def test_gatekeeper_honors_429_guidance_retries_and_metrics(tmp_path: Path) -> None:
    clock = FakeClock()
    calls = 0

    async def executor(_: ExternalCall) -> ExternalResult:
        nonlocal calls
        calls += 1
        if calls == 1:
            return ExternalResult("rate_limited", {"code": "GMAIL_429", "retry_after_sec": 9})
        return ExternalResult("success", {"provider_id": "ok"})

    gatekeeper = _gatekeeper(tmp_path, clock, executor)
    result = asyncio.run(
        gatekeeper.execute(ExternalCall("gmail", "send", {"value": calls, "priority": 2}))
    )
    assert result.outcome == "success"
    assert calls == 2
    assert clock.monotonic() >= 9
    metrics = gatekeeper.metrics()["gmail"]
    assert metrics["retries"] == 1
    assert metrics["successes"] == 1
    assert metrics["quota_daily_used"] == 2
    assert metrics["quota_session_used"] == 2
    assert {"tokens", "queue_depth", "concurrency", "circuit_state"} <= set(metrics)


def test_gatekeeper_quota_anomaly_circuit_and_manual_reset(tmp_path: Path) -> None:
    clock = FakeClock()

    async def unavailable(_: ExternalCall) -> ExternalResult:
        return ExternalResult("unavailable", {"code": "GMAIL_HTTP_503"})

    gatekeeper = _gatekeeper(
        tmp_path,
        clock,
        unavailable,
        _profile(circuit_failure_threshold=1),
    )
    first = asyncio.run(gatekeeper.execute(ExternalCall("gmail", "one", {"n": 1})))
    assert first.outcome in {"unavailable", "timeout"}
    second = asyncio.run(gatekeeper.execute(ExternalCall("gmail", "two", {"n": 2})))
    assert second.payload["code"] == "CIRCUIT_OPEN"
    with pytest.raises(ValueError, match="confirmation"):
        gatekeeper.manual_reset("gmail", confirmed=False)
    gatekeeper.manual_reset("gmail", confirmed=True)
    detector = AnomalyDetector(clock)
    assert detector.admit("gmail", "same", burst_limit=2, repeated_limit=2, error_limit=2)[0]
    assert detector.admit("gmail", "same", burst_limit=2, repeated_limit=2, error_limit=2)[0]
    assert detector.admit("gmail", "same", burst_limit=2, repeated_limit=2, error_limit=2)[1]


def test_priority_semaphore_orders_waiters_and_rejects_backpressure() -> None:
    async def scenario() -> None:
        semaphore = PrioritySemaphore(limit=1, queue_capacity=2)
        assert await semaphore.acquire(2) is AdmissionOutcome.ACQUIRED
        order: list[str] = []

        async def waiter(name: str, priority: int) -> None:
            outcome = await semaphore.acquire(priority)
            order.append(f"{name}:{outcome}")
            await semaphore.release()

        low = asyncio.create_task(waiter("low", 3))
        high = asyncio.create_task(waiter("high", 0))
        await asyncio.sleep(0)
        assert await semaphore.acquire(1) is AdmissionOutcome.REJECTED_BACKPRESSURE
        await semaphore.release()
        await asyncio.gather(low, high)
        assert order[0].startswith("high:")
        assert semaphore.active == 0

    asyncio.run(scenario())


def test_half_open_circuit_admits_one_probe_and_recovers() -> None:
    clock = FakeClock()
    circuit = CircuitBreaker(clock, threshold=1, cooldown=10)
    circuit.failure()
    assert not circuit.allow()
    clock.advance(10)
    assert circuit.state is CircuitState.HALF_OPEN
    assert circuit.allow()
    assert not circuit.allow()
    circuit.success()
    assert str(circuit.state) == "closed"
