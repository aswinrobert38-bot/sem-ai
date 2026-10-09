
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
    Track current internals, predict CIA 3, and plan your semester exam.
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

grade_cutoffs["C"] = st.sidebar.number_input(
    "C grade minimum (%)", min_value=0, max_value=100, value=40
)

st.sidebar.subheader("Grade points (enter your college values)")
grade_points = {
    "O": st.sidebar.number_input("O grade point", 0.0, 10.0, 10.0, 0.5),
    "A+": st.sidebar.number_input("A+ grade point", 0.0, 10.0, 9.0, 0.5),
    "A": st.sidebar.number_input("A grade point", 0.0, 10.0, 8.0, 0.5),
    "B+": st.sidebar.number_input("B+ grade point", 0.0, 10.0, 7.0, 0.5),
    "B": st.sidebar.number_input("B grade point", 0.0, 10.0, 6.0, 0.5),
    "C": st.sidebar.number_input("C grade point", 0.0, 10.0, 5.0, 0.5),
    "U": st.sidebar.number_input("U grade point", 0.0, 10.0, 0.0, 0.5),
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

st.header("2. Feed Your Academic Data")
st.caption("Use your own subjects and official assessment rules. The analytics below are calculated from the values you provide.")

# Users can either upload their own subject data or enter it in the table.
subject_template = pd.DataFrame({
    "Subject": ["Example subject"],
    "Credits": [3],
    "CIA 1": [30],
    "CIA 2": [30],
    "CIA 3 (out of 100)": [None],
    "Final Internal Marks": [None],
    "Semester Exam Marks": [None],
})
st.download_button(
    "Download subject data template (CSV)",
    subject_template.to_csv(index=False).encode("utf-8"),
    file_name="SemScore_subject_input_template.csv",
    mime="text/csv",
    help="Fill in your actual subjects, credits, and CIA marks, then upload the CSV."
)

uploaded_subjects = st.file_uploader(
    "Upload your subject data (CSV)",
    type=["csv"],
    key="subject_csv_upload",
    help="Required columns: Subject, Credits. Optional: Final Internal Marks, CIA 1, CIA 2, CIA 3 (out of 100), Semester Exam Marks. If Final Internal Marks is blank, enter component marks in the assessment section below."
)

if uploaded_subjects is not None and st.button("Import uploaded subject data", key="import_subject_csv"):
    try:
        incoming_subjects = pd.read_csv(uploaded_subjects)
        required_csv_cols = ["Subject", "Credits"]
        missing_cols = [c for c in required_csv_cols if c not in incoming_subjects.columns]
        if missing_cols:
            st.error("CSV is missing required columns: " + ", ".join(missing_cols))
        elif incoming_subjects.empty:
            st.error("The uploaded CSV has no subject rows.")
        else:
            for optional_col in ["Final Internal Marks", "CIA 1", "CIA 2", "CIA 3 (out of 100)", "Semester Exam Marks"]:
                if optional_col not in incoming_subjects.columns:
                    incoming_subjects[optional_col] = None
            expected_cols = ["Subject", "Credits", "Final Internal Marks", "CIA 1", "CIA 2", "CIA 3 (out of 100)", "Semester Exam Marks"]
            st.session_state.subjects = incoming_subjects[expected_cols].copy()
            st.success(f"Loaded {len(incoming_subjects)} subject(s) from your CSV.")
    except Exception as exc:
        st.error(f"Could not read that CSV: {exc}")

if "subjects" not in st.session_state:
    st.session_state.subjects = pd.DataFrame(columns=[
        "Subject", "Credits", "Final Internal Marks", "CIA 1", "CIA 2", "CIA 3 (out of 100)", "Semester Exam Marks"
    ])

# Keep older saved/imported tables compatible with the updated columns.
for _col in ["Final Internal Marks", "CIA 1", "CIA 2", "CIA 3 (out of 100)", "Semester Exam Marks"]:
    if _col not in st.session_state.subjects.columns:
        st.session_state.subjects[_col] = None

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
        "Final Internal Marks": st.column_config.NumberColumn(
            "Final Internal Marks (if portal provides it)", min_value=0, max_value=internal_max,
            step=0.01, required=False,
            help="If provided, SemScore AI uses this directly. Leave blank only when you need to calculate it from assessment components."
        ),
        "CIA 1": st.column_config.NumberColumn("CIA 1 (optional component data)", min_value=0, max_value=200, required=False),
        "CIA 2": st.column_config.NumberColumn("CIA 2 (optional component data)", min_value=0, max_value=200, required=False),
        "CIA 3 (out of 100)": st.column_config.NumberColumn(
            "CIA 3 (out of 100; leave blank if pending)", min_value=0, max_value=100,
            step=1, required=False,
            help="CIA 3 is scored out of 100. Its contribution to internal marks must follow the configured official assessment scheme."
        ),
        "Semester Exam Marks": st.column_config.NumberColumn(
            "Semester Exam Marks (optional)", min_value=0, max_value=exam_max,
            step=1, required=False,
            help="Leave blank before the semester exam. Enter actual marks after the exam."
        ),
    },
)

