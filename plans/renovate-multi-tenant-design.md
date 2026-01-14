# Design Plan: Multi-Tenant Renovate Workflow (Matrix with Max-Parallel)

This plan implements the user's request to support multiple GitHub App installations using a dynamic matrix strategy, throttled by `max-parallel` to prevent CI queue flooding.

**Priority:** The static Forgejo platform will be prioritized in the matrix to ensure it runs first.

## 1. Overview

The solution involves splitting the workflow into two jobs:
1.  **`discover`**: A setup job that fetches all installations of the GitHub App and constructs a unified job matrix (Forgejo + GitHub).
2.  **`renovate`**: The main job that runs Renovate for each item in the matrix, with concurrency limited to 5 jobs at a time.

## 2. New Script: `.github/scripts/get-github-installations.py`

A Python script will be created to handle the interaction with the GitHub API.

**Responsibilities:**
*   Authenticate as the GitHub App using the App ID and Private Key (JWT).
*   Fetch the list of installations (`GET /app/installations`).
*   Construct a list of GitHub installation objects (extracting the `owner`).
*   Output the list as a JSON string.

**Inputs (Environment Variables):**
*   `RENOVATE_APP_ID`
*   `RENOVATE_PRIVATE_KEY`
*   `RENOVATE_USERNAME`

**Dependencies:**
*   `requests`
*   `pyjwt`
*   `cryptography`

## 3. Workflow Changes (`.github/workflows/renovate.yml`)

### Job 1: `discover`
*   **Runs-on**: `ubuntu-latest`
*   **Steps**:
    1.  Checkout code.
    2.  Set up Python.
    3.  Install dependencies (`pip install requests pyjwt cryptography`).
    4.  Run `.github/scripts/get-github-installations.py` to get the GitHub matrix.
    5.  **Merge with Forgejo Configuration**:
        *   Define the static Forgejo configuration JSON.
        *   **Prepend** Forgejo to the GitHub list (Forgejo first).
    6.  Set the combined JSON as a job output (`matrix`).

### Job 2: `renovate`
*   **Needs**: `discover`
*   **Strategy**:
    *   `fail-fast`: `false`
    *   **`max-parallel`: 5**
    *   `matrix`:
        *   `include`: `${{ fromJson(needs.discover.outputs.matrix) }}`
*   **Steps**:
    1.  Checkout.
    2.  Cache Renovate.
    3.  **Generate Token (GitHub only)**:
        *   Use `actions/create-github-app-token`.
        *   Condition: `if: matrix.platform == 'github'`
        *   Inputs:
            *   `app-id`: `${{ vars.RENOVATE_APP_ID }}`
            *   `private-key`: `${{ secrets.RENOVATE_PRIVATE_KEY }}`
            *   `owner`: `${{ matrix.owner }}`
        *   Output: `steps.app-token.outputs.token`
    4.  **Run Renovate**:
        *   Update `token` input to use the generated token for GitHub, or the secret for Forgejo.
        *   Update `env` variables to use matrix values.

## 4. Matrix Structure

The final combined JSON output from the discovery job will look like this (Forgejo first):

```json
[
  {
    "platform": "forgejo",
    "owner": null,
    "endpoint": "https://codeberg.org/api/v1",
    "renovate_username": "codeberg-bot",
    "git_author": "codeberg-bot <...>"
  },
  {
    "platform": "github",
    "owner": "org-name-1",
    "endpoint": "",
    "renovate_username": "renovate-bot",
    "git_author": "renovate-bot[bot] <...>"
  },
  {
    "platform": "github",
    "owner": "org-name-2",
    "endpoint": "",
    "renovate_username": "renovate-bot",
    "git_author": "renovate-bot[bot] <...>"
  }
]
```

## 5. Implementation Details

### Python Script Pseudocode (`get-github-installations.py`)

```python
import os
import time
import json
import jwt
import requests

def get_jwt(app_id, private_key):
    payload = {
        'iat': int(time.time()),
        'exp': int(time.time()) + 600,
        'iss': app_id
    }
    return jwt.encode(payload, private_key, algorithm='RS256')

def main():
    app_id = os.environ['RENOVATE_APP_ID']
    private_key = os.environ['RENOVATE_PRIVATE_KEY']
    
    # 1. Get GitHub Installations
    token = get_jwt(app_id, private_key)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    resp = requests.get("https://api.github.com/app/installations", headers=headers)
    installations = resp.json()

    matrix = []

    # 2. Add GitHub entries
    for inst in installations:
        owner = inst['account']['login']
        matrix.append({
            "platform": "github",
            "owner": owner,
            "endpoint": "",
            "renovate_username": os.environ.get('RENOVATE_USERNAME'),
            "git_author": f"{os.environ.get('RENOVATE_USERNAME')}[bot] <{app_id}+{os.environ.get('RENOVATE_USERNAME')}[bot]@users.noreply.github.com>"
        })

    # 3. Output only GitHub entries
    print(json.dumps(matrix))

if __name__ == "__main__":
    main()
```

