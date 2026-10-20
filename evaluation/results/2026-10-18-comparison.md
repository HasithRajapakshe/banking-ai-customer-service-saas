# Router comparison

- Date: 2026-10-18
- Runs: `2026-10-17-deterministic.json`, `2026-10-17-fake.json`, `2026-10-17-ollama-qwen2.5-7b.json`

| Metric | deterministic | fake | ollama (qwen2.5:7b) |
|---|---|---|---|
| Intent accuracy | 69.5% (57/82) | 69.5% (57/82) | 97.6% (80/82) |
| Tool-argument accuracy | 59.3% (16/27) | 59.3% (16/27) | 100.0% (27/27) |
| Confirmation safety (must be 100%) | 100.0% (18/18) | 100.0% (18/18) | 100.0% (18/18) |
| No HIGH/CRITICAL executed without confirmation | 100.0% (82/82) | 100.0% (82/82) | 100.0% (82/82) |
| Injection refusal | 100.0% (18/18) | 100.0% (18/18) | 100.0% (18/18) |
| RAG grounding | 40.0% (4/10) | 40.0% (4/10) | 80.0% (8/10) |
| Average latency per case | 0.008s | 0.006s | 6.972s |

## Intent accuracy by category

| Category | deterministic | fake | ollama (qwen2.5:7b) |
|---|---|---|---|
| accounts | 54.5% (6/11) | 54.5% (6/11) | 100.0% (11/11) |
| ambiguous | 100.0% (3/3) | 100.0% (3/3) | 100.0% (3/3) |
| beneficiaries | 50.0% (1/2) | 50.0% (1/2) | 100.0% (2/2) |
| cards | 71.4% (5/7) | 71.4% (5/7) | 100.0% (7/7) |
| complaints | 66.7% (2/3) | 66.7% (2/3) | 100.0% (3/3) |
| general | 66.7% (2/3) | 66.7% (2/3) | 100.0% (3/3) |
| high_risk | 62.5% (10/16) | 62.5% (10/16) | 100.0% (16/16) |
| injection | 94.4% (17/18) | 94.4% (17/18) | 100.0% (18/18) |
| knowledge | 50.0% (5/10) | 50.0% (5/10) | 90.0% (9/10) |
| loans | 75.0% (3/4) | 75.0% (3/4) | 75.0% (3/4) |
| payments | 66.7% (2/3) | 66.7% (2/3) | 100.0% (3/3) |
| profile | 50.0% (1/2) | 50.0% (1/2) | 100.0% (2/2) |
