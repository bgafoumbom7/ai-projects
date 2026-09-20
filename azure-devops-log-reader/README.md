# Azure DevOps Log Reader

A command-line tool for reading, inspecting and diagnosing Azure DevOps pipeline deployment logs. It talks to the Azure DevOps REST API directly (no `az` CLI needed) and can optionally hand a failed run to Claude for a plain-language explanation.

```
$ python azdo_logs.py show 4821

Run 4821 · webapp-deploy · failed
Branch: refs/heads/main  Commit: 9f3c2a1e

✔ [Stage] Build  4m07s
  ✔ [Job] Build and test  4m02s
    ✔ [Task] Checkout  12s
    ✔ [Task] npm install  1m18s
    ✔ [Task] npm run build  1m49s
    ✔ [Task] Publish artifact  38s
✘ [Stage] Deploy to Production  4m15s
  ✘ [Job] Deploy webapp  3m31s
    ✔ [Task] Download artifact  14s
    ✘ [Task] Azure Web App Deploy: webshop-prod  3m01s
        ↳ Error: Failed to deploy web package to App Service.
    – [Task] Smoke test
```

## Try it without credentials

Sample data from a failed deployment is bundled, so every command works offline with `--demo`:

```bash
pip install requests
python azdo_logs.py --demo runs
python azdo_logs.py --demo show 4821
python azdo_logs.py --demo errors 4821
```

## Connect to your own organisation

1. Create a Personal Access Token at `https://dev.azure.com/<org>/_usersSettings/tokens` with the **Build (Read)** scope.
2. Set the environment (or copy `.env.example`):

```bash
export AZDO_ORG=my-org
export AZDO_PROJECT=my-project
export AZDO_PAT=xxxxxxxx
```

## Commands

| Command | What it does |
|---|---|
| `runs [--pipeline NAME] [--top N] [--failed]` | List recent runs, newest first |
| `show RUN_ID` | Stage → job → task tree with results, durations and error issues |
| `errors RUN_ID` | Pull the log of every failed task and print just the error lines (with context) |
| `logs RUN_ID [--out DIR] [--task TEXT]` | Download the raw log of every task to a folder |
| `summarize RUN_ID` | Send the failure to Claude and get: what failed, likely root cause, next steps |

`summarize` needs `pip install anthropic` and `ANTHROPIC_API_KEY`.

## How it works

- **Runs** come from `GET /_apis/build/builds` — in Azure DevOps, YAML pipeline runs (including deployment jobs) are builds under the hood.
- **Structure** comes from the run's *timeline* (`/builds/{id}/timeline`), a flat list of records with `parentId` pointers that the tool reassembles into a tree. Each task record carries its `result`, any `issues` the task raised, and the ID of its log.
- **Logs** come from `/builds/{id}/logs/{logId}` as plain text. The tool strips the ISO timestamps that prefix every line and greps for `##[error]`, `npm ERR!`, exceptions, `failed`, `exit code N` and similar markers.
- **Summaries** send only the failed tasks' issues and error excerpts to Claude, not whole logs, to keep the prompt small and focused.

## Tests

```bash
python test_azdo_logs.py      # or: python -m pytest
```

## Ideas to extend

- Classic Release pipelines use a separate API (`vsrm.dev.azure.com/.../_apis/release/deployments`); adding a `releases` command is the natural next step
- Poll a running deployment and stream its log live
- Post `summarize` output to Teams or Slack when a run fails
