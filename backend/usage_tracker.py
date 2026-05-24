"""
Usage tracker for Gemini API free tier limits.
Tracks requests, tokens, and resets daily at midnight Pacific Time.
Supports automatic model fallback when one model's quota is exhausted.
Persists stats to disk so server restarts don't lose counts.
"""

import json
import os
import threading
from datetime import datetime, timezone, timedelta

# Pacific Time offset (UTC-7 PDT / UTC-8 PST)
# Simplified: using UTC-7 for PDT (May-Nov)
PT = timezone(timedelta(hours=-7))

# Models in fallback order: best quality first → faster fallbacks.
# Each model has its own independent quota on the free tier.
MODEL_CHAIN = [
    {
        "name": "gemini-2.5-pro",
        "tier": "premium",
        "rpm": 5,
        "rpd": 25,
        "tpm_input": 250_000,
        "tpd_input": 1_000_000,
    },
    {
        "name": "gemini-2.5-flash",
        "tier": "primary",
        "rpm": 15,
        "rpd": 1500,
        "tpm_input": 1_000_000,
        "tpd_input": 1_500_000,
    },
    {
        "name": "gemini-2.5-flash-lite",
        "tier": "fallback",
        "rpm": 30,
        "rpd": 3000,
        "tpm_input": 1_000_000,
        "tpd_input": 1_500_000,
    },
]

# Backward-compat alias
FREE_TIER_LIMITS = {
    "rpm": MODEL_CHAIN[0]["rpm"],
    "rpd": MODEL_CHAIN[0]["rpd"],
    "tpm_input": MODEL_CHAIN[0]["tpm_input"],
    "tpd_input": MODEL_CHAIN[0]["tpd_input"],
}

# Persistence file paths
USAGE_FILE = os.path.join(os.path.dirname(__file__), "storage", "usage_stats.json")
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "storage", "usage_history.json")


