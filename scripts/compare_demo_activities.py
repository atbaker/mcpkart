"""Compare saved Cloud mock runs; dispatch gaps include the whole broker path."""

import argparse
import json
from collections import Counter
from datetime import datetime
from itertools import pairwise
from pathlib import Path

from audit_demo_wire import audit


def distribution(values):
    ordered = sorted(values)
    def percentile(q):
        position = (len(ordered) - 1) * q
        low = int(position)
        return ordered[low] + (ordered[min(low + 1, len(ordered) - 1)] - ordered[low]) * (position - low)
    return {"n": len(ordered), "p50_ms": percentile(.5), "p95_ms": percentile(.95), "max_ms": max(ordered)} if ordered else {"n": 0}


def analyze(path):
    path = Path(path)
    registration = json.loads((path / "demo-registration.json").read_text())
    assert registration["free"] and not registration["model_requests_enabled"]
    decisions = json.loads((path / "decisions.json").read_text())
    race = json.loads((path / "race.json").read_text())
    collection = json.loads((path / "collection.json").read_text())
    cadence, gaps, api_latency, scheduled_to_started = [], [], [], []
    counts = Counter()
    drivers = {}
    for rid, calls in decisions.items():
        driver_cadence = [(b["request_started_ns"] - a["request_started_ns"]) / 1e6
                          for a, b in pairwise(calls)]
        driver_gaps = [(b["request_started_ns"] - a["response_received_ns"]) / 1e6
                       for a, b in pairwise(calls)]
        assert all(x >= 0 for x in driver_gaps)
        cadence.extend(driver_cadence)
        gaps.extend(driver_gaps)
        api_latency.extend(c["latency_ms"] for c in calls)
        history = json.loads((path / ("temporal-history-" + rid + ".json")).read_text())["events"]
        assert history[-1]["eventType"] == "EVENT_TYPE_WORKFLOW_EXECUTION_COMPLETED"
        scheduled = {}
        for event in history:
            kind = event["eventType"]
            counts[kind] += 1
            assert "FAILED" not in kind and "TIMED_OUT" not in kind
            if kind == "EVENT_TYPE_ACTIVITY_TASK_SCHEDULED":
                attrs = event["activityTaskScheduledEventAttributes"]
                assert attrs["activityType"]["name"] == "kart_step"
                assert attrs["retryPolicy"]["maximumAttempts"] == 1
                scheduled[event["eventId"]] = datetime.fromisoformat(event["eventTime"])
            elif kind == "EVENT_TYPE_ACTIVITY_TASK_STARTED":
                attrs = event["activityTaskStartedEventAttributes"]
                assert attrs["attempt"] == 1
                scheduled_to_started.append((datetime.fromisoformat(event["eventTime"])
                                             - scheduled[attrs["scheduledEventId"]]).total_seconds() * 1000)
        drivers[rid] = {"requests": len(calls), "finish_s": race["summary"]["finish_times_s"][rid],
                        "rescues": race["summary"]["racers"][rid]["resets"],
                        "cadence": distribution(driver_cadence), "reply_to_next_request": distribution(driver_gaps)}
    if registration["local_activities"]:
        assert counts["EVENT_TYPE_MARKER_RECORDED"] > 0 and not counts["EVENT_TYPE_ACTIVITY_TASK_SCHEDULED"]
    else:
        assert counts["EVENT_TYPE_ACTIVITY_TASK_SCHEDULED"] > 0 and not counts["EVENT_TYPE_MARKER_RECORDED"]
    return {"path": str(path), "local_activities": registration["local_activities"],
            "all_finished": race["summary"]["finished"], "duration_s": race["summary"]["elapsed"],
            "native_requests": sum(len(c) for c in decisions.values()),
            "cadence": distribution(cadence), "reply_to_next_request": distribution(gaps),
            "api_latency": distribution(api_latency),
            "regular_schedule_to_start": distribution(scheduled_to_started),
            "child_history_event_counts": dict(counts), "drivers": drivers,
            "wire_audit": audit(path), "source_unchanged": collection["source_unchanged"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("local", type=Path)
    parser.add_argument("regular", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = {"local": analyze(args.local), "regular": analyze(args.regular),
              "real_model_calls": 0,
              "limitation": "One earlier local and one later regular mock race; service load and trajectories can differ. Reply gaps include broker/filesystem/MCP overhead."}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({mode: {k: value[k] for k in ("duration_s", "native_requests", "cadence",
                                                   "reply_to_next_request", "api_latency",
                                                   "regular_schedule_to_start")}
                      for mode, value in result.items() if mode in ("local", "regular")}, indent=2))


if __name__ == "__main__":
    main()
