# Self-Hosted Renovate Bot (GitHub & Codeberg)

A GitHub Actions workflow to run a self-hosted Renovate bot instance that manages dependencies for repositories on both **GitHub** and **Codeberg**.

## Purpose

This project provides a template to easily set up and run your own Renovate bot without needing a dedicated server. It leverages GitHub Actions to run the Renovate CLI on a schedule, keeping your dependencies up-to-date across your projects.

## Features

-   **Multi-Platform Support:** Runs Renovate for both GitHub and Codeberg repositories in parallel.
-   **Serverless:** Runs entirely on GitHub Actions (no VPS required).
-   **Template Ready:** Designed to be used as a GitHub Repository Template.
-   **Secure:** Uses GitHub Apps and Secrets for authentication.
-   **Customizable:** Configurable via GitHub Repository Variables and a shared `renovate-config.js`.

## Getting Started

1.  **Use this Template:** Click the "Use this template" button to create a new repository from this one.
2.  **Configure:** Follow the detailed setup instructions in [SETUP.md](SETUP.md) to configure the necessary GitHub App, Codeberg Bot, and Repository Secrets.
3.  **Run:** The workflow is configured to run on a schedule (e.g., hourly) or manually via `workflow_dispatch`.

## Documentation

For complete installation and configuration instructions, please refer to the **[Setup Guide](SETUP.md)**.

## How It Works

The workflow defines a build matrix that spawns two jobs:
1.  **GitHub Job:** Authenticates as a GitHub App to manage GitHub repositories.
2.  **Codeberg Job:** Authenticates as a Codeberg Bot to manage Codeberg repositories.

Both jobs utilize the same [`renovate-config.js`](renovate-config.js) but adapt dynamically to the target platform using environment variables.

## Credits are References:
- [Renovate Github Action Runner](https://github.com/renovatebot/github-action)

## License
[AGPLv3 License](LICENSE)
