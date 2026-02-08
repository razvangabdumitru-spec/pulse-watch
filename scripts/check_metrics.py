#!/usr/bin/env python3
import os
import json
import sys
from urllib import request, parse

REPO = os.environ.get("GITHUB_REPOSITORY")  # owner/repo
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

DAILY_PATH = "metrics/daily.json"
BASELINE_PATH = "metrics/baseline.json"

RULES = [
    ("high_error_rate", lambda d: d.get("error_rate", 0) > 0.025),
    ("latency_spike", lambda d: d.get("p95_latency_ms", 0) >= 900),
    ("traffic_drop", lambda d: d.get("requests", 0) < 120000),
    ("cpu_saturation", lambda d: d.get("cpu_avg", 0) >= 0.80),
    ("memory_regression", lambda d: d.get("memory_mb", 0) >= 7200),
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def comparisons(daily, baseline):
    lines = []
    for k in ["requests", "error_rate", "p95_latency_ms", "cpu_avg", "memory_mb"]:
        dv = daily.get(k)
        bv = baseline.get(k)
        if dv is None or bv is None:
            continue
        try:
            if isinstance(dv, float) or isinstance(bv, float):
                delta = dv - bv
                lines.append(f"{k}: {dv} vs baseline {bv} (delta {delta:+.3f})")
            else:
                delta = dv - bv
                lines.append(f"{k}: {dv} vs baseline {bv} (delta {delta:+d})")
        except Exception:
            lines.append(f"{k}: {dv} vs baseline {bv}")
    return lines


def create_issue(owner, repo, title, body):
    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN not set; cannot create issue.")
        return None
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    data = json.dumps({"title": title, "body": body}).encode("utf-8")
    req = request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    try:
        with request.urlopen(req) as resp:
            resp_data = resp.read().decode("utf-8")
            j = json.loads(resp_data)
            print(f"Created issue: {j.get('html_url')}")
            return j
    except Exception as e:
        print("Failed to create issue:", e)
        try:
            resp = e.read().decode()
            print(resp)
        except Exception:
            pass
        return None


def main():
    try:
        daily = load_json(DAILY_PATH)
    except Exception as e:
        print("Failed to load daily.json:", e)
        sys.exit(1)
    try:
        baseline = load_json(BASELINE_PATH)
    except Exception:
        baseline = {}

    date = daily.get("date", "unknown")
    print(f"Date: {date}")

    # comparisons
    print("Comparisons (daily vs baseline):")
    for line in comparisons(daily, baseline):
        print("- "+line)

    # Evaluate rules in exact order
    triggered = []
    for name, fn in RULES:
        try:
            if fn(daily):
                triggered.append(name)
        except Exception as e:
            print(f"Error evaluating rule {name}:", e)

    if triggered:
        print("Anomalies detected:")
        for r in triggered:
            print("- "+r)
        first = triggered[0]
        title = f"ALERT: {first}"
        # Build body
        body_lines = []
        body_lines.append(f"Date: {date}")
        body_lines.append("")
        body_lines.append("Triggered rules:")
        for r in triggered:
            body_lines.append(f"- {r}")
        body_lines.append("")
        body_lines.append("Raw daily.json:")
        body_lines.append("```json")
        body_lines.append(json.dumps(daily, indent=2))
        body_lines.append("```")
        body = "\n".join(body_lines)

        # Create issue via GitHub API
        if REPO and "/" in REPO:
            owner, repo = REPO.split("/")
            create_issue(owner, repo, title, body)
        else:
            print("GITHUB_REPOSITORY environment variable missing or malformed; cannot create issue.")
    else:
        print("No anomalies detected. No issue will be created.")


if __name__ == "__main__":
    main()