if edited.empty:
    st.warning("Add at least one subject to begin.")
    st.stop()

st.session_state.subjects = edited.copy()

required_columns = ["Subject", "Credits", "Final Internal Marks", "CIA 1", "CIA 2", "CIA 3 (out of 100)", "Semester Exam Marks"]

if any(c not in edited.columns for c in required_columns):
    st.error("Please keep the required subject columns.")
    st.stop()

required_numeric_columns = ["Credits"]
for column in required_numeric_columns:
    edited[column] = pd.to_numeric(edited[column], errors="coerce")
for _col in ["Final Internal Marks", "CIA 1", "CIA 2", "CIA 3 (out of 100)"]:
    edited[_col] = pd.to_numeric(edited[_col], errors="coerce")
edited["Semester Exam Marks"] = pd.to_numeric(edited["Semester Exam Marks"], errors="coerce")

if edited[required_numeric_columns].isna().any().any():
    st.error("Enter valid numbers for credits and CIA marks.")
    st.stop()

if (edited["Credits"] <= 0).any():
    st.error("Credits must be greater than zero.")
    st.stop()

if ((edited["Final Internal Marks"].dropna() < 0) | (edited["Final Internal Marks"].dropna() > internal_max)).any():
    st.error(f"Final Internal Marks must be between 0 and {internal_max}.")
    st.stop()
if ((edited["CIA 3 (out of 100)"].dropna() < 0) | (edited["CIA 3 (out of 100)"].dropna() > 100)).any():
    st.error("CIA 3 must be between 0 and 100.")
    st.stop()
if ((edited["Semester Exam Marks"].dropna() < 0) | (edited["Semester Exam Marks"].dropna() > exam_max)).any():
    st.error(f"Semester Exam Marks must be between 0 and {exam_max} when entered.")
    st.stop()

if (edited["Subject"].astype(str).str.strip() == "").any():
    st.error("Every subject needs a name.")
    st.stop()

# ---------------- CALCULATIONS ----------------

def get_grade(score):
    for grade, cutoff in sorted(
        grade_cutoffs.items(), key=lambda item: item[1], reverse=True
    ):
        if score >= cutoff:
            return grade
    return "U"


def grade_point(score):
    return grade_points[get_grade(score)]


def internal_from_cia(cia_marks):
    """Fallback estimate only; never use this if the portal's final internal is supplied."""
    valid = [float(x) for x in cia_marks if pd.notna(x)]
    if not valid:
        return None
    # Explicitly a provisional estimate, not claimed as the official AU R2023 formula.
    return (sum(valid) / len(valid)) / 100 * internal_max


