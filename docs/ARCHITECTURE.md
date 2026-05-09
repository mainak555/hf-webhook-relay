# Architecture

## Overview

This project is a lightweight relay between Hugging Face webhook events and GitHub Actions.

The service:

1. Authenticates the incoming webhook using a shared secret.
2. Checks whether the source HF repo/repo type is allowed.
3. Detects whether tracked files changed on the latest commit.
4. Sends a `repository_dispatch` event to a configured GitHub repository.

## System Context

```mermaid
flowchart LR
    HF[Hugging Face Repo Webhook] --> RELAY[HF Webhook Relay FastAPI]
    RELAY --> HFApi[Hugging Face Hub API]
    RELAY --> GHApi[GitHub REST API]
    GHApi --> GHA[GitHub Actions Workflow]
```

## Request Sequence

```mermaid
sequenceDiagram
    participant HF as Hugging Face
    participant API as Relay API (/v1/github_hook)
    participant HUB as Hugging Face Hub API
    participant GH as GitHub API

    HF->>API: POST webhook + x_webhook_secret + query params
    API->>API: Validate secret
    alt Secret invalid
        API-->>HF: 401 Invalid Secret
    else Secret valid
        API->>API: Validate hf_repo and hf_repo_type in TRACKING_PATHS
        alt Not tracked
            API-->>HF: {filtered: true}
        else Tracked
            API->>HUB: list_repo_commits(...)
            HUB-->>API: latest commit
            API->>HUB: list_repo_tree(..., expand=true)
            HUB-->>API: file tree with last_commit metadata
            API->>API: Compute changed files for latest commit
            alt No tracked files changed
                API-->>HF: {ignored: true}
            else Tracked file changed
                API->>GH: POST /repos/{owner}/{repo}/dispatches
                GH-->>API: 2xx/4xx
                API-->>HF: {success: true}
            end
        end
    end
```

## Component Responsibilities

- `app/app.py`: FastAPI entrypoint and relay control flow.
- `app/watch_list.py`: static whitelist of tracked repositories and file paths.
- `deploy-app.py`: Hugging Face Space bootstrap, secret injection, and app upload.
- `.github/workflows/pipeline.yml`: CI/CD deployment trigger and execution.
- `app/Dockerfile`: runtime image constraints used in Hugging Face Space.

## Runtime Inputs

- `HF_WEBHOOK_SECRET`: shared secret for inbound request gate.
- `HF_TOKEN`: token used to query HF repository metadata.
- `GH_PAT`: token used for GitHub dispatch API.

## Current Constraints

- Source logic is tightly coupled to Hugging Face APIs.
- Tracking config is static in code (`app/watch_list.py`).
- No built-in retry/rate-limit/replay-defense layer.

## Extension Direction

To support additional webhook providers where Hugging Face is not involved:

1. Add source adapters (`verify`, `extract_event`, `changed_files`).
2. Normalize provider output into a common relay event model.
3. Keep GitHub dispatch in a dedicated sender service.
4. Replace static watch list with config backend (file/env/store).
