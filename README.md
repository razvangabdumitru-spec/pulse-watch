pulse-watch

Lightweight GitHub-based monitoring/alerting workflow.

What it does
- On a schedule (daily at 09:00 UTC), on-demand (workflow_dispatch), and on push, a GitHub Actions workflow reads metrics/daily.json and evaluates a small set of anomaly rules.
- If any rule triggers, the workflow creates a GitHub issue in this repository. The issue title is "ALERT: <rule_name>" where <rule_name> is the first triggered rule (evaluated in a fixed order). The issue body includes the date, a bullet list of triggered rules, and the raw daily JSON.

Files
- metrics/daily.json: the daily snapshot of metrics (this is the file the rules are evaluated against).
- metrics/baseline.json: baseline metrics used for printing comparisons only (rules are evaluated on daily.json only).
- scripts/check_metrics.py: the script that reads metrics, prints comparisons, evaluates rules, and creates an issue via the GitHub API if needed.
- .github/workflows/monitor.yml: GitHub Actions workflow that runs the script on schedule and on demand.

Anomaly rules (evaluated in this exact order):
1) high_error_rate: error_rate > 0.025
2) latency_spike: p95_latency_ms >= 900
3) traffic_drop: requests < 120000
4) cpu_saturation: cpu_avg >= 0.80
5) memory_regression: memory_mb >= 7200

Updating thresholds
- To update thresholds or rule order, edit scripts/check_metrics.py. The RULES list at the top defines the rule names, evaluation lambdas, and order.

Notes
- The script uses only the standard library and the GITHUB_TOKEN provided by Actions to create issues via the GitHub API.
- The workflow requests issues: write permission so it can create issues automatically.