def final_score(internal_marks, exam_percent):
    """Combine normalized internal/exam percentages by configured weights."""
    total_weight = internal_weight + exam_weight
    if total_weight <= 0 or internal_max <= 0:
        return 0.0
    internal_percent = internal_marks / internal_max * 100
    return (internal_percent * internal_weight + exam_percent * exam_weight) / total_weight


results = []
for _, row in edited.iterrows():
    subject = str(row["Subject"])
    credits = int(row["Credits"])
    final_internal_input = row["Final Internal Marks"]
    has_portal_internal = pd.notna(final_internal_input)
    cia1, cia2 = row["CIA 1"], row["CIA 2"]
    cia3_value = row["CIA 3 (out of 100)"]
    cia3_entered = pd.notna(cia3_value)
    cia3_actual = float(cia3_value) if cia3_entered else None
    actual_exam = row["Semester Exam Marks"]
    exam_entered = pd.notna(actual_exam)

    # The portal's final internal marks always take priority when provided.
    if has_portal_internal:
        current_internal = float(final_internal_input)
        internal_source = "Portal-provided final internal (used directly)"
    else:
        available_components = [x for x in [cia1, cia2] if pd.notna(x)]
        current_internal = internal_from_cia(available_components)
        internal_source = "Provisional estimate — enter all required AU R2023 assessment components for an official calculation"
        if current_internal is None:
            current_internal = 0.0

    current_internal_percent = current_internal / internal_max * 100 if internal_max else 0.0
    total_weight = internal_weight + exam_weight
    if exam_weight > 0 and total_weight > 0:
        required_exam_percent = (desired_final * total_weight - current_internal_percent * internal_weight) / exam_weight
    elif desired_final <= current_internal_percent:
        required_exam_percent = 0.0
    else:
        required_exam_percent = float("inf")

    if required_exam_percent <= 0:
        exam_marks_text, exam_status = f"0/{exam_max}", "Target covered by current internal score"
    elif required_exam_percent <= 100:
        exam_marks_text, exam_status = f"{math.ceil(required_exam_percent / 100 * exam_max)}/{exam_max}", "Achievable under configured weightage"
    else:
        exam_marks_text, exam_status = f"Over {exam_max}", "Target not achievable under configured weightage"

    # CIA 3 is scored out of 100. It is not silently treated as an extra internal component.
    cia3_target = math.ceil(max(0, min(100, desired_final)))
    cia3_note = ("Actual CIA 3 mark entered; use course-specific regulation to map it into internals" if cia3_entered
                 else "CIA 3 target shown out of 100; not added directly to final internal marks")
    exam_percent_used = (float(actual_exam) / exam_max * 100) if exam_entered and exam_max else float(expected_exam)
    final_percent = final_score(current_internal, exam_percent_used)
    status = "Actual exam + supplied internal" if exam_entered and has_portal_internal else ("Projection using supplied internal" if has_portal_internal else "Projection; internal is estimated")
    results.append({
        "Subject": subject, "Credits": credits,
        "Final Internal Marks Provided": round(float(final_internal_input), 2) if has_portal_internal else "Not provided",
        "Current Internal Used": round(current_internal, 2),
        "Internal Data Source": internal_source,
        "CIA 1": cia1 if pd.notna(cia1) else "Not entered",
        "CIA 2": cia2 if pd.notna(cia2) else "Not entered",
        "CIA 3 (out of 100)": cia3_actual if cia3_entered else "Pending",
        "CIA 3 target (out of 100)": cia3_target,
        "CIA 3 note": cia3_note,
        "Semester Exam Marks": float(actual_exam) if exam_entered else "Pending",
        "Exam needed (%)": round(max(0, required_exam_percent), 1) if math.isfinite(required_exam_percent) else ">100%",
        "Exam marks needed": exam_marks_text, "Exam target status": exam_status,
        "Final subject score (%)": round(final_percent, 2),
        "Score type": status, "Estimated grade": get_grade(final_percent), "Grade point": grade_point(final_percent),
    })

