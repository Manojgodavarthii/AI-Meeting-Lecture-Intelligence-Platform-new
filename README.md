# EchoAction AI — Meeting-to-Action Platform

> **Project status: In active development**  
> EchoAction AI is a work-in-progress platform. Features, workflows, integrations, and the database schema may change. Some areas may be incomplete or require further testing.

## GitHub repository description

**A Flask-based meeting-to-action platform with AI-assisted transcription, meeting summaries, action items, project and workflow tools, role-based portals, and administrative security features. Currently under active development.**

## Overview

EchoAction AI is designed to help teams turn meeting recordings and discussions into useful follow-up work. The application combines meeting management, AI-assisted audio/video processing, collaboration tools, project tracking, and administration in one web interface.

The current codebase includes a Flask backend, a browser-based interface, MySQL database access, and optional desktop launching support through PyWebView.

## Main capabilities present in the codebase

- **Meeting workspace:** create and manage meeting records, review meeting information, and work with meeting-related content.
- **Audio/video processing:** supports common audio and video formats. The application uses OpenAI Whisper for speech transcription and FFmpeg/FFprobe for media processing and metadata.
- **Meeting intelligence:** UI and database structures cover transcripts, summaries, action items, meeting insights, replay, and related meeting material. The completeness and reliability of individual AI workflows are still being validated.
- **Collaboration:** messaging, notifications, user profiles, followers, profile links, and activity history.
- **Projects and work tracking:** project records, project documents, project members, project health, risks, reports, and task-related database structures.
- **Role-oriented portals:** the interface contains separate navigation areas for employee, student, staff, and administrator experiences. Exact access and feature availability depend on the configured account and permissions.
- **Administration:** user and staff management, queries, reports, permissions, role management, and system configuration.
- **Security-oriented features:** login history, security events, rate limiting, request validation, security headers, IP blocking utilities, and audit-related records.
- **Additional workspace tools:** calendar, task tracker, knowledge center, AI chat/command areas, workflow automation, report studio, and analytics-related sections are represented in the application.

> These items describe capabilities and modules visible in the supplied source code. They should not be interpreted as a guarantee that every screen, integration, or workflow is production-ready.

## Technology stack

| Area | Technologies |
|---|---|
| Backend | Python, Flask, Flask-CORS |
| Frontend | HTML, CSS, JavaScript |
| Database | MySQL (`mysql.connector`) |
| Speech processing | OpenAI Whisper, PyTorch |
| Media utilities | FFmpeg / FFprobe |
| Image utilities | Pillow, NumPy |
| Desktop wrapper | PyWebView |
| Security | Werkzeug utilities and project-specific security helpers |

## Repository structure

The structure below highlights the main application files and omits generated folders, dependencies, temporary debugging scripts, local media, and backup copies.

```text
project/
├── app.py                  # Flask application, routes, media and API workflows
├── db.py                   # MySQL connection pool, schema and database operations
├── models.py               # Application data/model definitions and helpers
├── security.py             # Security, validation, rate limiting and audit helpers
├── requirements.txt        # Python package requirements
├── desktop_app.py          # PyWebView desktop launcher
├── build_desktop.py        # Desktop build helper
├── launch_web.bat          # Windows web launch helper
├── launch_desktop.bat      # Windows desktop launch helper
├── migrate_db.py           # Database migration utility
├── recreate_db.py          # Database recreation utility
├── create_student_tables.py# Student-related table setup utility
├── test_security.py        # Security checks/tests
├── templates/
│   └── index.html          # Main application interface
└── static/
    ├── app.js              # Main frontend application logic
    ├── features-v2.js      # Additional frontend features
    ├── new-features.js     # Additional frontend interactions
    ├── security-center.js  # Security center interface logic
    ├── styles.css          # Main styles
    ├── new-features.css    # Additional styles
    └── font-awesome/       # Icon assets
```

## Getting started

### 1. Prerequisites

- Python 3.10 or newer (use a version compatible with your installed PyTorch and Whisper packages).
- MySQL Server.
- FFmpeg and FFprobe installed and available on your system `PATH` for media processing.
- Git.

### 2. Clone the repository

