"""Tests for usage_tracker module — fallback logic, counters, and token estimation."""

import pytest
from usage_tracker import UsageTracker, MODEL_CHAIN, estimate_tokens


class TestEstimateTokens:
    def test_empty_string(self):
        assert estimate_tokens("") == 0

    def test_none(self):
        assert estimate_tokens(None) == 0

    def test_short_text(self):
        assert estimate_tokens("hi") == 1  # min 1

    def test_typical_text(self):
        text = "What are the GDPR requirements for data breach notification?"
        tokens = estimate_tokens(text)
        assert tokens == len(text) // 4
        assert tokens > 0

    def test_long_text(self):
        text = "a" * 4000
        assert estimate_tokens(text) == 1000


class TestUsageTrackerBasic:
    def setup_method(self):
        self.tracker = UsageTracker()

    def test_initial_state(self):
        usage = self.tracker.get_usage()
        assert usage["active_model"] == MODEL_CHAIN[0]["name"]
        assert usage["fallback_enabled"] is True
        assert usage["summary"]["total_requests"] == 0
        assert usage["errors_today"] == 0
        assert usage["fallbacks_today"] == 0

    def test_record_request_increments(self):
        model = MODEL_CHAIN[0]["name"]
        self.tracker.record_request(model=model, input_tokens=100, output_tokens=50)
        usage = self.tracker.get_usage()
        assert usage["summary"]["total_requests"] == 1
        assert usage["summary"]["total_input_tokens"] == 100
        assert usage["summary"]["total_output_tokens"] == 50
        assert usage["models"][model]["daily_requests"]["used"] == 1
        assert usage["models"][model]["daily_tokens"]["input"] == 100

    def test_record_multiple_requests(self):
        model = MODEL_CHAIN[0]["name"]
        for _ in range(5):
            self.tracker.record_request(model=model, input_tokens=200, output_tokens=100)
        usage = self.tracker.get_usage()
        assert usage["summary"]["total_requests"] == 5
        assert usage["summary"]["total_input_tokens"] == 1000
        assert usage["models"][model]["daily_requests"]["used"] == 5

    def test_record_error(self):
        self.tracker.record_error()
        self.tracker.record_error()
        usage = self.tracker.get_usage()
        assert usage["errors_today"] == 2

    def test_record_fallback(self):
        self.tracker.record_fallback()
        usage = self.tracker.get_usage()
        assert usage["fallbacks_today"] == 1

    def test_last_request_initially_none(self):
        usage = self.tracker.get_usage()
        assert usage["last_request"] is None

    def test_last_request_set_after_request(self):
        self.tracker.record_request(model=MODEL_CHAIN[0]["name"], input_tokens=10)
        usage = self.tracker.get_usage()
        assert usage["last_request"] is not None

    def test_unknown_model_falls_back_to_primary(self):
        self.tracker.record_request(model="nonexistent-model", input_tokens=50)
        usage = self.tracker.get_usage()
        primary = MODEL_CHAIN[0]["name"]
        assert usage["models"][primary]["daily_requests"]["used"] == 1

    def test_default_model_is_primary(self):
        self.tracker.record_request(input_tokens=50)
        usage = self.tracker.get_usage()
        primary = MODEL_CHAIN[0]["name"]
        assert usage["models"][primary]["daily_requests"]["used"] == 1


class TestModelFallback:
    def setup_method(self):
        self.tracker = UsageTracker()

    def test_active_model_starts_as_primary(self):
        assert self.tracker.get_active_model() == MODEL_CHAIN[0]["name"]

    def test_fallback_when_primary_rpd_exhausted(self):
        """When primary model's daily requests hit the limit, active model should switch."""
        primary = MODEL_CHAIN[0]["name"]
        fallback = MODEL_CHAIN[1]["name"]
        rpd = MODEL_CHAIN[0]["rpd"]

        # Exhaust primary daily quota
        for _ in range(rpd):
            self.tracker.record_request(model=primary, input_tokens=1)

        active = self.tracker.get_active_model()
        assert active == fallback

    def test_fallback_when_primary_rpm_exhausted(self):
        """When primary hits per-minute limit, should fall back."""
        primary = MODEL_CHAIN[0]["name"]
        fallback = MODEL_CHAIN[1]["name"]
        rpm = MODEL_CHAIN[0]["rpm"]

        for _ in range(rpm):
            self.tracker.record_request(model=primary, input_tokens=1)

        active = self.tracker.get_active_model()
        assert active == fallback

    def test_returns_last_model_when_all_exhausted(self):
        """When all models are exhausted, returns last model in chain."""
        for m in MODEL_CHAIN:
            for _ in range(m["rpd"]):
                self.tracker.record_request(model=m["name"], input_tokens=1)

        active = self.tracker.get_active_model()
        assert active == MODEL_CHAIN[-1]["name"]

    def test_per_model_usage_independent(self):
        """Requests to one model don't affect another's counters."""
        primary = MODEL_CHAIN[0]["name"]
        fallback = MODEL_CHAIN[1]["name"]

        self.tracker.record_request(model=primary, input_tokens=100)
        self.tracker.record_request(model=primary, input_tokens=100)
        self.tracker.record_request(model=fallback, input_tokens=50)

        usage = self.tracker.get_usage()
        assert usage["models"][primary]["daily_requests"]["used"] == 2
        assert usage["models"][fallback]["daily_requests"]["used"] == 1
        assert usage["models"][primary]["daily_tokens"]["input"] == 200
        assert usage["models"][fallback]["daily_tokens"]["input"] == 50


class TestUsageResponseFormat:
    def setup_method(self):
        self.tracker = UsageTracker()

    def test_usage_has_required_keys(self):
        usage = self.tracker.get_usage()
        assert "date" in usage
        assert "active_model" in usage
        assert "fallback_enabled" in usage
        assert "summary" in usage
        assert "models" in usage
        assert "errors_today" in usage
        assert "resets_at" in usage

    def test_summary_has_required_keys(self):
        usage = self.tracker.get_usage()
        s = usage["summary"]
        assert "total_requests" in s
        assert "total_input_tokens" in s
        assert "total_output_tokens" in s
        assert "total_combined_quota" in s
        assert "total_remaining" in s
        assert "percent_used" in s

    def test_model_entry_has_required_keys(self):
        usage = self.tracker.get_usage()
        for name, info in usage["models"].items():
            assert "tier" in info
            assert "active" in info
            assert "daily_requests" in info
            assert "daily_tokens" in info
            assert "per_minute" in info

    def test_combined_quota_is_sum(self):
        usage = self.tracker.get_usage()
        expected = sum(m["rpd"] for m in MODEL_CHAIN)
        assert usage["summary"]["total_combined_quota"] == expected

    def test_remaining_decreases(self):
        model = MODEL_CHAIN[0]["name"]
        before = self.tracker.get_usage()["summary"]["total_remaining"]
        self.tracker.record_request(model=model, input_tokens=10)
        after = self.tracker.get_usage()["summary"]["total_remaining"]
        assert after == before - 1


class TestModelChainConfig:
    def test_model_chain_not_empty(self):
        assert len(MODEL_CHAIN) >= 1

    def test_first_model_is_primary(self):
        assert MODEL_CHAIN[0]["tier"] in ("primary", "premium")

    def test_all_models_have_required_fields(self):
        for m in MODEL_CHAIN:
            assert "name" in m
            assert "tier" in m
            assert "rpm" in m
            assert "rpd" in m
            assert "tpd_input" in m

    def test_all_model_names_unique(self):
        names = [m["name"] for m in MODEL_CHAIN]
        assert len(names) == len(set(names))