result_df = pd.DataFrame(results)

total_credits = int(result_df["Credits"].sum())
if total_credits <= 0:
    st.error("Your total subject credits must be greater than zero.")
    st.stop()

semester_gpa = (result_df["Credits"] * result_df["Grade point"]).sum() / total_credits
if completed_credits + total_credits > 0:
    projected_cgpa = (previous_cgpa * completed_credits + semester_gpa * total_credits) / (completed_credits + total_credits)
else:
    projected_cgpa = semester_gpa

required_semester_gpa = (
    target_cgpa * (completed_credits + total_credits) - previous_cgpa * completed_credits
) / total_credits if total_credits else 0.0

# ---------------- DASHBOARD ----------------

st.header("3. Your Academic Dashboard")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Target CGPA", f"{target_cgpa:.2f}")
m2.metric("Required Semester GPA", f"{required_semester_gpa:.2f}")
m3.metric("Projected Semester GPA", f"{semester_gpa:.2f}")
m4.metric("Projected CGPA", f"{projected_cgpa:.2f}")

if required_semester_gpa > 10:
    st.error("Your target CGPA would require a semester GPA above 10 under the entered credit assumptions. Consider a longer-term target.")
elif projected_cgpa >= target_cgpa:
    st.success("Your current scenario meets your CGPA goal.")
else:
    st.warning("Your current projection is below your target. Review subject-wise CIA 3 and exam targets below.")

st.caption("The dashboard uses your entered credits, assessment rules, grade boundaries and grade points. Results are planning estimates until actual exam marks are entered.")

# ---------------- CIA 3 AND INTERNAL OVERVIEW ----------------

st.header("4. Current Internal & CIA 3 Predictor")
st.info("If the portal provides Final Internal Marks, SemScore AI uses them directly. If missing, enter the applicable assessment components; this version labels a CIA-only fallback as provisional rather than claiming it is the official Anna University R2023 calculation. CIA 3 is out of 100 and is not automatically added to internal marks.")
st.write("Portal-provided Final Internal Marks take priority. If missing, enter applicable assessment components; incomplete component data is clearly labelled as provisional. CIA 3 is out of 100 and is kept separate until the official course-specific conversion is configured.")

chart_col, summary_col = st.columns([1.45, 1])
with chart_col:
    st.markdown("#### CIA marks by subject")
    chart_data = edited.set_index("Subject")[["CIA 1", "CIA 2", "CIA 3 (out of 100)"]].apply(pd.to_numeric, errors="coerce")
    st.bar_chart(chart_data, height=300)
with summary_col:
    st.markdown("#### Your targets")
    st.metric("Target final subject score", f"{desired_final:.0f}%")
    st.metric("Expected semester exam", f"{expected_exam:.0f}%")
    st.metric("Subjects in your plan", f"{len(result_df)}")
    actual_exam_count = int((result_df["Semester Exam Marks"] != "Pending").sum())
    st.metric("Subjects with actual exam marks", f"{actual_exam_count}/{len(result_df)}")
    st.caption("CIA 3 is scored out of 100. Do not treat the raw mark as internal marks without the applicable course conversion rule.")

st.markdown("#### Subject-wise current internal, CIA 3 target and exam plan")
st.dataframe(result_df[[
    "Subject", "Final Internal Marks Provided", "Current Internal Used", "Internal Data Source",
    "CIA 3 (out of 100)", "CIA 3 target (out of 100)", "Exam needed (%)", "Exam marks needed",
    "Final subject score (%)", "Score type", "Estimated grade", "Grade point"
]], use_container_width=True, hide_index=True)

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
    "Prioritize low-scoring subjects and practise both CIA-style and semester-exam questions."
)

# Prioritize subjects with the lowest estimated final score.
ranked_subjects = result_df.sort_values(
    "Final subject score (%)",
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

