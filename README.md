# 🎓 English Self-Assessment Web Platform

A production-ready, interactive web application built with Streamlit and SQLite for English language self-assessment. Designed for students, test-takers, and educators to evaluate and improve English proficiency across **Grammar**, **Reading Comprehension**, and **Listening Comprehension**.

---

## 🌟 Key Capabilities

- **Three Dedicated Assessment Pillars**:
  - **Grammar Mastery**: Dynamic question selection, zero duplicates, shuffled distractors, and immediate explanations.
  - **Reading Comprehension**: Passage analysis, multi-question context linking, and question-type targeting.
  - **Listening Comprehension**: Natural audio dialogue/lecture playback, transcripts, and clue retention.
- **Rule-Based Pedagogical Difficulty Classification**: Easy, Medium, and Hard tiers evaluated across linguistic criteria.
- **Admin Management Portal**:
  - Role-based authorization (`superadmin` and `admin`) with `bcrypt` password hashing.
  - Question CRUD, bulk status toggles, and archival.
  - DOCX (`.docx`) and Excel (`.xlsx`) question bank import/export pipelines with validation preview.
  - Question-level performance analytics (attempts, accuracy, and difficulty calibration alerts).
- **Personalized History & Self-Assessment Summary**:
  - Longitudinal performance tracking and category breakdowns.
  - Trend evaluation and clear, descriptive feedback with non-certification disclosures.

---

## 📁 Project Directory Structure

```text
english_self_assessment/
├── .streamlit/
│   ├── config.toml               # Streamlit server, browser & theme configuration
│   └── secrets.toml.example      # Template for environment secrets
├── app.py                        # Landing page entry point
├── config/
│   └── settings.py               # Central paths, directories & runtime settings
├── database/
│   ├── db.py                     # SQLite connection manager & idempotent init
│   ├── schema.py                 # DDL tables, indexes, constraints & seeds
│   ├── models.py                 # Dataclass entities (User, Admin, Question, etc.)
│   └── queries.py                # Parameterized SQL query repository
├── services/
│   ├── user_service.py           # Participant registration & session management
│   ├── quiz_engine.py            # Quiz session state lifecycle & execution
│   ├── question_selector.py      # Dynamic randomization & repetition control
│   ├── scoring_service.py        # Real-time scoring & accuracy calculations
│   ├── history_service.py        # History aggregation & self-assessment summary
│   ├── admin_service.py          # Admin authentication, bcrypt hashing & roles
│   ├── admin_dashboard_service.py# Dashboard statistics & activity ledgers
│   ├── question_service.py       # Question CRUD & payload validation
│   ├── import_service.py         # Batch question import executor
│   └── analytics_service.py      # Question performance analytics
├── utils/
│   ├── admin_init.py             # Safe initial Superadmin provisioning CLI
│   ├── backup_db.py              # Hot atomic SQLite backup utility
│   ├── difficulty.py             # Rule-based difficulty classifier
│   ├── docx_parser.py            # Resilient Word (.docx) question parser
│   ├── excel_parser.py           # Excel (.xlsx) importer & exporter
│   ├── audio.py                  # Audio player & safe playback handlers
│   └── security.py               # Filename sanitizer, file validator & security checks
├── pages/
│   ├── 02_Identity.py            # Participant registration
│   ├── 03_Category_Selection.py  # Category picker
│   ├── 04_Level_Selection.py     # Difficulty level picker
│   ├── 05_Quiz.py                # Active quiz interface with instant feedback
│   ├── 06_Results.py             # Quiz results & performance breakdown
│   ├── 07_History.py             # Self-assessment summary & historical trends
│   ├── 90_Admin_Login.py         # Administrator portal login
│   └── 91_Admin_Dashboard.py     # Admin dashboard & management suite
├── data/
│   ├── english_assessment.db     # SQLite database (auto-created on startup)
│   └── backups/                  # Database backup storage directory
├── audio/
│   ├── listening/                # Listening comprehension audio tracks (.mp3)
│   └── feedback/                 # Sound effects for answer evaluation (.mp3)
├── uploads/                      # Temporary storage for imported DOCX / Excel files
├── requirements.txt              # Production dependency specifications
└── README.md                     # Deployment & operations documentation
```

