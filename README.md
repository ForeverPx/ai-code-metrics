# Git AI Code Stats

**[中文](README_ZH.md)**

<img width="2120" height="1020" alt="image" src="https://github.com/user-attachments/assets/89c97370-5845-4122-8454-e993e21f5b5a" />

Teams use Cursor, Copilot, and other AI tools to write code—but rarely know *how much* of the codebase is AI-generated. This tool uses [git-ai](https://github.com/git-ai-project/git-ai) Git Notes (`refs/notes/ai`) to pull commits and AI attribution from GitLab, then computes **AI code ratio** by time range, repo, or department. Results are shown in tables and charts for review, reporting, and trend tracking.

**Built on [git-ai](https://github.com/git-ai-project/git-ai)** (a Git extension for tracking AI-generated code) and its [Git AI Standard](https://github.com/git-ai-project/git-ai).

## Features

- AI code ratio across multiple repos within a date range
- Department/group config with filtering by group
- Summary stats plus per-repo details (lines, commits, ratio)
- Dark-themed web UI with date picker and result charts

## Requirements

- Python 3.8+
- A GitLab instance with Git Notes `refs/notes/ai` (e.g. from Cursor or other AI coding tools that write AI line data)

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy the example env file and set your GitLab token:

```bash
cp .env.example .env
# Edit .env and set GITLAB_PRIVATE_TOKEN
```

| Variable | Required | Description |
|----------|----------|-------------|
| `GITLAB_PRIVATE_TOKEN` | Yes | GitLab Personal Access Token with `read_api` and `read_repository` |
| `GITLAB_BASE_URL` | No | GitLab base URL; default `https://gitlab.com` |
| `GIT_AI_REPOS_CONFIG` | No | Path to repos config JSON; default `repos_config.json` in project root |

### 3. Configure repository list

Edit `repos_config.json`.

**Simple format (no groups):**

```json
{
  "repos": [
    {
      "id": "123456",
      "name": "My Project",
      "branch": "main"
    }
  ]
}
```

**By department/group:**

```json
{
  "Frontend": [
    { "id": "111", "name": "web-app", "branch": "main" }
  ],
  "Backend": [
    { "id": "222", "name": "api-server", "branch": "master" }
  ]
}
```

- `id`: GitLab project ID (from project page or URL)
- `name`: Display name
- `branch`: Branch to analyze

### 4. Run the app

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser, pick a date range and optional department, then click the start button to run the stats.

## How it works

1. **Commits**: GitLab API returns commits in the given time range per repo/branch, with `additions` and `deletions`.
2. **AI Notes**: For each commit, the app fetches the Note under `refs/notes/ai`; if present, it parses the JSON.
3. **Stats**: It aggregates `accepted_lines` (AI-accepted lines) and `additions` (total new lines) per commit and computes the ratio.

The AI note format must match what Cursor and similar tools write (e.g. `prompts` and each prompt’s `accepted_lines`).

## Project structure

```
.
├── app.py              # Flask entry
├── git_ai_stats.py     # Stats and API logic
├── index.html          # Frontend
├── repos_config.json   # Repo config (you configure this)
├── requirements.txt
├── .env.example
├── README.md
└── README_ZH.md
```

## License

MIT
