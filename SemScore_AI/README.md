# SemScore AI

SemScore AI is a Streamlit academic analytics and student support platform. It includes an overview dashboard, transparent rule-based risk scoring, student explorer/editing, CIA analytics, personalized weekly study plans, local academic Q&A, CSV/PDF reports, CSV import validation, and a separate fictional demonstration dataset.

## Features

- Premium dark navy interface with blue/cyan accents and responsive Streamlit layout.
- SQLite storage for records in the current app environment.
- Fictional sample data included and seeded automatically.
- CSV import with flexible column-name recognition, validation, and duplicate handling.
- Missing CIA values are excluded from averages, not interpreted as zero.
- Risk factors and interventions are traceable to marks, trends, and attendance.
- Interactive Plotly charts and downloadable CSV/PDF reports.
- Local rule-based assistant works without an API key or paid service.

## Run locally

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens in a browser. The database is created as `semscore.db` beside `app.py`.

## CSV format

Required columns:
- `register_no`
- `student_name`

Optional columns:
- `department`, `year`, `section`, `subject`
- `cia1`, `cia2`, `cia3` (marks from 0 to 100; blanks are allowed)
- `attendance` (0 to 100)
- `previous_result`, `semester`

Column aliases such as `Register Number`, `Name`, `CIA 1`, `Attendance %`, and `Branch` are recognized. The importer previews and validates the file before import. The unique key is register number + subject + data source. Re-importing updates matching records.

## Risk scoring notes

This version uses a transparent configurable rules baseline. It does **not** claim to be a trained machine-learning model. The score is a prioritization signal for academic support, not a guarantee of exam outcomes. Model training is intentionally not enabled without a suitable labeled dataset and a held-out evaluation process.

Default risk categories:
- Low: score below 30
- Medium: 30 to below 60
- High: 60 to 100

## Deploy to Streamlit Community Cloud

1. Create a GitHub repository, for example `semscore-ai`.
2. Upload `app.py`, `requirements.txt`, `README.md`, `sample_students.csv`, and `.gitignore`.
3. Go to [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
4. Select **Create app**, choose the repository and branch, set the main file path to `app.py`, and deploy.
5. Open the generated public URL on a phone, tablet, or computer. On Android, open the URL in Chrome and optionally choose **Add to Home screen** from the browser menu.
6. To update the app, commit/push the changed files to the connected GitHub branch. Streamlit Community Cloud will redeploy the app.

## Important deployment and privacy notes

- A public unauthenticated app must only use fictional or non-sensitive data. Do not upload identifiable student records to a public presentation deployment.
- SQLite is appropriate for a local demo and basic persistence while the app process/storage remains available. Streamlit Community Cloud's local filesystem is not a durable database guarantee across restarts, rebuilds, or redeployments. For persistent production use, configure a managed database and set `SEMSCORE_DB_PATH` only when using durable mounted storage; a database URL adapter would be needed for hosted PostgreSQL.
- This project does not implement user authentication or role-based access. Do not present it as secure for real student records without adding authentication, authorization, and suitable persistent storage.
- No API keys are required. Never commit secrets to GitHub.

## Project structure

```text
SemScore_AI/
├── app.py
├── requirements.txt
├── README.md
├── sample_students.csv
└── .gitignore
```