---

## 🚀 Deployment & Setup Guide

### 1. Local Setup
Ensure your environment meets the minimum prerequisites:
- **Operating System**: Linux (Ubuntu 22.04+ recommended), macOS, or Windows 10/11.
- **Python**: Python 3.10, 3.11, 3.12, or 3.13.
- **Git**: For version control.

Clone or download the repository:
```bash
git clone <repository-url> english_self_assessment
cd english_self_assessment
```

### 2. Virtual Environment
Create an isolated virtual environment to prevent package version conflicts:

**Using standard `venv`:**
```bash
python3 -m venv .venv
source .venv/bin/activate
# On Windows (cmd.exe): .venv\Scripts\activate.bat
# On Windows (PowerShell): .venv\Scripts\Activate.ps1
```

**Using `uv` (optional, ultra-fast):**
```bash
uv venv
source .venv/bin/activate
```

### 3. Dependency Installation
Install all required production dependencies:
```bash
pip install -r requirements.txt
```

Verify that the core libraries install without warnings:
```bash
python -c "import streamlit, docx, openpyxl, pandas, plotly, bcrypt, email_validator, PIL; print('All dependencies successfully imported!')"
```

### 4. Database Initialization
The SQLite database schema is **fully idempotent**. It automatically initializes when the application boots.

To manually trigger or verify database schema initialization prior to starting the web server, run:
```bash
python -c "from database.db import init_db; init_db(); print('Database schema and seed categories initialized successfully.')"
```
The database will be created at `data/english_assessment.db` with secure file permissions (`0600` on POSIX systems).

### 5. Administrator Account Creation
Administrative accounts use salted `bcrypt` password hashing. Plaintext passwords are never stored or logged.

#### Option A: Interactive CLI (Recommended for initial setup)
Run the built-in admin initialization script:
```bash
python utils/admin_init.py
```
Follow the prompts to enter:
- **Superadmin Username** (minimum 3 characters)
- **Superadmin Password** (minimum 8 characters)

#### Option B: Environment Variable Provisioning (Ideal for CI/CD or Docker)
```bash
ADMIN_INIT_USER="admin" ADMIN_INIT_PASS="YourSecurePassword123!" python utils/admin_init.py
```
*Note: If an administrator already exists in the database, `admin_init.py` will safely refuse to overwrite existing credentials.*

### 6. Application Startup
Start the Streamlit application server:
```bash
streamlit run app.py
```
By default, the application runs at `http://localhost:8501`.

To run on a specific network interface and port (e.g. for a dedicated server or VPS):
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

---

## 🌐 Public Deployment Considerations

