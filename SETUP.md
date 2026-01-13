# Renovate Bot Setup Guide

This guide explains how to set up the self-hosted Renovate bot for both GitHub and Codeberg using the provided GitHub Actions workflow.

## Prerequisites

- A GitHub repository to host this workflow.
- A GitHub App for the GitHub integration.
- A Codeberg Bot Account for the Codeberg integration.

## Configuration

### 1. GitHub App (for GitHub)

1.  Create a new GitHub App in your organization or personal account.
2.  Grant the following permissions:
    *   **Repository permissions:**
        *   `Contents`: Read & Write
        *   `Pull requests`: Read & Write
        *   `Issues`: Read & Write
        *   `Metadata`: Read-only
        *   `Workflows`: Read & Write (if you want Renovate to update workflow files)
3.  Generate a Private Key for the App.
4.  Note the **App ID**.
5.  Install the App on the repositories you want Renovate to manage.

### 2. Codeberg Bot Account (for Codeberg)

1.  Create a new account on Codeberg to act as your bot (e.g., `my-renovate-bot`).
2.  Generate an Access Token (Settings -> Applications -> Generate Token).
    *   **Required Scopes:** Select **`repository`** and **`issue`**.
    *   Ensure you grant **Read & Write** access for both.
3.  Add this bot account as a **Collaborator** to the Codeberg repositories you want to manage.

### 3. GitHub Repository Secrets

Add the following secrets to your GitHub repository (Settings -> Secrets and variables -> Actions):

| Secret Name | Description |
| :--- | :--- |
| `RENOVATE_PRIVATE_KEY` | The content of the Private Key file (.pem) you generated for your GitHub App. |
| `CODEBERG_TOKEN` | The Access Token for your Codeberg bot account. |

### 4. GitHub Repository Variables

Add the following variables to your GitHub repository (Settings -> Secrets and variables -> Actions -> Variables):

| Variable Name | Description | Example |
| :--- | :--- | :--- |
| `RENOVATE_APP_ID` | The App ID of your GitHub App. | `123456` |
| `RENOVATE_USERNAME` | The username of your GitHub App bot (without `[bot]`). | `my-renovate-app` |
| `CODEBERG_BOT_USERNAME` | The username of your Codeberg bot account. | `my-renovate-bot` |
| `RENOVATE_AUTODISCOVER_FILTER` | (Optional) Filter string to limit which repos are discovered. | `user/*` |

**Example `RENOVATE_AUTODISCOVER_FILTER`:**
*   `user/*` (All repos owned by `user` - e.g., your personal username or organization name)
*   `{user1,user2}/*` (All repos owned by `user1` OR `user2` - useful if your GitHub and Codeberg usernames differ)
*   `org/repo-name` (Specific repo only)
*   `!org/exclude-repo` (Exclude specific repo)

### Warning!
- If you plan to make the instance publicly available and without autodiscover filters, read and understand [renovate security best practise] first!(https://docs.renovatebot.com/security-and-permissions)

## How it Works

The workflow uses a **Build Matrix** to run two parallel jobs:

1.  **GitHub Job:**
    *   Uses `actions/create-github-app-token` to generate a short-lived token from your GitHub App credentials.
    *   Configures Renovate to use the GitHub platform.
    *   Uses the App's identity for commits and PRs.

2.  **Codeberg Job:**
    *   Uses the `CODEBERG_TOKEN` secret for authentication.
    *   Configures Renovate to use the Codeberg platform (`https://codeberg.org/api/v1`).
    *   Uses the configured Bot username and email for commits.

Both jobs use the same `renovate-config.js` file, which dynamically adapts based on the environment variables set by the workflow.