### Workflow YAML Updates

```yaml
jobs:
  discover:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - run: pip install requests pyjwt cryptography
      - name: Generate Matrix
        id: set-matrix
        env:
          RENOVATE_APP_ID: ${{ vars.RENOVATE_APP_ID }}
          RENOVATE_PRIVATE_KEY: ${{ secrets.RENOVATE_PRIVATE_KEY }}
          RENOVATE_USERNAME: ${{ vars.RENOVATE_USERNAME }}
          CODEBERG_BOT_USERNAME: ${{ vars.CODEBERG_BOT_USERNAME }}
        run: |
          # 1. Get Dynamic GitHub Matrix
          GITHUB_JSON=$(python .github/scripts/get-github-installations.py)
          
          # 2. Define Static Forgejo Matrix
          # Note: We use jq to safely construct the JSON object
          FORGEJO_JSON=$(jq -n \
            --arg platform "forgejo" \
            --arg endpoint "https://codeberg.org/api/v1" \
            --arg renovate_username "$CODEBERG_BOT_USERNAME" \
            --arg git_author "$CODEBERG_BOT_USERNAME <$CODEBERG_BOT_USERNAME@noreply.codeberg.org>" \
            '{platform: $platform, owner: null, endpoint: $endpoint, renovate_username: $renovate_username, git_author: $git_author}')

          # 3. Combine and Output
          # We wrap Forgejo in an array [ $FORGEJO_JSON ] and PREPEND it to the GitHub array
          # This ensures Forgejo runs first
          COMBINED_JSON=$(echo "$GITHUB_JSON" | jq --argjson fj "$FORGEJO_JSON" '[$fj] + .')
          
          echo "matrix=$COMBINED_JSON" >> $GITHUB_OUTPUT

  renovate:
    needs: discover
    runs-on: ubuntu-latest
    concurrency:
      group: renovate-${{ matrix.platform }}-${{ matrix.owner }}
      cancel-in-progress: false
    strategy:
      fail-fast: false
      max-parallel: 5
      matrix:
        include: ${{ fromJson(needs.discover.outputs.matrix) }}
    
    steps:
      - name: Checkout
        uses: actions/checkout@v6.0.1

      - name: Cache Renovate
        uses: actions/cache@v5.0.1
        with:
          path: /tmp/renovate
          key: renovate-${{ matrix.platform }}-${{ github.run_id }}
          restore-keys: |
            renovate-${{ matrix.platform }}-

      - name: Fix Cache Permissions
        run: |
          sudo mkdir -p /tmp/renovate
          sudo chown -R 12021:0 /tmp/renovate

      # Run Renovate (GitHub)
      - name: Make entrypoint executable
        run: chmod +x .github/renovate-entrypoint.sh

      - name: Get GitHub App Token
        if: matrix.platform == 'github'
        uses: actions/create-github-app-token@v1
        id: app-token
        with:
          app-id: ${{ vars.RENOVATE_APP_ID }}
          private-key: ${{ secrets.RENOVATE_PRIVATE_KEY }}
          owner: ${{ matrix.owner }}

      - name: Self-hosted Renovate
        uses: renovatebot/github-action@v44.2.4
        with:
          configurationFile: renovate-config.js
          token: ${{ matrix.platform == 'github' && steps.app-token.outputs.token || secrets.CODEBERG_TOKEN }}
          renovate-version: 42.80.2-full
          docker-cmd-file: .github/renovate-entrypoint.sh
        env:
          RENOVATE_PLATFORM: ${{ matrix.platform }}
          RENOVATE_ENDPOINT: ${{ matrix.endpoint }}
          RENOVATE_USERNAME: ${{ matrix.renovate_username }}
          RENOVATE_GIT_AUTHOR: ${{ matrix.git_author }}
          RENOVATE_AUTODISCOVER_FILTER: ${{ vars.RENOVATE_AUTODISCOVER_FILTER }}
          LOG_LEVEL: debug

      - name: Fix Cache Permissions for Save
        if: always()
        run: |
          sudo chown -R $USER /tmp/renovate