class UsageTracker:
    """Thread-safe daily usage tracker with automatic midnight PT reset,
    model fallback, and disk persistence across server restarts."""

    def __init__(self, persistence_file=None, history_file=None):
        self._lock = threading.Lock()
        self._persistence_file = persistence_file
        self._history_file = history_file
        self._load_or_reset()

    def _load_or_reset(self):
        """Load stats from disk if same day, otherwise reset."""
        today = datetime.now(PT).strftime("%Y-%m-%d")
        loaded = False
        pf = self._persistence_file
        if pf and os.path.exists(pf):
            try:
                with open(USAGE_FILE, "r") as f:
                    data = json.load(f)
                if data.get("date") == today:
                    self.date = data["date"]
                    self.current_minute = datetime.now(PT).strftime("%H:%M")
                    self.last_request_time = data.get("last_request_time")
                    self.errors_today = data.get("errors_today", 0)
                    self.fallbacks_today = data.get("fallbacks_today", 0)
                    self._model_stats = {}
                    for m in MODEL_CHAIN:
                        saved = data.get("model_stats", {}).get(m["name"], {})
                        self._model_stats[m["name"]] = {
                            "requests_today": saved.get("requests_today", 0),
                            "input_tokens_today": saved.get("input_tokens_today", 0),
                            "output_tokens_today": saved.get("output_tokens_today", 0),
                            "total_tokens_today": saved.get("total_tokens_today", 0),
                            "requests_this_minute": 0,  # always reset per-minute on restart
                            "current_minute": self.current_minute,
                            "exhausted": saved.get("exhausted", False),
                        }
                    loaded = True
            except (json.JSONDecodeError, KeyError):
                pass
        if not loaded:
            self._reset()

    def _save(self):
        """Persist current stats to disk (call while holding lock)."""
        pf = self._persistence_file
        if not pf:
            return
        data = {
            "date": self.date,
            "last_request_time": self.last_request_time,
            "errors_today": self.errors_today,
            "fallbacks_today": self.fallbacks_today,
            "model_stats": {
                name: {
                    "requests_today": s["requests_today"],
                    "input_tokens_today": s["input_tokens_today"],
                    "output_tokens_today": s["output_tokens_today"],
                    "total_tokens_today": s["total_tokens_today"],
                    "exhausted": s.get("exhausted", False),
                }
                for name, s in self._model_stats.items()
            },
        }
        try:
            os.makedirs(os.path.dirname(pf), exist_ok=True)
            with open(pf, "w") as f:
                json.dump(data, f)
        except OSError:
            pass

    def _reset(self):
        """Reset all counters."""
        now_pt = datetime.now(PT)
        self.date = now_pt.strftime("%Y-%m-%d")
        self.current_minute = now_pt.strftime("%H:%M")
        self.last_request_time = None
        self.errors_today = 0
        self.fallbacks_today = 0
        # Per-model counters: { "gemini-2.5-flash": { requests, input_tokens, ... }, ... }
        self._model_stats = {}
        for m in MODEL_CHAIN:
            self._model_stats[m["name"]] = {
                "requests_today": 0,
                "input_tokens_today": 0,
                "output_tokens_today": 0,
                "total_tokens_today": 0,
                "requests_this_minute": 0,
                "current_minute": self.current_minute,
                "exhausted": False,
            }

    def _check_day_rollover(self):
        """Reset counters if the date changed (midnight PT)."""
        today = datetime.now(PT).strftime("%Y-%m-%d")
        if today != self.date:
            self._archive_day()
            self._reset()

    def _check_minute_rollover(self):
        """Reset per-minute counters if the minute changed."""
        now_minute = datetime.now(PT).strftime("%H:%M")
        if now_minute != self.current_minute:
            self.current_minute = now_minute
            for stats in self._model_stats.values():
                stats["requests_this_minute"] = 0
                stats["current_minute"] = now_minute

    def _model_limits(self, model_name: str) -> dict:
        """Get limits dict for a model."""
        for m in MODEL_CHAIN:
            if m["name"] == model_name:
                return m
        return MODEL_CHAIN[0]

    def get_active_model(self) -> str:
        """Return the best available model (first one not over quota)."""
        with self._lock:
            self._check_day_rollover()
            self._check_minute_rollover()
            for m in MODEL_CHAIN:
                name = m["name"]
                stats = self._model_stats[name]
                if (not stats.get("exhausted")
                        and stats["requests_today"] < m["rpd"]
                        and stats["requests_this_minute"] < m["rpm"]
                        and stats["input_tokens_today"] < m["tpd_input"]):
                    return name
            # All exhausted — return last one (will get 429 but user sees proper error)
            return MODEL_CHAIN[-1]["name"]

    def record_request(self, model: str = None, input_tokens: int = 0, output_tokens: int = 0):
        """Record a successful API request for a specific model."""
        with self._lock:
            self._check_day_rollover()
            self._check_minute_rollover()
            model = model or MODEL_CHAIN[0]["name"]
            if model not in self._model_stats:
                model = MODEL_CHAIN[0]["name"]
            stats = self._model_stats[model]
            stats["requests_today"] += 1
            stats["requests_this_minute"] += 1
            stats["input_tokens_today"] += input_tokens
            stats["output_tokens_today"] += output_tokens
            stats["total_tokens_today"] += input_tokens + output_tokens
            self.last_request_time = datetime.now(PT).strftime("%H:%M:%S")
            self._save()

    def record_fallback(self):
        """Record that a model fallback occurred."""
        with self._lock:
            self.fallbacks_today += 1
            self._save()

    def record_error(self):
        """Record a failed request."""
        with self._lock:
            self._check_day_rollover()
            self.errors_today += 1
            self._save()

    def exhaust_model(self, model: str):
        """Mark a model as exhausted (e.g., after a 429). Skipped until daily reset."""
        with self._lock:
            if model in self._model_stats:
                self._model_stats[model]["exhausted"] = True
                self._save()

    def get_usage(self) -> dict:
        """Return current usage stats with per-model breakdown."""
        with self._lock:
            self._check_day_rollover()
            self._check_minute_rollover()

            active_model = None
            for m in MODEL_CHAIN:
                name = m["name"]
                stats = self._model_stats[name]
                if (active_model is None
                        and not stats.get("exhausted")
                        and stats["requests_today"] < m["rpd"]
                        and stats["requests_this_minute"] < m["rpm"]
                        and stats["input_tokens_today"] < m["tpd_input"]):
                    active_model = name
            active_model = active_model or MODEL_CHAIN[-1]["name"]

            # Per-model breakdown
            models = {}
            total_requests = 0
            total_input = 0
            total_output = 0
            for m in MODEL_CHAIN:
                name = m["name"]
                stats = self._model_stats[name]
                total_requests += stats["requests_today"]
                total_input += stats["input_tokens_today"]
                total_output += stats["output_tokens_today"]
                models[name] = {
                    "tier": m["tier"],
                    "active": name == active_model,
                    "exhausted": bool(stats.get("exhausted")),
                    "daily_requests": {
                        "used": stats["requests_today"],
                        "limit": m["rpd"],
                        "remaining": max(0, m["rpd"] - stats["requests_today"]),
                        "percent_used": round(stats["requests_today"] / m["rpd"] * 100, 1),
                    },
                    "daily_tokens": {
                        "input": stats["input_tokens_today"],
                        "output": stats["output_tokens_today"],
                        "total": stats["total_tokens_today"],
                        "limit": m["tpd_input"],
                    },
                    "per_minute": {
                        "used": stats["requests_this_minute"],
                        "limit": m["rpm"],
                        "remaining": max(0, m["rpm"] - stats["requests_this_minute"]),
                    },
                }

            return {
                "date": self.date,
                "active_model": active_model,
                "fallback_enabled": len(MODEL_CHAIN) > 1,
                "summary": {
                    "total_requests": total_requests,
                    "total_input_tokens": total_input,
                    "total_output_tokens": total_output,
                    "total_combined_quota": sum(m["rpd"] for m in MODEL_CHAIN),
                    "total_remaining": sum(m["rpd"] for m in MODEL_CHAIN) - total_requests,
                    "percent_used": round(total_requests / sum(m["rpd"] for m in MODEL_CHAIN) * 100, 1),
                },
                "models": models,
                "fallbacks_today": self.fallbacks_today,
                "errors_today": self.errors_today,
                "last_request": self.last_request_time,
                "current_time_pt": datetime.now(PT).strftime("%I:%M %p PT"),
                "resets_at": "12:00 AM Pacific Time (PT)",
                "resets_in": self._time_until_reset(),
            }

    def _time_until_reset(self) -> str:
        """Calculate time remaining until midnight PT reset."""
        now = datetime.now(PT)
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        diff = midnight - now
        hours, remainder = divmod(int(diff.total_seconds()), 3600)
        minutes = remainder // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


    def _archive_day(self):
        """Save today's stats to history before resetting."""
        hf = self._history_file
        if not hf:
            return
        # Build snapshot of today
        total_requests = 0
        total_input = 0
        total_output = 0
        model_snapshot = {}
        for m in MODEL_CHAIN:
            name = m["name"]
            stats = self._model_stats[name]
            total_requests += stats["requests_today"]
            total_input += stats["input_tokens_today"]
            total_output += stats["output_tokens_today"]
            model_snapshot[name] = {
                "requests": stats["requests_today"],
                "input_tokens": stats["input_tokens_today"],
                "output_tokens": stats["output_tokens_today"],
                "exhausted": bool(stats.get("exhausted")),
                "quota": m["rpd"],
                "percent_used": round(stats["requests_today"] / m["rpd"] * 100, 1),
            }
        if total_requests == 0:
            return  # Don't archive empty days
        combined_quota = sum(m["rpd"] for m in MODEL_CHAIN)
        entry = {
            "date": self.date,
            "total_requests": total_requests,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "combined_quota": combined_quota,
            "percent_used": round(total_requests / combined_quota * 100, 1),
            "fallbacks": self.fallbacks_today,
            "errors": self.errors_today,
            "models": model_snapshot,
        }
        # Load existing history
        history = []
        if os.path.exists(hf):
            try:
                with open(hf, "r") as f:
                    history = json.load(f)
            except (json.JSONDecodeError, OSError):
                history = []
        # Don't duplicate if same date already archived
        if history and history[-1].get("date") == self.date:
            history[-1] = entry
        else:
            history.append(entry)
        # Keep last 90 days
        history = history[-90:]
        try:
            os.makedirs(os.path.dirname(hf), exist_ok=True)
            with open(hf, "w") as f:
                json.dump(history, f)
        except OSError:
            pass

    def get_history(self, days: int = 30) -> dict:
        """Return usage history for the dashboard chart."""
        with self._lock:
            self._check_day_rollover()
            self._check_minute_rollover()

            # Load archived history
            history = []
            hf = self._history_file
            if hf and os.path.exists(hf):
                try:
                    with open(hf, "r") as f:
                        history = json.load(f)
                except (json.JSONDecodeError, OSError):
                    history = []

            # Append today's live data
            total_requests = 0
            total_input = 0
            total_output = 0
            model_snapshot = {}
            for m in MODEL_CHAIN:
                name = m["name"]
                stats = self._model_stats[name]
                total_requests += stats["requests_today"]
                total_input += stats["input_tokens_today"]
                total_output += stats["output_tokens_today"]
                model_snapshot[name] = {
                    "requests": stats["requests_today"],
                    "input_tokens": stats["input_tokens_today"],
                    "output_tokens": stats["output_tokens_today"],
                    "exhausted": bool(stats.get("exhausted")),
                    "quota": m["rpd"],
                    "percent_used": round(stats["requests_today"] / m["rpd"] * 100, 1),
                }
            combined_quota = sum(m["rpd"] for m in MODEL_CHAIN)
            today_entry = {
                "date": self.date,
                "total_requests": total_requests,
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_tokens": total_input + total_output,
                "combined_quota": combined_quota,
                "percent_used": round(total_requests / combined_quota * 100, 1) if combined_quota else 0,
                "fallbacks": self.fallbacks_today,
                "errors": self.errors_today,
                "models": model_snapshot,
                "is_today": True,
            }
            # Replace or append today
            if history and history[-1].get("date") == self.date:
                history[-1] = today_entry
            else:
                history.append(today_entry)

            # Trim to requested days
            history = history[-days:]

            return {
                "days": len(history),
                "history": history,
            }


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~1 token per 4 characters for English text."""
    if not text:
        return 0
    return max(1, len(text) // 4)


# Global singleton (persists to disk)
tracker = UsageTracker(persistence_file=USAGE_FILE, history_file=HISTORY_FILE)
