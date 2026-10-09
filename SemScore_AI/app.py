
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
.stApp {
    background: #0b1120;
    color: #f1f5f9;
}
[data-testid="stSidebar"] {
    background: #111b2e;
}
div[data-testid="stMetric"] {
    background: #162238;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #263752;
}
h1, h2, h3 {
    color: #60a5fa;
}
</style>
""", unsafe_allow_html=True)

st.title("SemScore AI")
st.caption("Your personal academic improvement planner")
st.write("Plan CIA 3. Prepare for semester exams. Work toward your CGPA goal.")

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

# ---------------- SUBJECT PLAN ----------------

st.header("4. Subject-wise Recovery Plan")

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

st.header("5. Your Daily Study Timetable")

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

st.header("6. Weekly Checklist")

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

st.header("7. CGPA Scenario Planner")

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
