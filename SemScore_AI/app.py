import io, os, sqlite3, json, math
from datetime import datetime, date
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).parent
DB_PATH = Path(os.getenv("SEMSCORE_DB_PATH", str(APP_DIR / "semscore.db")))
SAMPLE_PATH = APP_DIR / "sample_students.csv"

st.set_page_config(page_title="SemScore AI", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root { --bg:#070b14; --panel:#0d1423; --panel2:#101b2d; --line:#1d2a40; --blue:#4d8dff; --cyan:#52d8e8; --muted:#91a0b8; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background: radial-gradient(ellipse at 85% 0%, #10213a 0%, #070b14 42%); color:#edf3ff; }
[data-testid="stSidebar"] { background:#080e19; border-right:1px solid #1c2b42; }
[data-testid="stSidebar"] * { color:#dce7fa; }
h1,h2,h3 { font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.025em; }
h1 { font-size:2.15rem !important; }
small,.muted { color:var(--muted); }
[data-testid="stMetric"] { background:linear-gradient(145deg,#101b2c,#0b1220); border:1px solid #23334b; border-radius:15px; padding:17px 18px; }
[data-testid="stMetricLabel"] { color:#a6b6ce !important; }
[data-testid="stMetricValue"] { color:#f4f8ff !important; font-family:'Space Grotesk',sans-serif; }
.stButton > button, .stDownloadButton > button { border-radius:9px; border:1px solid #31558a; background:#132744; color:#eaf2ff; font-weight:600; }
.stButton > button:hover, .stDownloadButton > button:hover { border-color:#52d8e8; color:white; background:#19395f; }
div[data-testid="stDataFrame"] { border:1px solid #22324a; border-radius:12px; overflow:hidden; }
div[data-testid="stForm"] { border:1px solid #22324a; border-radius:14px; padding:18px; background:#0c1422; }
hr { border-color:#1e2b40; }
section[data-testid="stVerticalBlock"] > div:has(> .sem-panel) { background:#0d1423; }
.sem-kicker { color:#65c7ff; text-transform:uppercase; letter-spacing:.14em; font-size:.72rem; font-weight:700; }
.sem-card { background:linear-gradient(145deg,rgba(17,29,48,.96),rgba(10,17,29,.96)); border:1px solid #22334c; border-radius:15px; padding:17px 18px; min-height:100px; }
.sem-card-label { color:#94a7c2; font-size:.82rem; margin-bottom:7px; }
.sem-card-value { color:#f1f6ff; font:600 1.65rem 'Space Grotesk',sans-serif; }
.sem-card-note { color:#58cbe4; font-size:.78rem; margin-top:5px; }
[data-testid="stAlert"] { border-radius:10px; }
</style>
""", unsafe_allow_html=True)

PAGES = ["My Score Planner", "Overview", "Risk Assessment", "Student Explorer", "CIA Analytics",
         "Improvement Planner", "AI Assistant", "Reports", "Data Management", "Settings"]

# ---------- Data and storage ----------
ALIASES = {
    "register_no": ["register_no","register number","register no","reg_no","reg no","roll_no","roll number","student_id","id"],
    "student_name": ["student_name","student name","name","full_name","full name"],
    "department": ["department","dept","branch","program"],
    "year": ["year","study_year","academic_year"],
    "section": ["section","sec","class_section"],
    "subject": ["subject","course","subject_name"],
    "cia1": ["cia1","cia 1","cia_1","assessment 1","assessment1","internal 1"],
    "cia2": ["cia2","cia 2","cia_2","assessment 2","assessment2","internal 2"],
    "cia3": ["cia3","cia 3","cia_3","assessment 3","assessment3","internal 3"],
    "attendance": ["attendance","attendance_pct","attendance percentage","attendance %","attendance_percent"],
    "previous_result": ["previous_result","previous result","previous_score","previous score","last_semester_score"],
    "semester": ["semester","sem","term"],
}

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT, register_no TEXT NOT NULL, student_name TEXT NOT NULL,
        department TEXT, year TEXT, section TEXT, subject TEXT, cia1 REAL, cia2 REAL, cia3 REAL,
        attendance REAL, previous_result REAL, semester TEXT, source TEXT DEFAULT 'uploaded',
        updated_at TEXT, UNIQUE(register_no, subject, source))""")
    con.commit()
    return con

def normalize_columns(df):
    df = df.copy()
    lookup = {str(c).strip().lower().replace("-", "_"): c for c in df.columns}
    rename = {}
    for target, variants in ALIASES.items():
        for v in variants:
            key = v.lower().replace("-", "_")
            if key in lookup:
                rename[lookup[key]] = target
                break
    return df.rename(columns=rename)

def validate_and_normalize(raw):
    df = normalize_columns(raw)
    errors, warnings = [], []
    required = ["register_no", "student_name"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return None, [f"Missing required column(s): {', '.join(missing)}. Required: register_no and student_name."], []
    for c, default in [("department","General"),("year","1"),("section","A"),("subject","Overall"),("semester","Current")]:
        if c not in df.columns: df[c] = default
    for c in ["cia1","cia2","cia3","attendance","previous_result"]:
        if c not in df.columns: df[c] = np.nan
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["cia1","cia2","cia3","previous_result"]:
        bad = df[c].notna() & ~df[c].between(0,100)
        if bad.any():
            errors.append(f"{c.upper()} has {int(bad.sum())} value(s) outside 0–100.")
    bad_att = df["attendance"].notna() & ~df["attendance"].between(0,100)
    if bad_att.any(): errors.append(f"Attendance has {int(bad_att.sum())} value(s) outside 0–100.")
    df["register_no"] = df["register_no"].astype(str).str.strip()
    df["student_name"] = df["student_name"].astype(str).str.strip()
    if (df["register_no"] == "").any() or (df["student_name"] == "").any():
        errors.append("Register number and student name cannot be blank.")
    dup = df.duplicated(["register_no","subject"], keep=False)
    if dup.any(): warnings.append(f"{int(dup.sum())} duplicate register-number/subject row(s) detected; only the last row will be kept.")
    df = df.drop_duplicates(["register_no","subject"], keep="last")
    if errors: return None, errors, warnings
    return df, [], warnings

def seed_demo(con):
    count = con.execute("SELECT COUNT(*) FROM students WHERE source='demo'").fetchone()[0]
    if count: return
    if SAMPLE_PATH.exists():
        raw = pd.read_csv(SAMPLE_PATH)
    else:
        raw = make_sample()
    df, errs, _ = validate_and_normalize(raw)
    if df is not None:
        write_records(con, df, "demo")

def make_sample():
    rng = np.random.default_rng(42)
    names = ["Aarav Sharma","Diya Nair","Kabir Menon","Ananya Iyer","Rohan Das","Meera Krishnan","Arjun Patel","Ishita Rao","Vikram Singh","Nila Joseph","Aditya Kumar","Sara Thomas","Karthik Raj","Priya Shah","Rahul Verma","Anika Bose","Sanjay Mohan","Tara Reddy","Dev Anand","Maya Pillai","Naveen Kumar","Aisha Khan","Varun Suresh","Kavya Balan","Harish Gopal","Ira Mukherjee","Manoj Selvam","Zoya Ali","Pranav Nair","Sneha Das"]
    subjects = ["Mathematics","Programming","Data Structures"]
    rows=[]
    for i,name in enumerate(names):
        base = float(rng.integers(34,92))
        trend = float(rng.integers(-18,16))
        for j,sub in enumerate(subjects):
            subject_bias = [0,-4,3][j]
            a1=np.clip(base+subject_bias+rng.normal(0,9),8,99)
            a2=np.clip(a1+trend/2+rng.normal(0,7),5,100)
            a3=np.clip(a2+trend/2+rng.normal(0,7),5,100) if (i+j)%5!=0 else np.nan
            attendance=np.clip(rng.normal(82 if i%5 else 67,10),48,100)
            previous=np.clip(base+rng.normal(0,10),0,100)
            rows.append({"register_no":f"SS{2026}{i+1:03d}","student_name":name,"department":["AI&DS","CSE","IT"][i%3],
                         "year":str(1+(i%3)),"section":["A","B"][i%2],"subject":sub,"cia1":round(a1,1),
                         "cia2":round(a2,1),"cia3":None if pd.isna(a3) else round(a3,1),
                         "attendance":round(attendance,1),"previous_result":round(previous,1),"semester":"Semester 1"})
    return pd.DataFrame(rows)

def write_records(con, df, source):
    now = datetime.now().isoformat(timespec="seconds")
    cols = ["register_no","student_name","department","year","section","subject","cia1","cia2","cia3","attendance","previous_result","semester"]
    for _, r in df.iterrows():
        vals = []
        for c in cols:
            v = r.get(c, None)
            if pd.isna(v): v = None
            elif c in ["register_no","student_name","department","year","section","subject","semester"]: v = str(v)
            else: v = float(v)
            vals.append(v)
        con.execute("""INSERT INTO students (register_no,student_name,department,year,section,subject,cia1,cia2,cia3,attendance,previous_result,semester,source,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(register_no,subject,source) DO UPDATE SET
            student_name=excluded.student_name, department=excluded.department, year=excluded.year, section=excluded.section,
            cia1=excluded.cia1, cia2=excluded.cia2, cia3=excluded.cia3, attendance=excluded.attendance,
            previous_result=excluded.previous_result, semester=excluded.semester, updated_at=excluded.updated_at""",
            vals+[source,now])
    con.commit()

def load_data(con, source):
    df = pd.read_sql_query("SELECT * FROM students WHERE source=? ORDER BY register_no, subject", con, params=(source,))
    return df

def assessment_average(row):
    vals = [row.get(c) for c in ["cia1","cia2","cia3"]]
    vals = [float(x) for x in vals if pd.notna(x)]
    return float(np.mean(vals)) if vals else np.nan

def student_summary(df, pass_mark=50, attendance_weight=15, trend_weight=20):
    if df.empty: return pd.DataFrame()
    rows=[]
    for reg, g in df.groupby("register_no", dropna=False):
        first=g.iloc[0]
        marks = [g[c].mean(skipna=True) if c in g else np.nan for c in ["cia1","cia2","cia3"]]
        valid_marks=[x for x in marks if pd.notna(x)]
        avg=float(np.mean(valid_marks)) if valid_marks else np.nan
        latest = marks[2] if pd.notna(marks[2]) else (marks[1] if pd.notna(marks[1]) else marks[0])
        earliest = marks[0] if pd.notna(marks[0]) else np.nan
        decline = max(0, earliest-latest) if pd.notna(earliest) and pd.notna(latest) else 0
        low_subjects=[]
        for _, sr in g.iterrows():
            vals=[sr[c] for c in ["cia1","cia2","cia3"] if pd.notna(sr[c])]
            savg=float(np.mean(vals)) if vals else np.nan
            if pd.notna(savg) and savg < pass_mark: low_subjects.append(str(sr["subject"]))
        attendance=g["attendance"].mean(skipna=True)
        score=0.0
        factors=[]
        if pd.isna(avg):
            score += 35; factors.append("No CIA marks available")
        elif avg < pass_mark:
            score += min(45, (pass_mark-avg)*1.25+15); factors.append(f"Average CIA score below {pass_mark}% ({avg:.1f}%)")
        elif avg < 60:
            score += 15; factors.append(f"Borderline CIA average ({avg:.1f}%)")
        if pd.notna(attendance) and attendance < 75:
            score += min(attendance_weight, (75-attendance)*0.8+4); factors.append(f"Attendance below 75% ({attendance:.1f}%)")
        if decline >= 10:
            score += min(trend_weight, decline*0.7); factors.append(f"Assessment average declined by {decline:.1f} points")
        if low_subjects:
            score += min(20, 6*len(set(low_subjects))); factors.append("Below-target subjects: "+", ".join(sorted(set(low_subjects))))
        score=float(np.clip(score,0,100))
        risk="High" if score>=60 else ("Medium" if score>=30 else "Low")
        recs=[]
        if low_subjects: recs.append("Schedule two focused practice sessions for: "+", ".join(sorted(set(low_subjects)))+".")
        if pd.notna(attendance) and attendance<75: recs.append("Meet the faculty advisor and build an attendance recovery plan.")
        if decline>=10: recs.append("Review recent mistakes and set a weekly progress check.")
        if pd.notna(avg) and avg<pass_mark: recs.append("Arrange faculty support and complete a targeted remedial worksheet.")
        if not recs: recs.append("Maintain the current routine and complete one timed practice set per week.")
        rows.append({"register_no":str(reg),"student_name":first["student_name"],"department":first["department"],"year":str(first["year"]),
            "section":first["section"],"average_score":round(avg,1) if pd.notna(avg) else np.nan,
            "latest_score":round(latest,1) if pd.notna(latest) else np.nan,"decline":round(decline,1),
            "attendance":round(attendance,1) if pd.notna(attendance) else np.nan,"risk_score":round(score,1),
            "risk_level":risk,"risk_factors":"; ".join(factors) if factors else "No major risk indicators detected",
            "recommendations":" ".join(recs),"subjects":", ".join(sorted(g["subject"].dropna().astype(str).unique()))})
    return pd.DataFrame(rows).sort_values(["risk_score","student_name"],ascending=[False,True]).reset_index(drop=True)

def plot_layout(fig, height=330):
    fig.update_layout(height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#d9e5f7", family="DM Sans"), margin=dict(l=10,r=10,t=38,b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"), title_font=dict(size=15))
    fig.update_xaxes(gridcolor="#1d2a40", zerolinecolor="#1d2a40")
    fig.update_yaxes(gridcolor="#1d2a40", zerolinecolor="#1d2a40")
    return fig

def card(label, value, note=""):
    st.markdown(f'<div class="sem-card"><div class="sem-card-label">{label}</div><div class="sem-card-value">{value}</div><div class="sem-card-note">{note}</div></div>', unsafe_allow_html=True)

def get_filtered(df, key_prefix="flt"):
    if df.empty: return df
    c1,c2,c3,c4=st.columns([1.2,1,1,1.1])
    depts=["All"]+sorted(df["department"].dropna().astype(str).unique().tolist())
    years=["All"]+sorted(df["year"].dropna().astype(str).unique().tolist())
    sections=["All"]+sorted(df["section"].dropna().astype(str).unique().tolist())
    dept=c1.selectbox("Department",depts,key=f"{key_prefix}_dept")
    year=c2.selectbox("Year",years,key=f"{key_prefix}_year")
    section=c3.selectbox("Section",sections,key=f"{key_prefix}_section")
    query=c4.text_input("Search student",placeholder="Name or register no.",key=f"{key_prefix}_search")
    out=df.copy()
    if dept!="All": out=out[out.department.astype(str)==dept]
    if year!="All": out=out[out.year.astype(str)==year]
    if section!="All": out=out[out.section.astype(str)==section]
    if query.strip():
        q=query.strip().lower()
        out=out[out.student_name.astype(str).str.lower().str.contains(q,na=False)|out.register_no.astype(str).str.lower().str.contains(q,na=False)]
    return out

# ---------- Initialize ----------
con=connect()
seed_demo(con)
if "data_source" not in st.session_state: st.session_state.data_source="demo"
if "selected_student" not in st.session_state: st.session_state.selected_student=""
if "page" not in st.session_state: st.session_state.page="My Score Planner"

with st.sidebar:
    st.markdown('<div class="sem-kicker">ACADEMIC INTELLIGENCE</div>',unsafe_allow_html=True)
    st.markdown("# ◈ SemScore AI")
    st.caption("Anna University R2023 planning prototype • Student-first score planner")
    st.divider()
    page=st.radio("WORKSPACE",PAGES,index=PAGES.index(st.session_state.page),key="page_nav",label_visibility="visible")
    st.session_state.page=page
    st.divider()
    st.markdown("**Active dataset**")
    source_choice=st.radio("Choose data",["Demo dataset","Uploaded dataset"],index=0 if st.session_state.data_source=="demo" else 1,key="source_radio")
    st.session_state.data_source="demo" if source_choice=="Demo dataset" else "uploaded"
    st.caption("Demo records are fictional. Uploaded records are stored separately.")
    st.divider()
    st.caption("Rule-based risk scoring • No untrained ML claims")

source=st.session_state.data_source
raw=load_data(con,source)
if raw.empty and source=="uploaded":
    df=pd.DataFrame(columns=["register_no","student_name","department","year","section","subject","cia1","cia2","cia3","attendance","previous_result","semester"])
else:
    df=raw.copy()
for c in ["cia1","cia2","cia3","attendance","previous_result"]:
    if c in df: df[c]=pd.to_numeric(df[c],errors="coerce")
summary=student_summary(df)
page=st.session_state.page

# ---------- Header ----------
st.markdown('<div class="sem-kicker">ANNA UNIVERSITY R2023 • STUDENT SCORE PLANNER PROTOTYPE</div>',unsafe_allow_html=True)
st.title(page)
st.caption("Plan CIA 3, estimate the semester-exam mark you need, and work toward a target grade. Confirm your autonomous-college scheme before relying on the estimates.")
if source=="demo":
    st.info("Demonstration mode: all student records are fictional sample data. Switch to Uploaded dataset to work with your own CSV.")

# ---------- Student Score Planner ----------
if page == "My Score Planner":
    st.markdown("Build a recovery plan from your first two CIAs, prepare for CIA 3, and set a subject-by-subject semester-exam target. Your goal is an **8.5 CGPA**; all target calculations are estimates that depend on the marking scheme you enter.")
    st.info("Student mode: enter your own marks below. If the app is showing the demo dataset, its student records are fictional and are not used for your personal score plan.")

    with st.expander("1. Configure your assessment and grade scheme", expanded=True):
        st.warning("Only the all-three-CIA average is fixed here, as requested. The internal/exam split, maximum marks, pass requirements and grade-point boundaries are editable assumptions. Confirm them with KRCE's official autonomous scheme before relying on the results.")
        cfg1, cfg2, cfg3 = st.columns(3)
        with cfg1:
            cia_max = st.number_input("Maximum mark for each CIA", min_value=1, max_value=200, value=50, step=1, key="personal_cia_max")
            internal_weight = st.number_input("Internal component (% of final)", min_value=1, max_value=99, value=40, step=1, key="personal_internal_weight")
        with cfg2:
            exam_max = st.number_input("Maximum semester-exam mark", min_value=1, max_value=200, value=100, step=1, key="personal_exam_max")
            exam_weight = st.number_input("Semester-exam component (% of final)", min_value=1, max_value=99, value=60, step=1, key="personal_exam_weight")
        with cfg3:
            expected_exam_pct = st.slider("Expected exam performance (%)", min_value=0, max_value=100, value=75, step=1, key="personal_expected_exam_pct", help="A planning estimate. Change it to compare realistic and stretch scenarios.")
            target_cgpa = st.number_input("Target CGPA", min_value=0.0, max_value=10.0, value=8.5, step=0.1, key="personal_target_cgpa")

        st.markdown("**Editable grade-point table**")
        st.caption("The rows below are example values only, not an official Anna University/KRCE grade table. Replace the cutoffs and grade points with the values published by your college.")
        grade_defaults = pd.DataFrame([
            {"Minimum final %": 90.0, "Grade label": "Example grade 1", "Grade point": 10.0},
            {"Minimum final %": 80.0, "Grade label": "Example grade 2", "Grade point": 9.0},
            {"Minimum final %": 70.0, "Grade label": "Example grade 3", "Grade point": 8.0},
            {"Minimum final %": 60.0, "Grade label": "Example grade 4", "Grade point": 7.0},
            {"Minimum final %": 50.0, "Grade label": "Example grade 5", "Grade point": 6.0},
            {"Minimum final %": 0.0, "Grade label": "Example grade 6", "Grade point": 0.0},
        ])
        grade_table = st.data_editor(grade_defaults, key="personal_grade_table", num_rows="dynamic", hide_index=True, use_container_width=True,
            column_config={"Minimum final %": st.column_config.NumberColumn(min_value=0, max_value=100, step=1),
                           "Grade label": st.column_config.TextColumn(),
                           "Grade point": st.column_config.NumberColumn(min_value=0, max_value=10, step=0.5)})

    if int(internal_weight) + int(exam_weight) != 100:
        st.warning(f"Internal and exam weights currently total {int(internal_weight) + int(exam_weight)}%, not 100%. Adjust them to match the official scheme before interpreting results.")

    st.divider()
    st.subheader("2. Enter your subjects and CIA marks")
    st.caption("Enter CIA 1 and CIA 2 marks you already received. CIA 3 is not known yet, so use the expected CIA 3 column to try scenarios. Replace the example subject names, credits and marks with your own.")
    default_subjects = [str(x) for x in (sorted(df["subject"].dropna().astype(str).unique().tolist())[:8] if not df.empty else [])]
    if not default_subjects:
        default_subjects = ["Subject 1", "Subject 2", "Subject 3", "Subject 4", "Subject 5"]
    subject_defaults = pd.DataFrame({
        "Subject": default_subjects,
        "CIA 1": [min(35.0, float(cia_max))] * len(default_subjects),
        "CIA 2": [min(40.0, float(cia_max))] * len(default_subjects),
        "Expected CIA 3": [min(40.0, float(cia_max))] * len(default_subjects),
        "Credits": [0.0] * len(default_subjects),
        "Syllabus ready %": [0] * len(default_subjects),
        "Target final %": [85.0] * len(default_subjects),
    })
    subjects_input = st.data_editor(subject_defaults, key="personal_subject_inputs", num_rows="dynamic", hide_index=True, use_container_width=True,
        column_config={
            "Subject": st.column_config.TextColumn(required=True),
            "CIA 1": st.column_config.NumberColumn(min_value=0, max_value=float(cia_max), step=1),
            "CIA 2": st.column_config.NumberColumn(min_value=0, max_value=float(cia_max), step=1),
            "Expected CIA 3": st.column_config.NumberColumn(min_value=0, max_value=float(cia_max), step=1),
            "Credits": st.column_config.NumberColumn(min_value=0, max_value=30, step=1, help="Enter official subject credits. A zero credit value is excluded from GPA calculations."),
            "Syllabus ready %": st.column_config.NumberColumn(min_value=0, max_value=100, step=5),
            "Target final %": st.column_config.NumberColumn(min_value=0, max_value=100, step=1),
        })

    if subjects_input.empty:
        st.warning("Add at least one subject to calculate your plan.")
    elif int(internal_weight) + int(exam_weight) == 100:
        valid_grades = grade_table.copy()
        valid_grades["Minimum final %"] = pd.to_numeric(valid_grades["Minimum final %"], errors="coerce")
        valid_grades["Grade point"] = pd.to_numeric(valid_grades["Grade point"], errors="coerce")
        valid_grades = valid_grades.dropna(subset=["Minimum final %", "Grade point", "Grade label"]).sort_values("Minimum final %", ascending=False)

        def point_for_score(score):
            if not valid_grades.empty:
                for _, band in valid_grades.iterrows():
                    if score >= float(band["Minimum final %"]):
                        return float(band["Grade point"]), str(band["Grade label"])
            return 0.0, "Unmapped"

        result_rows = []
        study_rows = []
        def safe_num(value, default=0.0):
            try:
                if pd.isna(value):
                    return float(default)
                return float(value)
            except (TypeError, ValueError):
                return float(default)

        for _, row in subjects_input.iterrows():
            raw_subject = row.get("Subject", "")
            if pd.isna(raw_subject):
                continue
            subject = str(raw_subject).strip()
            if not subject:
                continue
            c1 = safe_num(row.get("CIA 1", 0))
            c2 = safe_num(row.get("CIA 2", 0))
            c3_plan = safe_num(row.get("Expected CIA 3", 0))
            credits = max(0.0, safe_num(row.get("Credits", 0)))
            readiness = float(np.clip(safe_num(row.get("Syllabus ready %", 0)), 0, 100))
            target_pct = float(np.clip(safe_num(row.get("Target final %", 85), 85), 0, 100))
            c1p, c2p, c3p = [np.clip(v / float(cia_max) * 100, 0, 100) for v in (c1, c2, c3_plan)]
            internal_pct = (c1p + c2p + c3p) / 3.0
            internal_contribution = internal_pct * float(internal_weight) / 100.0
            estimated_final = internal_contribution + float(expected_exam_pct) * float(exam_weight) / 100.0
            req_internal_pct = (target_pct - float(expected_exam_pct) * float(exam_weight) / 100.0) * 100.0 / float(internal_weight)
            req_cia3_pct = max(0.0, 3.0 * req_internal_pct - c1p - c2p)
            if req_internal_pct <= 0:
                cia3_needed = 0.0
                cia3_status = "Target covered by exam estimate"
            elif req_internal_pct > 100 or req_cia3_pct > 100:
                cia3_needed = np.nan
                cia3_status = "Not reachable at current exam estimate"
            else:
                cia3_needed = req_cia3_pct * float(cia_max) / 100.0
                cia3_status = "Achievable under entered assumptions" if cia3_needed <= cia_max else "Not reachable"
            exam_required_pct = (target_pct - internal_contribution) * 100.0 / float(exam_weight)
            if exam_required_pct <= 0:
                exam_needed = 0.0
                exam_status = "Target covered by internal estimate*"
            elif exam_required_pct > 100:
                exam_needed = np.nan
                exam_status = "Not reachable with current CIA 3 estimate"
            else:
                exam_needed = exam_required_pct * float(exam_max) / 100.0
                exam_status = "Achievable under entered assumptions"
            gp, grade_label = point_for_score(estimated_final)
            result_rows.append({
                "Subject": subject, "CIA 1": round(c1, 1), "CIA 2": round(c2, 1),
                "Expected CIA 3": round(c3_plan, 1), "CIA 3 needed for target": round(cia3_needed, 1) if pd.notna(cia3_needed) else "Not reachable",
                "Target final %": round(target_pct, 1), "Exam mark needed": round(exam_needed, 1) if pd.notna(exam_needed) else "Not reachable",
                "Expected exam %": float(expected_exam_pct), "Estimated final %": round(estimated_final, 1),
                "Example grade band": grade_label, "Grade point": gp, "Credits": credits,
                "CIA 3 status": cia3_status, "Exam target status": exam_status,
            })
            # Focus more study time on weak CIA performance and lower syllabus readiness.
            known_avg = (c1p + c2p) / 2.0
            priority = (100.0 - known_avg) * 0.65 + (100.0 - readiness) * 0.35
            study_rows.append({"Subject": subject, "CIA 1–2 average %": round(known_avg, 1), "Syllabus ready %": readiness,
                               "Priority score": round(priority, 1), "Target final %": target_pct, "Credits": credits})

        results = pd.DataFrame(result_rows)
        if not results.empty:
            st.subheader("3. Your CIA 3 recovery and semester-exam targets")
            st.caption("CIA 3 target assumes the three CIA percentages are averaged equally. Exam targets assume a linear internal/exam weighting and do not enforce any official minimum exam mark or rounding rule.")
            st.dataframe(results[["Subject", "CIA 1", "CIA 2", "Expected CIA 3", "CIA 3 needed for target", "Target final %", "Exam mark needed", "Estimated final %", "Example grade band", "CIA 3 status", "Exam target status"]], hide_index=True, use_container_width=True)
            if (results["CIA 3 status"] == "Not reachable at current exam estimate").any():
                st.warning("Some CIA 3 targets are not reachable with your current expected semester-exam performance. Raise the exam-performance estimate, lower the target, or check the assessment settings.")
            if (results["Exam target status"] == "Not reachable with current CIA 3 estimate").any():
                st.warning("Some subject targets are not reachable through the semester exam alone under the entered assumptions. Use the results to prioritize effort, not as a guarantee.")

            # Credit-weighted GPA estimate, only for subjects with user-entered positive credits.
            credited = results[pd.to_numeric(results["Credits"], errors="coerce") > 0].copy()
            if not credited.empty:
                total_credits = float(credited["Credits"].sum())
                estimated_sgpa = float((credited["Grade point"] * credited["Credits"]).sum() / total_credits)
                st.divider()
                st.subheader("4. Semester GPA and CGPA goal tracker")
                g1, g2, g3 = st.columns(3)
                g1.metric("Credits entered", f"{total_credits:g}")
                g2.metric("Estimated semester GPA", f"{estimated_sgpa:.2f}/10", help="Credit-weighted estimate using the editable grade-point table above.")
                g3.metric("CGPA goal", f"{target_cgpa:.2f}/10")
                st.caption("GPA is estimated from the example grade table and your entered credits. Replace example grade cutoffs/points and verify how your college handles failed, audited, practical and non-credit courses.")
                cg1, cg2, cg3 = st.columns(3)
                with cg1:
                    current_cgpa = st.number_input("Current CGPA before this semester", min_value=0.0, max_value=10.0, value=7.5, step=0.01, key="personal_current_cgpa", help="Enter the official CGPA shown on your marksheet.")
                with cg2:
                    completed_credits = st.number_input("Credits completed before this semester", min_value=0.0, max_value=500.0, value=24.0, step=1.0, key="personal_completed_credits", help="Enter total credits already counted in your current CGPA.")
                with cg3:
                    current_sem_credits = st.number_input("Credits counted this semester", min_value=0.0, max_value=60.0, value=total_credits, step=1.0, key="personal_semester_credits", help="Defaults to the sum of credits entered above. Change if not every listed subject counts toward GPA.")
                if current_sem_credits > 0:
                    needed_sgpa = (float(target_cgpa) * (float(completed_credits) + float(current_sem_credits)) - float(current_cgpa) * float(completed_credits)) / float(current_sem_credits)
                    if needed_sgpa > 10:
                        st.error(f"To reach CGPA {target_cgpa:.2f} immediately, the required semester GPA would be {needed_sgpa:.2f}, above 10.0. The target may need more than one semester; this is a planning calculation, not a verdict.")
                    elif needed_sgpa <= 0:
                        st.success(f"Based on the credits and current CGPA entered, the target CGPA is already covered mathematically even with a very low semester GPA. Verify your official credit/grade rules.")
                    else:
                        st.success(f"Estimated semester GPA needed to reach CGPA {target_cgpa:.2f} after this semester: **{needed_sgpa:.2f}/10**.")
                    scenario_rows = []
                    for scenario_sgpa in [6.0, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]:
                        resulting = (float(current_cgpa) * float(completed_credits) + scenario_sgpa * float(current_sem_credits)) / (float(completed_credits) + float(current_sem_credits)) if completed_credits + current_sem_credits > 0 else scenario_sgpa
                        scenario_rows.append({"Scenario semester GPA": scenario_sgpa, "Projected CGPA": round(resulting, 3), "Reaches target?": "Yes" if resulting >= float(target_cgpa) else "Not yet"})
                    st.dataframe(pd.DataFrame(scenario_rows), hide_index=True, use_container_width=True)
                    scenario_chart = pd.DataFrame(scenario_rows)
                    fig = px.line(scenario_chart, x="Scenario semester GPA", y="Projected CGPA", markers=True, title="How this semester's GPA affects your CGPA")
                    fig.add_hline(y=float(target_cgpa), line_dash="dash", annotation_text=f"Target CGPA {target_cgpa:.2f}")
                    st.plotly_chart(plot_layout(fig, 320), use_container_width=True)
                else:
                    st.info("Enter the number of credits that count toward this semester's GPA to calculate CGPA scenarios.")
            else:
                st.info("Enter official subject credits (greater than zero) in the subject table to enable semester GPA and CGPA estimates.")

            st.divider()
            st.subheader("5. Your personalized 3.5-hour daily study guide")
            st.write("Since semester-exam preparation has not started, use the first week to build coverage, then move quickly into active recall and timed practice. The plan allocates more time to subjects with lower CIA performance and lower syllabus readiness.")
            study_df = pd.DataFrame(study_rows).sort_values("Priority score", ascending=False)
            st.markdown("**Subject priority order**")
            st.dataframe(study_df[["Subject", "CIA 1–2 average %", "Syllabus ready %", "Priority score", "Target final %"]], hide_index=True, use_container_width=True)
            top_subjects = study_df["Subject"].tolist()
            session_subjects = (top_subjects + ["Mixed revision"] * 7)[:7]
            day_plan = []
            for day in range(7):
                sub = session_subjects[day]
                day_plan.append({"Day": f"Day {day + 1}", "Block 1 — 75 min": f"{sub}: learn concepts and make concise notes", "Block 2 — 60 min": f"{sub}: solve examples without looking at solutions", "Block 3 — 45 min": "Recall yesterday's topics and write key formulas/definitions", "Block 4 — 30 min": "Closed-book quiz, error log, and plan tomorrow", "Done": False})
            st.dataframe(pd.DataFrame(day_plan).drop(columns=["Done"]), hide_index=True, use_container_width=True)
            st.markdown("**Daily routine (210 minutes = 3.5 hours)**")
            st.markdown("- **75 min:** Study the highest-priority subject/topic from class notes and prescribed material.\n- **60 min:** Solve questions or past-paper problems without checking the answer first.\n- **45 min:** Active recall from yesterday's topics; explain the concept in your own words.\n- **30 min:** Short timed quiz, record mistakes, and choose tomorrow's first task.\n\nTake short breaks between blocks. Reserve at least one block daily for the subject with the weakest CIA 1–2 average, and rotate the other blocks across remaining subjects.")
            with st.expander("Weekly checklist", expanded=False):
                checklist = ["List all syllabus units and mark completed / partial / not started", "Collect prescribed notes and previous question papers", "Create an error log from CIA 1 and CIA 2 mistakes", "Complete one timed practice set in each subject", "Revise definitions, formulas, diagrams and common problem steps", "Do a weekly review and update syllabus readiness percentages", "Ask faculty about topics or assessment rules that remain unclear"]
                for i, task in enumerate(checklist):
                    st.checkbox(task, key=f"personal_weekly_check_{i}")
            st.download_button("Download my subject targets (CSV)", results.to_csv(index=False).encode("utf-8"), "semscore_personal_targets.csv", "text/csv")
            st.download_button("Download my 7-day study plan (CSV)", pd.DataFrame(day_plan).to_csv(index=False).encode("utf-8"), "semscore_7_day_study_plan.csv", "text/csv")

    st.divider()
    st.caption("Planning aid only. Final marks, pass eligibility, letter grades, grade points, SGPA and CGPA must be calculated using the official KRCE autonomous regulations applicable to your programme and course. No official outcome is guaranteed.")

# ---------- Overview ----------
elif page=="Overview":
    if df.empty:
        st.warning("No uploaded records yet. Open Data Management to import a CSV, or switch to Demo dataset.")
    else:
        total=summary.register_no.nunique()
        avg=summary.average_score.mean()
        high=int((summary.risk_level=="High").sum())
        pass_pct=float((summary.average_score>=50).mean()*100) if summary.average_score.notna().any() else np.nan
        a,b,c,d=st.columns(4)
        with a: st.metric("Students",f"{total:,}",help="Unique register numbers in the active dataset.")
        with b: st.metric("Average CIA score",f"{avg:.1f}%" if pd.notna(avg) else "—")
        with c: st.metric("Estimated pass share",f"{pass_pct:.1f}%" if pd.notna(pass_pct) else "—",help="Share of students whose available mean CIA score is at least 50%. This is not an exam outcome prediction.")
        with d: st.metric("High-risk students",f"{high:,}")
        st.divider()
        left,right=st.columns([1.15,1])
        with left:
            st.subheader("Academic performance distribution")
            dist=summary.copy()
            dist["score_band"]=pd.cut(dist.average_score,[-0.1,39.999,49.999,59.999,69.999,79.999,100],labels=["<40","40–49","50–59","60–69","70–79","80–100"])
            counts=dist.score_band.value_counts(sort=False).rename_axis("Band").reset_index(name="Students")
            st.plotly_chart(plot_layout(px.bar(counts,x="Band",y="Students",color="Band",text="Students",title="Mean available CIA score"),330),use_container_width=True)
        with right:
            st.subheader("Risk distribution")
            risk_counts=summary.risk_level.value_counts().reindex(["Low","Medium","High"],fill_value=0).rename_axis("Risk").reset_index(name="Students")
            st.plotly_chart(plot_layout(px.pie(risk_counts,names="Risk",values="Students",hole=.68,title="Rule-based risk categories"),330),use_container_width=True)
        l,r=st.columns(2)
        with l:
            st.subheader("CIA assessment comparison")
            means=df[["cia1","cia2","cia3"]].mean().dropna()
            if not means.empty:
                x=pd.DataFrame({"Assessment":means.index.str.upper(),"Average mark":means.values})
                st.plotly_chart(plot_layout(px.bar(x,x="Assessment",y="Average mark",text_auto=".1f",title="Class mean by assessment"),300),use_container_width=True)
            else: st.info("No CIA marks available.")
        with r:
            st.subheader("Subject-wise performance")
            sub=df.melt(id_vars=["subject"],value_vars=["cia1","cia2","cia3"],var_name="Assessment",value_name="Mark").dropna()
            if not sub.empty:
                subavg=sub.groupby("subject",as_index=False).Mark.mean().sort_values("Mark")
                st.plotly_chart(plot_layout(px.bar(subavg,x="Mark",y="subject",orientation="h",title="Average available CIA mark",text_auto=".1f"),300),use_container_width=True)
            else: st.info("No subject marks available.")
        st.divider()
        left,right=st.columns([1.2,1])
        with left:
            st.subheader("Students requiring attention")
            risk=summary[summary.risk_level=="High"].head(8)
            if risk.empty: st.success("No students currently meet the high-risk threshold.")
            else: st.dataframe(risk[["register_no","student_name","department","average_score","attendance","risk_score","risk_factors"]],hide_index=True,use_container_width=True)
        with right:
            st.subheader("Recent academic alerts")
            alerts=summary[(summary.risk_level!="Low") | (summary.decline>=10)].head(7)
            if alerts.empty: st.success("No alerts generated from the current data.")
            for _,r in alerts.iterrows():
                st.markdown(f"**{r.student_name}** · {r.risk_level} risk  \n<small>{r.risk_factors}</small>",unsafe_allow_html=True)
                st.markdown("---")

# ---------- Risk Assessment ----------
elif page=="Risk Assessment":
    st.markdown("Risk scores are configurable rule-based indicators, not machine-learning predictions or guaranteed exam outcomes.")
    with st.expander("Scoring settings",expanded=False):
        pass_mark=st.slider("Target CIA average (%)",30,70,50,1)
        attendance_weight=st.slider("Maximum attendance contribution",0,25,15,1)
        trend_weight=st.slider("Maximum decline contribution",0,30,20,1)
    rs=student_summary(df,pass_mark,attendance_weight,trend_weight)
    if rs.empty: st.warning("No records available in this dataset.")
    else:
        filtered=get_filtered(rs,"risk")
        categories=st.multiselect("Risk categories",["High","Medium","Low"],default=["High","Medium","Low"],key="risk_categories")
        filtered=filtered[filtered.risk_level.isin(categories)]
        st.dataframe(filtered[["register_no","student_name","department","year","section","average_score","attendance","decline","risk_score","risk_level","risk_factors"]],hide_index=True,use_container_width=True)
        st.download_button("Export risk ranking CSV",filtered.to_csv(index=False).encode("utf-8"),"semscore_risk_ranking.csv","text/csv")
        if not filtered.empty:
            st.subheader("Risk profile")
            chosen=st.selectbox("Select student",filtered.register_no+" · "+filtered.student_name,key="risk_detail")
            reg=chosen.split(" · ")[0]
            r=filtered[filtered.register_no==reg].iloc[0]
            a,b,c=st.columns(3)
            a.metric("Risk score",f"{r.risk_score:.1f}/100")
            b.metric("Classification",r.risk_level)
            c.metric("Mean CIA score",f"{r.average_score:.1f}%" if pd.notna(r.average_score) else "Not available")
            st.markdown("**Contributing factors**")
            st.write(r.risk_factors)
            st.markdown("**Suggested interventions**")
            st.write(r.recommendations)

# ---------- Student Explorer ----------
elif page=="Student Explorer":
    if df.empty: st.warning("No records yet. Import a CSV in Data Management.")
    else:
        unique=summary.copy()
        filtered=get_filtered(unique,"explorer")
        st.caption(f"{len(filtered)} of {len(unique)} students shown")
        st.dataframe(filtered[["register_no","student_name","department","year","section","average_score","latest_score","attendance","risk_level","risk_score"]],hide_index=True,use_container_width=True)
        st.download_button("Export filtered directory",filtered.to_csv(index=False).encode("utf-8"),"semscore_student_directory.csv","text/csv")
        st.divider()
        st.subheader("Student record")
        options=(filtered.register_no+" · "+filtered.student_name).tolist()
        if options:
            default=options[0]
            if st.session_state.selected_student in options: default=st.session_state.selected_student
            selected=st.selectbox("Choose a student",options,index=options.index(default),key="explorer_student")
            st.session_state.selected_student=selected
            reg=selected.split(" · ")[0]
            sg=df[df.register_no.astype(str)==reg].copy()
            sr=summary[summary.register_no.astype(str)==reg].iloc[0]
            a,b,c,d=st.columns(4)
            a.metric("Average CIA",f"{sr.average_score:.1f}%" if pd.notna(sr.average_score) else "—")
            b.metric("Risk",sr.risk_level)
            c.metric("Attendance",f"{sr.attendance:.1f}%" if pd.notna(sr.attendance) else "—")
            d.metric("Latest assessment",f"{sr.latest_score:.1f}" if pd.notna(sr.latest_score) else "—")
            st.write(f"**Department:** {sg.iloc[0].department}  ·  **Year:** {sg.iloc[0]['year']}  ·  **Section:** {sg.iloc[0].section}")
            st.write(f"**Risk factors:** {sr.risk_factors}")
            st.dataframe(sg[["subject","cia1","cia2","cia3","attendance","previous_result","semester"]],hide_index=True,use_container_width=True)
            long=sg.melt(id_vars="subject",value_vars=["cia1","cia2","cia3"],var_name="Assessment",value_name="Mark").dropna()
            if not long.empty:
                st.plotly_chart(plot_layout(px.line(long,x="Assessment",y="Mark",color="subject",markers=True,title="Student assessment history"),320),use_container_width=True)
            with st.expander("Edit student record"):
                subject=st.selectbox("Subject row to edit",sg.subject.tolist(),key="edit_subject")
                old=sg[sg.subject==subject].iloc[0]
                with st.form("edit_student_form"):
                    nm=st.text_input("Student name",str(old.student_name))
                    dept=st.text_input("Department",str(old.department))
                    year=st.text_input("Year",str(old["year"]))
                    section=st.text_input("Section",str(old.section))
                    cia1=st.number_input("CIA 1",0.0,100.0,float(old.cia1) if pd.notna(old.cia1) else 0.0)
                    cia2=st.number_input("CIA 2",0.0,100.0,float(old.cia2) if pd.notna(old.cia2) else 0.0)
                    has3=st.checkbox("CIA 3 mark available",value=pd.notna(old.cia3))
                    cia3=st.number_input("CIA 3",0.0,100.0,float(old.cia3) if pd.notna(old.cia3) else 0.0,disabled=not has3)
                    att=st.number_input("Attendance (%)",0.0,100.0,float(old.attendance) if pd.notna(old.attendance) else 0.0)
                    save=st.form_submit_button("Save changes")
                if save:
                    con.execute("""UPDATE students SET student_name=?,department=?,year=?,section=?,cia1=?,cia2=?,cia3=?,attendance=?,updated_at=?
                        WHERE register_no=? AND subject=? AND source=?""",(nm,dept,year,section,cia1,cia2,cia3 if has3 else None,att,datetime.now().isoformat(timespec="seconds"),reg,subject,source))
                    con.commit()
                    st.success("Record updated. Refreshing the data view…")
                    st.rerun()

# ---------- CIA Analytics ----------
elif page=="CIA Analytics":
    if df.empty: st.warning("No records available.")
    else:
        st.subheader("Assessment comparison")
        long=df.melt(id_vars=["register_no","student_name","department","subject"],value_vars=["cia1","cia2","cia3"],var_name="Assessment",value_name="Mark").dropna()
        if long.empty: st.info("CIA marks are missing. Missing marks are excluded, not treated as zero.")
        else:
            c1,c2=st.columns(2)
            with c1:
                av=long.groupby("Assessment",as_index=False).Mark.mean()
                st.plotly_chart(plot_layout(px.bar(av,x="Assessment",y="Mark",text_auto=".1f",title="Mean CIA mark"),320),use_container_width=True)
            with c2:
                sub=long.groupby("subject",as_index=False).Mark.mean().sort_values("Mark")
                st.plotly_chart(plot_layout(px.bar(sub,x="Mark",y="subject",orientation="h",text_auto=".1f",title="Subject average"),320),use_container_width=True)
            st.subheader("Student-wise progress")
            chosen_dept=st.selectbox("Department filter",["All"]+sorted(df.department.dropna().astype(str).unique()),key="analytics_dept")
            prog=long.copy()
            if chosen_dept!="All": prog=prog[prog.department==chosen_dept]
            student_opts=sorted(prog.student_name.dropna().unique())
            if student_opts:
                picked=st.multiselect("Students to compare",student_opts,default=student_opts[:min(6,len(student_opts))])
                view=prog[prog.student_name.isin(picked)]
                if not view.empty:
                    st.plotly_chart(plot_layout(px.line(view,x="Assessment",y="Mark",color="student_name",line_group="subject",markers=True,title="CIA progress by student and subject"),390),use_container_width=True)
            st.subheader("Pass / below-target distribution")
            threshold=st.slider("Below-target threshold (%)",30,70,50,key="analytics_threshold")
            student_subject=long.groupby(["register_no","student_name","subject"],as_index=False).Mark.mean()
            student_subject["Outcome"]=np.where(student_subject.Mark>=threshold,"At/above target","Below target")
            pass_counts=student_subject.Outcome.value_counts().rename_axis("Outcome").reset_index(name="Subject records")
            st.plotly_chart(plot_layout(px.pie(pass_counts,names="Outcome",values="Subject records",hole=.55,title="Subject-average target status"),300),use_container_width=True)
            if "semester" in df and df.semester.nunique()>1:
                sem=df.melt(id_vars=["semester","department"],value_vars=["cia1","cia2","cia3"],value_name="Mark").dropna()
                sem=sem.groupby(["semester","department"],as_index=False).Mark.mean()
                st.plotly_chart(plot_layout(px.bar(sem,x="semester",y="Mark",color="department",barmode="group",title="Semester and department comparison"),320),use_container_width=True)

# ---------- Improvement Planner ----------
elif page=="Improvement Planner":
    if df.empty: st.warning("No records available.")
    else:
        opts=(summary.register_no+" · "+summary.student_name).tolist()
        selected=st.selectbox("Student",opts,key="planner_student")
        reg=selected.split(" · ")[0]
        sg=df[df.register_no.astype(str)==reg]
        sr=summary[summary.register_no.astype(str)==reg].iloc[0]
        st.subheader(f"Plan for {sr.student_name}")
        st.caption("Recommendations are generated from recorded marks, attendance and assessment trends.")
        st.write(f"**Current risk:** {sr.risk_level} ({sr.risk_score:.0f}/100) · **Average CIA:** {sr.average_score if pd.notna(sr.average_score) else 'Unavailable'} · **Attendance:** {sr.attendance if pd.notna(sr.attendance) else 'Unavailable'}")
        st.markdown("**Data-linked recommendations**")
        st.write(sr.recommendations)
        weak=[]
        for _,r in sg.iterrows():
            vals=[r[c] for c in ["cia1","cia2","cia3"] if pd.notna(r[c])]
            if vals and np.mean(vals)<60: weak.append((r.subject,float(np.mean(vals))))
        weak=sorted(weak,key=lambda x:x[1])
        st.markdown("**Suggested weekly study plan**")
        tasks=[]
        if weak:
            for sub,score in weak[:3]:
                tasks.append({"Goal":f"Revise {sub} (current average {score:.1f}%)","Target":"2 focused sessions + 10 practice questions","Done":False})
        else:
            tasks.append({"Goal":"Maintain subject consistency","Target":"One timed practice set in each subject","Done":False})
        tasks += [{"Goal":"Review CIA mistakes","Target":"Create an error log and redo incorrect questions","Done":False},
                  {"Goal":"Progress check","Target":"Compare next assessment with current baseline","Done":False}]
        task_key=f"tasks_{source}_{reg}"
        if task_key not in st.session_state: st.session_state[task_key]=tasks
        current=st.session_state[task_key]
        for i,t in enumerate(current):
            current[i]["Done"]=st.checkbox(f"{t['Goal']} — {t['Target']}",value=t["Done"],key=f"{task_key}_{i}")
        done=sum(1 for t in current if t["Done"])
        st.progress(done/max(1,len(current)),text=f"{done} of {len(current)} weekly goals completed")
        if st.button("Reset weekly plan",key="reset_plan"):
            st.session_state[task_key]=[dict(t,Done=False) for t in tasks]
            st.rerun()
        st.download_button("Download study plan",pd.DataFrame(current).to_csv(index=False).encode(),f"study_plan_{reg}.csv","text/csv")

# ---------- AI Assistant ----------
elif page=="AI Assistant":
    st.markdown("Ask questions about the active dataset. Answers are generated locally from records; no external LLM is required.")
    question=st.text_input("Ask an academic question",placeholder="e.g. Which students are currently at high risk?")
    if st.button("Analyze question",type="primary") and question.strip():
        q=question.lower()
        if df.empty:
            st.warning("The active dataset is empty. Switch to Demo dataset or import a CSV.")
        elif any(x in q for x in ["high risk","at risk","risk students","risk ranking"]):
            result=summary[summary.risk_level=="High"]
            st.write(f"**{len(result)} high-risk student(s)** found in the active dataset.")
            st.dataframe(result[["register_no","student_name","department","risk_score","risk_factors"]],hide_index=True,use_container_width=True)
        elif "lowest" in q and ("subject" in q or "class average" in q):
            av=df.melt(id_vars="subject",value_vars=["cia1","cia2","cia3"],value_name="Mark").dropna().groupby("subject").Mark.mean().sort_values()
            if av.empty: st.info("No CIA marks available.")
            else: st.write(f"**Lowest subject average:** {av.index[0]} ({av.iloc[0]:.1f}%)."); st.dataframe(av.rename("Average mark").reset_index(),hide_index=True)
        elif "declin" in q or "drop" in q or "fall" in q:
            result=summary[summary.decline>=5].sort_values("decline",ascending=False)
            st.write(f"**{len(result)} student(s)** show a decline of at least 5 points from first available to latest available assessment.")
            st.dataframe(result[["register_no","student_name","decline","average_score","risk_level"]],hide_index=True,use_container_width=True)
        elif "cia" in q and ("compare" in q or "average" in q or "performance" in q):
            av=df[["cia1","cia2","cia3"]].mean().dropna()
            if av.empty: st.info("No CIA marks available.")
            else:
                st.write("Class averages by assessment:")
                st.dataframe(av.rename_axis("Assessment").rename("Average mark").reset_index(),hide_index=True)
                st.write("Missing marks are excluded from each average.")
        else:
            match=summary[summary.student_name.astype(str).str.lower().apply(lambda n:n in q) | summary.register_no.astype(str).str.lower().apply(lambda n:n in q)]
            if not match.empty:
                r=match.iloc[0]
                st.markdown(f"### {r.student_name} · {r.risk_level} risk")
                st.write(f"Risk score: {r.risk_score:.1f}/100. Average score: {r.average_score if pd.notna(r.average_score) else 'unavailable'}.")
                st.write("**Factors:** "+r.risk_factors)
                st.write("**Recommended interventions:** "+r.recommendations)
            else:
                st.warning("I couldn't map that question to a supported analysis. Try: “Which students are high risk?”, “Which subject has the lowest class average?”, “Which students have declining marks?”, or include a student's name/register number.")
    st.divider()
    st.markdown("**Example questions**")
    for ex in ["Which students are currently at high risk?","Which subject has the lowest class average?","Which students have declining marks?","How does CIA performance compare across assessments?"]:
        st.markdown(f"- {ex}")

# ---------- Reports ----------
elif page=="Reports":
    if df.empty: st.warning("No records available to report.")
    else:
        st.subheader("Student report")
        opts=(summary.register_no+" · "+summary.student_name).tolist()
        selected=st.selectbox("Student for report",opts,key="report_student")
        reg=selected.split(" · ")[0]
        sg=df[df.register_no.astype(str)==reg]
        sr=summary[summary.register_no.astype(str)==reg].iloc[0]
        report={"Register number":reg,"Student name":sr.student_name,"Department":sr.department,"Year":sr.year,"Section":sr.section,
                "Average CIA score":sr.average_score,"Latest available CIA score":sr.latest_score,"Attendance":sr.attendance,
                "Risk score":sr.risk_score,"Risk classification":sr.risk_level,"Risk factors":sr.risk_factors,"Recommendations":sr.recommendations}
        st.json({k:(None if pd.isna(v) else v) for k,v in report.items()})
        student_csv=sg[["register_no","student_name","department","year","section","subject","cia1","cia2","cia3","attendance","previous_result","semester"]].to_csv(index=False).encode("utf-8")
        st.download_button("Download student report (CSV)",student_csv,f"student_report_{reg}.csv","text/csv")
        report_df=pd.DataFrame([report])
        st.download_button("Download student summary (CSV)",report_df.to_csv(index=False).encode("utf-8"),f"student_summary_{reg}.csv","text/csv")
        st.divider()
        st.subheader("Class report")
        class_df=summary.copy()
        st.dataframe(class_df[["register_no","student_name","department","average_score","attendance","risk_score","risk_level","risk_factors","recommendations"]],hide_index=True,use_container_width=True)
        st.download_button("Download class report (CSV)",class_df.to_csv(index=False).encode("utf-8"),"semscore_class_report.csv","text/csv")
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            buf=io.BytesIO()
            doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=36,leftMargin=36,topMargin=36,bottomMargin=36)
            styles=getSampleStyleSheet()
            story=[Paragraph("SemScore AI — Student Academic Report",styles["Title"]),Spacer(1,14)]
            for k,v in report.items():
                if pd.isna(v): v="Not available"
                story.append(Paragraph(f"<b>{k}:</b> {str(v)}",styles["BodyText"]))
                story.append(Spacer(1,5))
            story += [Spacer(1,12),Paragraph("Subject-wise CIA marks",styles["Heading2"])]
            table_data=[["Subject","CIA 1","CIA 2","CIA 3","Attendance"]]
            for _,rr in sg.iterrows():
                table_data.append([str(rr.subject),*[("—" if pd.isna(rr[c]) else f"{rr[c]:.1f}") for c in ["cia1","cia2","cia3","attendance"]]])
            tbl=Table(table_data,repeatRows=1)
            tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17345c")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("GRID",(0,0),(-1,-1),.4,colors.grey),("PADDING",(0,0),(-1,-1),6)]))
            story.append(tbl)
            doc.build(story)
            st.download_button("Download student report (PDF)",buf.getvalue(),f"student_report_{reg}.pdf","application/pdf")
        except Exception as e:
            st.error(f"PDF generation is unavailable in this environment: {e}. CSV reports remain available.")

# ---------- Data Management ----------
elif page=="Data Management":
    st.markdown("Import, validate and maintain your uploaded dataset. Uploaded records are stored separately from fictional demo records.")
    st.subheader("Import CSV")
    up=st.file_uploader("Choose a student CSV file",type=["csv"],key="csv_uploader")
    if up is not None:
        try:
            uploaded=pd.read_csv(up)
            st.write("**Preview**")
            st.dataframe(uploaded.head(10),use_container_width=True)
            normalized, errors, warnings=validate_and_normalize(uploaded)
            if warnings:
                for w in warnings: st.warning(w)
            if errors:
                for e in errors: st.error(e)
            else:
                st.success(f"Validation passed: {len(normalized)} unique student-subject rows.")
                st.caption("Recognized columns are normalized automatically. Required fields: register number and student name.")
                if st.button("Import / update uploaded records",type="primary"):
                    write_records(con,normalized,"uploaded")
                    st.success(f"Imported or updated {len(normalized)} row(s) in the uploaded dataset.")
                    st.rerun()
        except Exception as e: st.error(f"Could not read this CSV: {e}")
    st.divider()
    st.subheader("Uploaded data inventory")
    upload_df=load_data(con,"uploaded")
    x,y,z=st.columns(3)
    x.metric("Student-subject rows",len(upload_df))
    y.metric("Unique students",upload_df.register_no.nunique() if not upload_df.empty else 0)
    z.metric("Subjects",upload_df.subject.nunique() if not upload_df.empty else 0)
    if not upload_df.empty:
        st.dataframe(upload_df.drop(columns=["id"],errors="ignore"),hide_index=True,use_container_width=True)
        st.download_button("Export uploaded data CSV",upload_df.drop(columns=["id","source","updated_at"],errors="ignore").to_csv(index=False).encode(), "semscore_uploaded_data.csv","text/csv")
        if st.button("Delete all uploaded records",type="secondary"):
            st.session_state.confirm_delete=True
        if st.session_state.get("confirm_delete",False):
            st.warning("This permanently deletes uploaded records from this app's SQLite database.")
            c1,c2=st.columns(2)
            if c1.button("Confirm delete"):
                con.execute("DELETE FROM students WHERE source='uploaded'"); con.commit()
                st.session_state.confirm_delete=False; st.success("Uploaded records deleted."); st.rerun()
            if c2.button("Cancel"):
                st.session_state.confirm_delete=False; st.rerun()
    else:
        st.info("No uploaded records yet. A sample CSV is included in the project.")
    st.divider()
    st.subheader("CSV column guide")
    st.markdown("Required: `register_no`, `student_name`. Optional: `department`, `year`, `section`, `subject`, `cia1`, `cia2`, `cia3`, `attendance`, `previous_result`, `semester`. Marks and attendance must be 0–100. Blank CIA values stay missing.")

# ---------- Settings ----------
elif page=="Settings":
    st.subheader("Risk scoring policy")
    st.markdown("""
    **Baseline scoring model (transparent rules):**
    - Missing all CIA marks: adds a 35-point data-risk signal.
    - Mean CIA below target: adds a score proportional to the gap.
    - Borderline mean CIA (below 60%): adds 15 points.
    - Attendance below 75%: adds a configurable contribution.
    - Decline of 10 or more points from CIA 1 to the latest available assessment: adds a trend contribution.
    - Each subject averaging below target adds a limited contribution.

    Classification defaults: **Low** below 30, **Medium** from 30–59.9, **High** at 60 and above. The score is a support prioritization aid, not a diagnosis or guaranteed prediction.
    """)
    st.subheader("Application information")
    st.write(f"Database path: `{DB_PATH}`")
    st.write(f"Active dataset: **{source}**")
    st.write(f"App version: **1.1.0**")
    st.warning("For public deployments, do not upload real identifiable student data to an unauthenticated app. Use fictional/demo data for presentations. Streamlit Community Cloud local files may not be durable across app restarts or redeployments; use managed external storage for important records.")
    st.subheader("Optional LLM integration")
    st.write("The assistant currently uses deterministic local analysis and does not send student data to an external service. An LLM API can be added later using Streamlit secrets, but is not required.")

con.close()
