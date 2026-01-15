# Renovate Bot Setup Guide

This guide explains how to set up the self-hosted Renovate bot for both GitHub and Codeberg using the provided GitHub Actions workflow.

## Prerequisites

- A GitHub repository to host this workflow.
- A GitHub App for the GitHub integration.
- A Codeberg Bot Account for the Codeberg integration.

***

## Configuration

### 1. GitHub App (for GitHub)

1.  Create a new GitHub App in your organization or personal account.
2.  Grant the following permissions, based on [official renovate docs](https://docs.renovatebot.com/modules/platform/github/#running-as-a-github-app):
    *   `Administration`: Read
    *   `Checks`: Read & Write
    *   `Commit statuses`: Read & Write
    *   `Contents`: Read & Write
    *   `Dependabot alerts`: Read
    *   `Issues`: Read & Write
    *   `Members`: Read
    *   `Metadata`: Read (required to discover installations)
    *   `Pull requests`: Read & Write
    *   `Workflows`: Read & Write (if you want Renovate to update workflow files)
3.  Generate a Private Key for the App.
4.  Note the **App ID**.
5.  Install the App on the repositories you want Renovate to manage.
> [!IMPORTANT]
> You **MUST** also install the App on the repository hosting the workflow. The workflow needs to generate an installation token to automatically fetch github `BOT_USER_ID` (different from `GOTHUB_APP_ID`) and github `APP_SLUG`

### 2. Codeberg Bot Account (for Codeberg)

1.  Create a new account on Codeberg to act as your bot (e.g., `my-renovate-bot`).
2.  Generate an Access Token (Settings -> Applications -> Generate Token).
    *   **Required Scopes:**
        *   `read:organization`
        *   `write:issue`
        *   `write:repository`
        *   `read:user`
3.  Add this bot account as a **Collaborator** to the Codeberg repositories you want to manage.

### 3. GitHub Repository Secrets

Add the following secrets to your GitHub repository at the **Repository level** (Settings -> Secrets and variables -> Actions -> **Secrets** tab -> **Repository secrets**):

| Secret Name | Description |
| :--- | :--- |
| `GOTHUB_PRIVATE_KEY` | The content of the Private Key file (.pem) you generated for your GitHub App. |
| `CODEBERG_TOKEN` | The Access Token for your Codeberg bot account. |

### 4. GitHub Repository Variables

Add the following variables to your GitHub repository at the **Repository level** (Settings -> Secrets and variables -> Actions -> **Variables** tab -> **Repository variables**):

> [!NOTE]
> The following configuration values can be defined as either **Variables** or **Secrets**. The workflow will check for a Secret first, and if not found, will look for a Variable. This allows you to hide sensitive configuration (like `GOTHUB_APP_ID` or `CODEBERG_BOT_USERNAME`) if you prefer.

| Variable Name | Description | Example |
| :--- | :--- | :--- |
| `GOTHUB_APP_ID` | The App ID of your GitHub App. | `123456` |
| `CODEBERG_BOT_USERNAME` | The username of your Codeberg bot account. | `my-renovate-bot` |
| `RENOVATE_AUTODISCOVER_FILTER` | (Optional) Filter string to limit which repos are discovered. | `user/*` |
| `GOTHUB_INSTALLATION_WHITELIST` | (Optional) A comma-separated list of GitHub App Installation IDs or Owner names to explicitly run on. If not set, Renovate will run on all installations it discovers. | `12345,MyOrg` |
| `RENOVATE_HASH_ALL_NAMESPACES` | (Optional) If set to `true`, all namespace names (org/user) will be hashed in the GitHub Action job names. | `true` |
| `LOG_LEVEL` | (Optional) Sets the log level for Renovate. Defaults to `fatal`. Possible values: `debug`, `info`, `warn`, `error`, `fatal`. | `debug` |
| `MATRIX_MAX_PARALLEL` | (Optional) The maximum number of Renovate jobs to run in parallel. Defaults to `5`. | `10` |

**Example `RENOVATE_AUTODISCOVER_FILTER`:**
*   `user/*` (All repos owned by `user` - e.g., your personal username or organization name)
*   `{user1,user2}/*` (All repos owned by `user1` OR `user2` - useful if your GitHub and Codeberg usernames differ)
*   `org/repo-name` (Specific repo only)
*   `!org/exclude-repo` (Exclude specific repo)

### Namespace Hashing

To protect privacy, the workflow automatically hashes the names of **private** namespaces (organizations or users) in the GitHub Actions job names.
If you want to hash **all** namespaces (including public ones), set the `RENOVATE_HASH_ALL_NAMESPACES` variable to `true`.

### Warning on `LOG_LEVEL`
> [!WARNING]
> Using `debug` or `info` for the `LOG_LEVEL` variable can be dangerous if you are running this workflow on a public repository. These levels can leak repository names, namespace information, and other sensitive details into the public action logs (both in the `discover` and `renovate` jobs). It is highly recommended to use `warn`, `error`, or `fatal` for public repositories to avoid unintentional data exposure.

### Warning on Large Number of Installations
> [!WARNING]
> This workflow spawns a new runner for each GitHub App installation (each organization or user is a separate installation). The number of parallel runners is controlled by the `MATRIX_MAX_PARALLEL` variable. GitHub Actions has a limit of 256 jobs in a matrix. If your GitHub App is installed in more than 256 namespaces, the workflow will fail.
>
> Furthermore, running a very large number of jobs might lead to your account being flagged or even banned by GitHub.
>
> It is **highly recommended** to use the `GOTHUB_INSTALLATION_WHITELIST` variable to limit the number of installations the workflow runs on, especially if your GitHub App is public.

### Warning on public instances
> [!WARNING]
> If you plan to make the instance publicly available and without autodiscover filters, read and understand [renovate security-and-permissions](https://docs.renovatebot.com/security-and-permissions) first!

***

## How it Works

The workflow has been updated to support multi-tenant GitHub App installations. It now runs in two stages:

1.  **`discover` Job:**
    *   This job runs first and connects to the GitHub API as the GitHub App.
    *   It fetches a list of all installations where the App is installed.
    *   It filters this list based on the `GOTHUB_INSTALLATION_WHITELIST` variable, if it's set.
    *   It dynamically generates a JSON matrix of configurations, with one entry for each installation (and a static one for Codeberg).

2.  **`renovate` Job (Matrix Execution):**
    *   This job uses the matrix generated by the `discover` job.
    *   It runs a separate Renovate instance for each entry in the matrix in parallel.
    *   **For GitHub:** It authenticates using a short-lived installation token for the specific installation (`owner`).
    *   **For Codeberg:** It uses the static `CODEBERG_TOKEN` for authentication.

3.  **Bot Identity:**
    *   The bot's username and git author identity are automatically determined.
    *   **GitHub:** Uses the GitHub App's slug and internal ID to format the author as `app-slug[bot] <id+app-slug[bot]@users.noreply.github.com>`.
    *   **Codeberg:** Uses the `CODEBERG_BOT_USERNAME` and formats the author as `username <username@noreply.codeberg.org>`.

This approach allows a single workflow to manage multiple organizations or user accounts while maintaining secure, automated authentication and correct commit attribution.
