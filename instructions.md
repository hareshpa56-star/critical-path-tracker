# NLHS Critical Path Tracker -- Setup & Operations Guide

## Overview

The Critical Path Tracker is a three-page web application:

- **Tracker** (`critical_path.html`) -- main task management table with sections, filters, inline editing, weekly goals, and history
- **Dashboard** (`dashboard.html`) -- read-only analytics: workload charts, status/priority donuts, risk cards, section progress
- **Checklists** (`checklist.html`) -- per-analyst weekly checklists with links to critical path tasks

---

## Running Locally

### Prerequisites
- Python 3.8+
- No additional installs needed for local JSON storage

### Start the server
```bash
cd C:\Users\hapatel\NLHS\CriticalPath
python server.py
```

Or double-click `CriticalPathTracker.vbs` to start the server silently and open the browser.

### Access
- **Local**: http://localhost:8080
- **Network** (same Wi-Fi/VPN): http://YOUR_IP:8080

### Local data storage
Data saves to `critical_path_data.json` and `checklist_data.json` in the project folder.

---

## Cloud Deployment (Render + Neon)

### Architecture
- **Render** (free tier) -- hosts the Python web server
- **Neon** (free tier) -- hosts the PostgreSQL database
- **GitHub** (private repo) -- source code, triggers auto-deploy on push

### Initial Setup

#### 1. Create a Neon database
1. Sign up at https://neon.tech (GitHub login works)
2. Create a new project named `nlhs-critical-path`
3. Copy the connection string (looks like `postgresql://user:pass@ep-xyz.aws.neon.tech/neondb?sslmode=require`)

#### 2. Push code to GitHub
1. Create a private repo at https://github.com/new named `nlhs-critical-path`
2. Push your code:
```bash
cd C:\Users\hapatel\NLHS\CriticalPath
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/nlhs-critical-path.git
git branch -M main
git push -u origin main
```

#### 3. Deploy on Render
1. Sign up at https://render.com (GitHub login works)
2. Click **New** > **Web Service** > connect your GitHub repo
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`
4. Go to **Environment** tab, add these variables:
   - `DATABASE_URL` = your Neon connection string
   - `APP_PASSWORD` = a team password for login
   - `PORT` = `10000`
5. Click **Manual Deploy** > **Deploy latest commit**

#### 4. Access your live site
Your URL will be shown in the Render dashboard, e.g.:
`https://nlhs-critical-path.onrender.com`

Share this URL + the password with your team.

---

## Deploying Changes

After making code changes locally:

```bash
cd C:\Users\hapatel\NLHS\CriticalPath
git add .
git commit -m "Description of what changed"
git push origin main
```

Render auto-deploys on every push to `main`. Takes ~1-2 minutes. Monitor progress in the Render dashboard under **Events**.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | No | PostgreSQL connection string. If not set, uses local JSON files. |
| `APP_PASSWORD` | No | If set, users must enter this password to access the app. |
| `PORT` | No | Server port. Defaults to `8080` locally. Set to `10000` on Render. |

---

## File Structure

```
CriticalPath/
  server.py                  # Python HTTP server (tasks + checklists API)
  critical_path.html         # Main tracker page
  dashboard.html             # Analytics dashboard
  checklist.html             # Analyst checklists
  critical_path_data.json    # Local task data (not used in cloud)
  checklist_data.json        # Local checklist data (not used in cloud)
  requirements.txt           # Python dependencies (psycopg2-binary)
  render.yaml                # Render deployment config
  .gitignore                 # Excludes local data files from git
  CriticalPathTracker.vbs    # Windows launcher (local use only)
  start_server.bat           # Batch file to start server (local use only)
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/tasks` | Fetch all critical path tasks |
| POST | `/api/tasks` | Save all tasks (full replace) |
| GET | `/api/checklists` | Fetch all checklist items |
| POST | `/api/checklists` | Save all checklist items (full replace) |
| GET | `/api/backup` | Download full backup (tasks + checklists) as JSON file |
| POST | `/api/restore` | Restore from a backup JSON file |
| GET | `/api/auth-required` | Check if password is configured |
| POST | `/api/login` | Authenticate with password, returns token |

All data endpoints require `X-Auth-Token` header if `APP_PASSWORD` is set.

---

## Key Features

### Tracker
- **Sections** -- group tasks by owner; click pencil icon to rename
- **Inline editing** -- click dropdowns to change status/priority/owner; click goal cell to edit
- **Quick Add** -- top bar for fast task entry
- **Filters** -- dropdowns for Epic Owner, Customer, Status, Priority, Review state
- **Sort** -- click any column header
- **SLG Links** -- enter a Sherlock ID or full URL; displays as clickable link to `sherlock.epic.com`
- **EOW Goals** -- inline editable; last week's goal shown beneath current
- **Reset Week** -- archives goals, unchecks reviewed flags; option to carry forward goals
- **History** -- view all archived goals and updates grouped by week
- **Email** -- generates formatted HTML email summary
- **Print** -- landscape print-friendly view
- **Import/Export** -- JSON backup and restore

### Dashboard
- KPI strip, workload bar charts, status/priority donuts
- Owner performance matrix, risk cards, weekly activity chart
- Section progress bars, missing goals list

### Checklists
- Per-analyst checklist cards
- Auto-populates analysts from tracker data
- Link checklist items to critical path tasks
- Reset Week unchecks all items

---

## Notes

- **Free tier cold starts**: Render free tier spins down after 15 min idle. First load after idle takes ~30 seconds.
- **Theme**: dark/light mode syncs across all three pages via localStorage.
- **Auth tokens**: valid for 7 days. Stored in browser localStorage.
- **Data**: cloud mode stores everything in PostgreSQL. Local mode uses JSON files. The two are independent -- local changes don't sync to cloud automatically.

## Backup & Restore

Code deploys do **not** affect your database. Your data (tasks, checklists, history) is stored in Neon Postgres, completely separate from the code on Render.

### Download a backup
Click the download arrow button (&#8681;) in the tracker header. This downloads a `cp_backup_YYYY-MM-DD.json` file containing all tasks and checklists.

### Restore from backup
Click the upload arrow button (&#8679;) in the tracker header and select a backup file. If the file is a full backup (has both tasks and checklists), it restores everything. If it's a legacy tasks-only file, it restores just the tasks.

### Recommended backup schedule
- **Weekly**: download a backup every Friday after your review
- **Before big changes**: download before doing Reset Week or bulk edits
- Store backups in a shared drive or Teams folder so they're not just on one machine