### A. Streamlit Community Cloud
1. Push your repository to GitHub (ensure `.gitignore` excludes `data/*.db` and `.streamlit/secrets.toml`).
2. Log into [Streamlit Community Cloud](https://share.streamlit.io/) and create a new app pointing to `app.py`.
3. Under **App settings → Secrets**, paste any desired environment secrets based on `.streamlit/secrets.toml.example`.
4. *Important note*: Streamlit Community Cloud instances have ephemeral local disk storage. Any changes to `data/english_assessment.db` will reset when the app sleeps or reboots. For persistent public deployments with user history and admin data, use a VPS, VM, or Docker container with persistent volumes (see below).

### B. Linux VPS / Virtual Machine (Ubuntu / Debian)
For production deployments, run the application as a background `systemd` service behind an Nginx reverse proxy with HTTPS.

#### 1. Systemd Service File
Create `/etc/systemd/system/english-assessment.service`:
```ini
[Unit]
Description=English Self-Assessment Streamlit Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/english_self_assessment
Environment="PATH=/var/www/english_self_assessment/.venv/bin"
ExecStart=/var/www/english_self_assessment/.venv/bin/streamlit run app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable english-assessment
sudo systemctl start english-assessment
```

#### 2. Nginx Reverse Proxy with WebSocket Support
Streamlit requires WebSocket upgrade support. Create `/etc/nginx/sites-available/english-assessment`:
```nginx
server {
    listen 80;
    server_name assessment.yourdomain.edu;

    client_max_body_size 25M;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```
Enable the site and obtain a free SSL certificate via Certbot:
```bash
sudo ln -s /etc/nginx/sites-available/english-assessment /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d assessment.yourdomain.edu
```
*HTTPS is strongly recommended so that browser audio playback and student session data remain encrypted in transit.*

### C. Docker Deployment
You can deploy using Docker with a persistent storage mount:
```bash
# Build Docker image
docker build -t english-self-assessment .

# Run container with persistent data and audio storage
docker run -d \
  --name english-assessment-app \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/audio:/app/audio \
  --restart unless-stopped \
  english-self-assessment
```

---

## 💾 SQLite Database Backup & Recovery Procedure

SQLite operates as a single, file-based database engine. To prevent file corruption during backups while users are actively taking quizzes, **always use atomic online backups**.

### 1. Automated Online Backup Utility
This project includes a dedicated atomic backup utility ([`utils/backup_db.py`](file:///Users/mertimegawaty/Bank%20Soal/english_self_assessment/utils/backup_db.py)) that utilizes the official SQLite Online Backup API:
```bash
python utils/backup_db.py
```
This command:
1. Safely locks pages incrementally without interrupting active users.
2. Generates a timestamped snapshot in `data/backups/english_assessment_backup_YYYYMMDD_HHMMSS.db`.
3. Verifies file integrity using `PRAGMA quick_check;`.
4. Sets strict file permissions (`0600`).

To specify a custom backup directory (e.g. an external mounted volume or offsite backup folder):
```bash
python utils/backup_db.py --dest /mnt/secure_backups/english_assessment/
```

### 2. Scheduled Cron Job (Automated Daily Backups)
To schedule automatic daily backups at 02:00 AM on Linux/macOS:
```bash
crontab -e
```
Add the following entry:
```cron
0 2 * * * cd /var/www/english_self_assessment && .venv/bin/python utils/backup_db.py >> /var/log/db_backup.log 2>&1
```

### 3. Database Restoration Procedure
In the event of hardware failure or accidental data deletion, restore from the latest verified backup:

1. Stop the application service:
   ```bash
   sudo systemctl stop english-assessment
   ```
2. Archive the current database state (if any):
   ```bash
   mv data/english_assessment.db data/english_assessment_damaged.db.bak
   ```
3. Copy the desired backup snapshot to `data/english_assessment.db`:
   ```bash
   cp data/backups/english_assessment_backup_20260928_120000.db data/english_assessment.db
   chmod 600 data/english_assessment.db
   ```
4. Restart the application service:
   ```bash
   sudo systemctl start english-assessment
   ```
5. Confirm application health by visiting the landing page and admin dashboard.

---

## 🔒 Security Best Practices

- **Never Commit Secrets**: Keep `.streamlit/secrets.toml` and `.env` in `.gitignore`.
- **Audio Path Traversal Guard**: All audio references are constrained to the safe `audio/` root via `utils/security.py:is_safe_audio_path()`.
- **Upload Validation**: Uploaded Word (.docx) and Excel (.xlsx) files are validated for MIME type, file size limits (max 25MB), and valid zip package structure before processing.
- **Admin Authentication**: Admin accounts require passwords with minimum length constraints and utilize salted `bcrypt` key derivation.
- **SQL Parameterization**: All SQL operations use parameter substitution (`?`) to prevent SQL injection vulnerabilities.

---

## 🧪 Testing & Verification

Run the comprehensive unit and integration test suite:
```bash
python -m unittest discover tests -v
```
All 123 tests covering participant workflows, category engines, database transactions, foreign key constraints, and edge cases will execute.