```bash
git clone https://github.com/<your-username>/<your-repository>.git
cd <your-repository>/project
```

Replace the URL placeholders with your actual GitHub repository URL. If you upload the contents of the `project` folder directly to the repository root, omit the final `/project` when changing directory.

### 3. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
pip install mysql-connector-python
```

`mysql-connector-python` is required by `db.py` but is not currently listed in the supplied `requirements.txt`.

PyTorch and Whisper can take time to install and may require platform-specific installation steps. Check their official installation guidance if installation fails.

### 5. Configure MySQL

Create a MySQL database named `echoaction` (or update the database name in the application configuration). The current `db.py` contains local connection defaults. Before publishing or deploying, replace those defaults with environment-based configuration and your own local credentials. Never commit database passwords.

The application attempts to initialize selected authentication and security tables when `app.py` is started. Other schema setup and migration utilities are included in the repository. Review them and back up any existing database before running migration or recreation scripts.

### 6. Configure secrets

Set a strong `SECRET_KEY` environment variable before running the app. Keep API keys, passwords, database credentials, and other secrets outside source control. Do not use sample or development credentials on a public deployment.

### 7. Run the application

From the directory containing `app.py`:

```bash
python app.py
```

By default, the Flask server is configured for:

```text
http://127.0.0.1:5003
```

Optional environment variables include:

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-secret"
$env:FLASK_HOST = "127.0.0.1"
$env:FLASK_PORT = "5003"
$env:FLASK_DEBUG = "0"
python app.py
```

### 8. Media processing notes

The project configures FFmpeg using a few Windows-specific locations and also expects FFmpeg tools to be available through `PATH`. For other environments, install FFmpeg and ensure both `ffmpeg` and `ffprobe` can be run from a terminal. Whisper model files may be downloaded the first time a model is loaded.

## Development status and known considerations

This repository is **still under development**. The current source includes ongoing UI and feature work, and the included TODO notes identify areas that still need verification. Do not assume every role-specific page, AI workflow, or integration has been fully tested.

Before using this project beyond local development:

- Verify every role and permission path.
- Test audio/video uploads with different file sizes and formats.
- Validate transcription, summaries, action items, and generated outputs against real examples.
- Review database schema creation and migration scripts.
- Move all credentials and secrets to environment variables.
- Add the missing MySQL connector package to `requirements.txt`.
- Add automated tests and deployment documentation.
- Configure secure cookies and production-grade server settings for HTTPS deployment.

## Important: clean the repository before pushing to GitHub

The supplied ZIP contains files that should **not** be committed as-is. In particular, it includes a local credentials file with passwords and API tokens, browser/session-related files, server logs, backup code, Python cache files, a large `node_modules` directory, and sample meeting media.

Before uploading:

1. Remove `login details.txt`, `cookies.txt`, logs, local database files, and any files containing passwords or API keys.
2. Rotate/revoke any API keys or passwords that were included in the ZIP or previously shared.
3. Remove `.opencode/node_modules/`, `__pycache__/`, temporary test/debug files, and obsolete backups unless they are intentionally required.
4. Add a `.gitignore` for virtual environments, caches, uploads, local configuration, logs, and secrets.
5. Check the Git staging area and run a secret scan before every push.

Suggested `.gitignore`:

```gitignore
.venv/
venv/
__pycache__/
*.py[cod]
node_modules/
.opencode/node_modules/
.env
.env.*
!.env.example
*.log
cookies.txt
login details.txt
uploads/
instance/
*.sqlite
*.db
.DS_Store
Thumbs.db
```

Do not upload real user recordings or private meeting content without permission.

## Author

**Godavarthi Naga Manoj Balaji**

- GitHub: [Manojgodavarthii](https://github.com/Manojgodavarthii)
- Project: EchoAction AI — Meeting-to-Action Platform

## License

No license file was present in the supplied project archive. Add a `LICENSE` file before making the repository openly reusable. Until a license is added, all rights remain with the copyright holder by default.

## Contributions and feedback

Suggestions, bug reports, and contributions are welcome. Since the project is under active development, please describe the issue clearly and include steps to reproduce it where possible.
