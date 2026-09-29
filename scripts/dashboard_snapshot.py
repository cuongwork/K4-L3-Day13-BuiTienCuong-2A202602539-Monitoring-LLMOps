from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((p / 100) * len(ordered) + 0.5) - 1))
    return ordered[index]


def parse_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use an ISO-8601 datetime, for example 2026-09-29T09:36:01Z") from exc
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("Datetime must include a timezone")
    return parsed.astimezone(timezone.utc)


def load_logs(path: Path, start: datetime | None = None, end: datetime | None = None) -> list[dict]:
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            ts = datetime.fromisoformat(str(record["ts"]).replace("Z", "+00:00"))
        except (KeyError, ValueError, json.JSONDecodeError):
            continue
        if start is not None and ts < start:
            continue
        if end is not None and ts > end:
            continue
        records.append(record)
    return records


def load_recent_logs(path: Path, minutes: int) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    return load_logs(path, start=cutoff)


def render(
    records: list[dict],
    config: dict,
    time_range_label: str,
    latency_threshold_ms: int,
) -> str:
    responses = [r for r in records if r.get("event") == "response_sent"]
    requests = [r for r in records if r.get("event") == "request_received"]
    failures = [r for r in records if r.get("event") == "request_failed"]
    latencies = [float(r.get("latency_ms", 0)) for r in responses]
    ttfts = [float(r.get("ttft_ms", 0)) for r in responses]
    tool_events = [r for r in records if r.get("tool_success") is not None]
    success_rate = (
        100 * sum(r.get("tool_success") is True for r in tool_events) / len(tool_events)
        if tool_events
        else 100.0
    )
    error_rate = 100 * len(failures) / len(requests) if requests else 0.0
    cost = sum(float(r.get("cost_usd", 0)) for r in responses)
    tokens_in = sum(int(r.get("tokens_in", 0)) for r in responses)
    tokens_out = sum(int(r.get("tokens_out", 0)) for r in responses)
    quality = (
        sum(float(r.get("quality_score", 0)) for r in responses) / len(responses)
        if responses
        else 0.0
    )
    panels = [
        ("Latency percentiles and TTFT", f"P50 {percentile(latencies, 50):.0f} · P95 {percentile(latencies, 95):.0f} · P99 {percentile(latencies, 99):.0f}", f"TTFT P95 {percentile(ttfts, 95):.0f} ms · threshold ≤ {latency_threshold_ms} ms"),
        ("Request traffic", f"{len(requests)} requests", "count in selected window"),
        ("Error rate and retrieval success", f"Errors {error_rate:.2f}% · Retrieval {success_rate:.1f}%", "SLO errors ≤ 2% · retrieval ≥ 90%"),
        ("Cost over time", f"${cost:.6f}", "selected window total · threshold ≤ $2.50"),
        ("Input and output tokens", f"{tokens_in:,} input · {tokens_out:,} output", "unit tokens · threshold ≤ 50,000"),
        ("Quality proxy", f"{quality:.3f}", "score 0–1 · threshold ≥ 0.75"),
    ]
    cards = []
    for index, (title, value, detail) in enumerate(panels):
        x = 35 + (index % 2) * 565
        y = 145 + (index // 2) * 190
        cards.append(
            f'<g transform="translate({x} {y})"><rect width="530" height="155" rx="14" fill="#172033" stroke="#334155"/>'
            f'<text x="24" y="38" fill="#94a3b8" font-size="17">{html.escape(title)}</text>'
            f'<text x="24" y="88" fill="#f8fafc" font-size="27" font-weight="600">{html.escape(value)}</text>'
            f'<text x="24" y="125" fill="#60a5fa" font-size="15">{html.escape(detail)}</text></g>'
        )
    title = html.escape(config["dashboard"]["title"])
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="750" viewBox="0 0 1160 750">'
        '<rect width="1160" height="750" fill="#0b1120"/>'
        f'<text x="35" y="55" fill="#f8fafc" font-size="28" font-weight="600">{title}</text>'
        f'<text x="35" y="88" fill="#94a3b8" font-size="16">Time range: {html.escape(time_range_label)} · source: data/logs.jsonl</text>'
        f'<text x="35" y="115" fill="#64748b" font-size="13">Generated {generated} · {len(records)} structured log records</text>'
        + "".join(cards)
        + '</svg>'
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs", type=Path, default=REPO_ROOT / "data" / "logs.jsonl")
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "config" / "dashboard.yaml")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "submission" / "evidence" / "11-dashboard-overview.svg")
    parser.add_argument("--start", type=parse_datetime, help="Inclusive ISO-8601 start time for a focused snapshot")
    parser.add_argument("--end", type=parse_datetime, help="Inclusive ISO-8601 end time for a focused snapshot")
    parser.add_argument("--latency-threshold-ms", type=int, help="Override the dashboard latency threshold")
    args = parser.parse_args()
    if (args.start is None) != (args.end is None):
        parser.error("--start and --end must be provided together")
    if args.start is not None and args.end < args.start:
        parser.error("--end must be equal to or later than --start")

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if args.start is not None:
        records = load_logs(args.logs, start=args.start, end=args.end)
        time_range_label = f"{args.start.isoformat(timespec='seconds')} to {args.end.isoformat(timespec='seconds')}"
    else:
        minutes = config["dashboard"]["time_range_minutes"]
        records = load_recent_logs(args.logs, minutes)
        time_range_label = f"last {minutes} minutes"
    latency_threshold_ms = args.latency_threshold_ms
    if latency_threshold_ms is None:
        latency_panel = next(panel for panel in config["dashboard"]["panels"] if panel["id"] == "latency")
        latency_threshold_ms = latency_panel["threshold"]["value"]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(records, config, time_range_label, latency_threshold_ms), encoding="utf-8")
    print(f"Dashboard snapshot: {args.output} ({len(records)} records)")


if __name__ == "__main__":
    main()
