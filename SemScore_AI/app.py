
import streamlit as st
import pandas as pd
import math

st.set_page_config(
    page_title="SemScore AI",
    page_icon="🎓",
    layout="wide"
)

# ---------------- CONFIGURATION ----------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
  --bg: #070b14;
  --panel: #0f1728;
  --panel-2: #131f34;
  --border: rgba(148, 163, 184, .16);
  --blue: #60a5fa;
  --cyan: #67e8f9;
  --text: #e8eef9;
  --muted: #94a3b8;
}
.stApp {
  background:
    radial-gradient(ellipse at 12% 0%, rgba(37,99,235,.16), transparent 34%),
    radial-gradient(ellipse at 90% 10%, rgba(124,58,237,.12), transparent 30%),
    var(--bg);
  color: var(--text);
  font-family: 'DM Sans', sans-serif;
}
[data-testid="stHeader"] { background: rgba(7,11,20,.72); }
.block-container { max-width: 1440px; padding-top: 1.8rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0e1728 0%, #0a1020 100%);
  border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] > div { padding-top: 1.5rem; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -.035em; }
h1 { color: #f8fafc !important; font-size: clamp(2.1rem, 4vw, 3rem) !important; }
h2 { color: #e8eef9 !important; margin-top: 1.2rem !important; }
h3 { color: #cbd5e1 !important; }
p, label, .stMarkdown { color: var(--text); }
[data-testid="stMetric"] {
  background: linear-gradient(145deg, rgba(20,33,56,.96), rgba(13,22,39,.96));
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 19px 20px;
  box-shadow: 0 12px 28px rgba(0,0,0,.14);
  transition: border-color .2s ease, transform .2s ease;
}
[data-testid="stMetric"]:hover { border-color: rgba(96,165,250,.5); transform: translateY(-2px); }
[data-testid="stMetricLabel"] { color: #a9b8ce !important; font-size: .88rem !important; }
[data-testid="stMetricValue"] { color: var(--blue) !important; font-family: 'Space Grotesk', sans-serif; }
[data-testid="stMetricDelta"] { font-size: .82rem; }
div[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: var(--border) !important;
  border-radius: 16px !important;
}
div.stButton > button, div.stDownloadButton > button {
  background: linear-gradient(100deg, #2563eb, #4f46e5);
  color: white; border: 1px solid rgba(147,197,253,.22);
  border-radius: 11px; padding: .55rem 1rem; font-weight: 700;
  transition: all .18s ease;
}
div.stButton > button:hover, div.stDownloadButton > button:hover {
  border-color: #93c5fd; box-shadow: 0 0 22px rgba(59,130,246,.2);
  color: white; transform: translateY(-1px);
}
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {
  background: #0e192b; border-color: #2a3b56; border-radius: 10px;
}
[data-testid="stDataFrame"], [data-testid="stTable"] {
  border: 1px solid var(--border); border-radius: 13px; overflow: hidden;
}
[data-testid="stAlert"] { border-radius: 12px; }
hr { border-color: var(--border) !important; margin: 1.4rem 0 !important; }
[data-testid="stProgressBar"] > div > div { background: linear-gradient(90deg,#3b82f6,#22d3ee); }
small, .stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
@media (max-width: 768px) {
  .block-container { padding: 1rem .8rem 2rem; }
  [data-testid="stMetric"] { padding: 13px; }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="
  padding: 1.35rem 1.5rem; margin: .2rem 0 1.25rem;
  border: 1px solid rgba(96,165,250,.24); border-radius: 20px;
  background: linear-gradient(115deg, rgba(20,38,69,.92), rgba(17,24,48,.82) 60%, rgba(49,29,83,.55));
  box-shadow: 0 18px 48px rgba(0,0,0,.18);">
  <div style="font-size:.76rem; font-weight:700; letter-spacing:.16em; color:#67e8f9; text-transform:uppercase;">
    Academic intelligence platform
  </div>
  <div style="font-family:'Space Grotesk',sans-serif; font-size:clamp(2rem,4vw,3rem); font-weight:700; letter-spacing:-.045em; color:#f8fafc; margin-top:.3rem;">
    SemScore <span style="color:#60a5fa;">AI</span>
  </div>
  <div style="font-size:1rem; color:#b6c5da; margin-top:.25rem;">
    Turn your current marks into a clear CIA 3 action plan.
  </div>
  <div style="display:flex; flex-wrap:wrap; gap:.5rem; margin-top:1rem;">
    <span style="padding:.35rem .7rem; border-radius:999px; background:rgba(96,165,250,.12); border:1px solid rgba(96,165,250,.22); color:#bfdbfe; font-size:.8rem;">CIA 3 Goal Predictor</span>
    <span style="padding:.35rem .7rem; border-radius:999px; background:rgba(103,232,249,.08); border:1px solid rgba(103,232,249,.18); color:#a5f3fc; font-size:.8rem;">CGPA Planning</span>
    <span style="padding:.35rem .7rem; border-radius:999px; background:rgba(167,139,250,.09); border:1px solid rgba(167,139,250,.2); color:#ddd6fe; font-size:.8rem;">Personal Study Plan</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR SETTINGS ----------------

st.sidebar.title("Academic Settings")

target_cgpa = st.sidebar.number_input(
    "Target CGPA",
    min_value=0.0,
    max_value=10.0,
    value=8.5,
    step=0.1
)

cia_max = st.sidebar.number_input(
    "Maximum marks per CIA",
    min_value=1,
    max_value=100,
    value=50
)

internal_max = st.sidebar.number_input(
    "Maximum internal marks",
    min_value=1,
    max_value=100,
    value=40
)

exam_max = st.sidebar.number_input(
    "Maximum semester exam marks",
    min_value=1,
    max_value=200,
    value=100
)

exam_weight = st.sidebar.number_input(
    "Semester exam contribution",
    min_value=0,
    max_value=100,
    value=60
)

exam_weight = float(exam_weight)
internal_weight = st.sidebar.number_input(
    "Internal contribution",
    min_value=0,
    max_value=100,
    value=40
)

if exam_weight + internal_weight == 0:
    st.sidebar.error("Internal and exam contributions cannot both be zero.")
    st.stop()

st.sidebar.caption(
    "Confirm these values with your college's official assessment scheme."
)

st.sidebar.subheader("Grade boundaries (illustrative)")
grade_cutoffs = {
    "O": st.sidebar.number_input("O grade minimum (%)", 0, 100, 90),
    "A+": st.sidebar.number_input("A+ minimum (%)", 0, 100, 80),
    "A": st.sidebar.number_input("A minimum (%)", 0, 100, 70),
    "B+": st.sidebar.number_input("B+ minimum (%)", 0, 100, 60),
    "B": st.sidebar.number_input("B minimum (%)", 0, 100, 50),
}

grade_points = {
    "O": 10,
    "A+": 9,
    "A": 8,
    "B+": 7,
    "B": 6,
    "C": 5,
    "U": 0,
}

st.sidebar.subheader("Previous academic record")

previous_cgpa = st.sidebar.number_input(
    "Current CGPA",
    min_value=0.0,
    max_value=10.0,
    value=7.5,
    step=0.01
)

completed_credits = st.sidebar.number_input(
    "Credits completed before this semester",
    min_value=0,
    max_value=300,
    value=20
)

# ---------------- PERSONAL GOALS ----------------

st.header("1. Your Study Goals")

col1, col2, col3 = st.columns(3)

with col1:
    study_hours = st.number_input(
        "Daily study hours",
        min_value=1.0,
        max_value=12.0,
        value=3.5,
        step=0.5
    )

with col2:
    expected_exam = st.slider(
        "Expected semester exam mark (%)",
        min_value=0,
        max_value=100,
        value=75
    )

with col3:
    desired_final = st.slider(
        "Target final subject score (%)",
        min_value=0,
        max_value=100,
        value=80
    )

st.info(
    "Enter your real marks below. CIA 3 targets and exam requirements "
    "are estimates based on the assessment settings you choose."
)

# ---------------- SUBJECT INPUT ----------------

st.header("2. Enter Your Subject Marks")

if "subjects" not in st.session_state:
    st.session_state.subjects = pd.DataFrame({
        "Subject": ["Subject 1", "Subject 2", "Subject 3"],
        "Credits": [3, 4, 4],
        "CIA 1": [30, 30, 30],
        "CIA 2": [30, 30, 30],
        "CIA 3": [0, 0, 0],
    })

edited = st.data_editor(
    st.session_state.subjects,
    num_rows="dynamic",
    use_container_width=True,
    key="subject_editor",
    column_config={
        "Subject": st.column_config.TextColumn(
            "Subject name", required=True
        ),
        "Credits": st.column_config.NumberColumn(
            "Credits", min_value=1, max_value=10, step=1
        ),
        "CIA 1": st.column_config.NumberColumn(
            "CIA 1", min_value=0, max_value=cia_max
        ),
        "CIA 2": st.column_config.NumberColumn(
            "CIA 2", min_value=0, max_value=cia_max
        ),
        "CIA 3": st.column_config.NumberColumn(
            "CIA 3", min_value=0, max_value=cia_max
        ),
    },
)

if edited.empty:
    st.warning("Add at least one subject to begin.")
    st.stop()

st.session_state.subjects = edited.copy()

required_columns = ["Subject", "Credits", "CIA 1", "CIA 2", "CIA 3"]

if any(c not in edited.columns for c in required_columns):
    st.error("Please keep the required subject columns.")
    st.stop()

numeric_columns = ["Credits", "CIA 1", "CIA 2", "CIA 3"]
for column in numeric_columns:
    edited[column] = pd.to_numeric(edited[column], errors="coerce")

if edited[numeric_columns].isna().any().any():
    st.error("Enter valid numbers for credits and CIA marks.")
    st.stop()

if (edited["Credits"] <= 0).any():
    st.error("Credits must be greater than zero.")
    st.stop()

for column in ["CIA 1", "CIA 2", "CIA 3"]:
    if ((edited[column] < 0) | (edited[column] > cia_max)).any():
        st.error(f"{column} must be between 0 and {cia_max}.")
        st.stop()

if (edited["Subject"].astype(str).str.strip() == "").any():
    st.error("Every subject needs a name.")
    st.stop()

# ---------------- CALCULATIONS ----------------

def get_grade(score):
    for grade, cutoff in sorted(
        grade_cutoffs.items(),
        key=lambda item: item[1],
        reverse=True
    ):
        if score >= cutoff:
            return grade
    return "U"


def grade_point(score):
    return grade_points[get_grade(score)]


def internal_score(cia1, cia2, cia3):
    average = (cia1 + cia2 + cia3) / 3
    return (average / cia_max) * internal_max


def final_score(internal, exam_percent):
    total_weight = internal_weight + exam_weight
    return (
        internal * internal_weight
        + exam_percent * exam_weight
    ) / total_weight


results = []

for _, row in edited.iterrows():
    subject = str(row["Subject"])
    credits = int(row["Credits"])
    cia1 = float(row["CIA 1"])
    cia2 = float(row["CIA 2"])
    cia3 = float(row["CIA 3"])

    current_internal = internal_score(cia1, cia2, cia3)

    estimated_final = final_score(
        current_internal,
        expected_exam
    )

    # CIA 3 required for the desired final score,
    # assuming the selected expected exam percentage.
    required_internal = (
        desired_final * (internal_weight + exam_weight)
        - expected_exam * exam_weight
    ) / internal_weight if internal_weight > 0 else 0

    required_average_cia = (
        required_internal / internal_max
    ) * cia_max

    required_cia3 = required_average_cia * 3 - cia1 - cia2

    if internal_weight == 0:
        required_cia3 = 0

    if required_cia3 <= 0:
        cia_message = "CIA target already covered"
    elif required_cia3 > cia_max:
        cia_message = "Target not reachable with CIA 3 alone"
    else:
        cia_message = f"Target CIA 3: {math.ceil(required_cia3)}/{cia_max}"

    # Semester exam mark required for the desired final score.
    if exam_weight > 0:
        required_exam = (
            desired_final * (internal_weight + exam_weight)
            - current_internal * internal_weight
        ) / exam_weight
    else:
        required_exam = 0

    required_exam = max(0, required_exam)
    achievable = required_exam <= 100

    results.append({
        "Subject": subject,
        "Credits": credits,
        "CIA 1": cia1,
        "CIA 2": cia2,
        "CIA 3": cia3,
        "Internal score": round(current_internal, 2),
        "Estimated final (%)": round(estimated_final, 2),
        "CIA 3 guidance": cia_message,
        "Exam needed (%)": (
            round(required_exam, 1) if achievable else "Over 100%"
        ),
        "Estimated grade": get_grade(estimated_final),
        "Grade point": grade_point(estimated_final),
    })

result_df = pd.DataFrame(results)

total_credits = int(result_df["Credits"].sum())

if total_credits <= 0:
    st.error("Your total subject credits must be greater than zero.")
    st.stop()

semester_gpa = (
    result_df["Credits"] * result_df["Grade point"]
).sum() / total_credits

if completed_credits + total_credits > 0:
    projected_cgpa = (
        previous_cgpa * completed_credits
        + semester_gpa * total_credits
    ) / (completed_credits + total_credits)
else:
    projected_cgpa = semester_gpa

# ---------------- DASHBOARD ----------------

st.header("3. Your Academic Dashboard")

m1, m2, m3 = st.columns(3)

m1.metric("Target CGPA", f"{target_cgpa:.2f}")
m2.metric("Projected Semester GPA", f"{semester_gpa:.2f}")
m3.metric("Projected CGPA", f"{projected_cgpa:.2f}")

if projected_cgpa >= target_cgpa:
    st.success("Your current scenario meets your CGPA goal.")
else:
    st.warning(
        "Your current scenario is below your target. "
        "Improve CIA 3 and semester-exam scores, then recalculate."
    )

st.caption(
    "GPA calculations use the configurable grade cutoffs and grade points. "
    "These are planning estimates, not official university results."
)

# ---------------- CIA 3 VISUAL OVERVIEW (UI ADDITION) ----------------

st.header("4. CIA 3 Goal Predictor")
st.write(
    "Compare your current CIA marks and review the required CIA 3 guidance "
    "for each subject below. The existing assessment calculations are retained."
)

chart_col, summary_col = st.columns([1.45, 1])

with chart_col:
    st.markdown("#### Assessment marks by subject")
    chart_data = edited.set_index("Subject")[["CIA 1", "CIA 2", "CIA 3"]]
    st.bar_chart(chart_data, color=["#60a5fa", "#a78bfa", "#22d3ee"], height=300)

with summary_col:
    st.markdown("#### Current target settings")
    st.metric("Target final subject score", f"{desired_final:.0f}%")
    st.metric("Expected semester exam mark", f"{expected_exam:.0f}%")
    st.metric("Subjects in your plan", f"{len(result_df)}")
    st.caption(
        "Change marks or targets above to refresh the projection. "
        "Confirm the formula and grade boundaries with your college."
    )

# ---------------- SUBJECT PLAN ----------------

st.header("5. Subject-wise Recovery Plan")

st.dataframe(
    result_df,
    use_container_width=True,
    hide_index=True
)

st.download_button(
    "Download subject plan (CSV)",
    result_df.to_csv(index=False).encode("utf-8"),
    file_name="SemScore_subject_plan.csv",
    mime="text/csv",
)

# ---------------- STUDY TIMETABLE ----------------

st.header("6. Your Daily Study Timetable")

st.write(
    f"Your plan uses **{study_hours:.1f} hours per day**. "
    "Since semester preparation has not started, begin with fundamentals "
    "and gradually move toward problem practice and revision."
)

# Prioritize subjects with the lowest estimated final score.
ranked_subjects = result_df.sort_values(
    "Estimated final (%)",
    ascending=True
)["Subject"].tolist()

if not ranked_subjects:
    st.info("Add subjects to generate a study plan.")
    st.stop()

slots = [
    ("Session 1", 0.35, "Learn concepts and review class notes"),
    ("Session 2", 0.30, "Practice problems and important questions"),
    ("Session 3", 0.25, "Prepare CIA 3 and semester-exam answers"),
    ("Quick review", 0.10, "Recall formulas and revise mistakes"),
]

schedule = []
for index, (session, fraction, activity) in enumerate(slots):
    subject = ranked_subjects[index % len(ranked_subjects)]
    duration = round(study_hours * fraction, 2)
    schedule.append({
        "Session": session,
        "Duration (hours)": duration,
        "Subject priority": subject,
        "Task": activity,
    })

schedule_df = pd.DataFrame(schedule)

st.dataframe(
    schedule_df,
    use_container_width=True,
    hide_index=True
)

st.download_button(
    "Download study timetable (CSV)",
    schedule_df.to_csv(index=False).encode("utf-8"),
    file_name="SemScore_weekly_study_plan.csv",
    mime="text/csv",
)

# ---------------- WEEKLY CHECKLIST ----------------

st.header("7. Weekly Checklist")

checklist = [
    "Review CIA 1 and CIA 2 mistakes for each subject",
    "Complete one difficult topic per priority subject",
    "Practice important problems without looking at solutions",
    "Write at least one exam-style answer per theory subject",
    "Revise formulas, definitions, and key diagrams",
    "Take a timed self-test and record the marks",
    "Update CIA 3 targets after each practice test",
]

for item in checklist:
    st.checkbox(item, key="check_" + item)

# ---------------- CGPA SCENARIOS ----------------

st.header("8. CGPA Scenario Planner")

st.write(
    "Estimate the CGPA you could achieve with different semester GPAs."
)

scenario_gpas = [6.0, 7.0, 8.0, 8.5, 9.0, 9.5, 10.0]
scenario_rows = []

for gpa in scenario_gpas:
    total = completed_credits + total_credits
    projected = (
        previous_cgpa * completed_credits
        + gpa * total_credits
    ) / total if total else gpa

    scenario_rows.append({
        "Semester GPA scenario": gpa,
        "Projected CGPA": round(projected, 2),
        "Meets target": "Yes" if projected >= target_cgpa else "No",
    })

scenario_df = pd.DataFrame(scenario_rows)

st.dataframe(
    scenario_df,
    use_container_width=True,
    hide_index=True
)

st.download_button(
    "Download CGPA scenarios (CSV)",
    scenario_df.to_csv(index=False).encode("utf-8"),
    file_name="SemScore_CGPA_scenarios.csv",
    mime="text/csv",
)

# ---------------- DISCLAIMER ----------------

st.divider()
st.caption(
    "SemScore AI is a personal planning tool. Confirm CIA calculations, "
    "internal/exam weightings, grade boundaries, grade points, and credit "
    "rules with KRCE's official autonomous regulations before relying on "
    "the projections. This prototype does not guarantee a particular grade."
)
