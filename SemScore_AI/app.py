import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SemScore AI", page_icon="🎓", layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--bg:#070b14;--border:rgba(148,163,184,.16);--blue:#60a5fa;--cyan:#67e8f9;--text:#e8eef9;--muted:#94a3b8}
.stApp{background:radial-gradient(ellipse at 12% 0%,rgba(37,99,235,.16),transparent 34%),radial-gradient(ellipse at 90% 10%,rgba(124,58,237,.12),transparent 30%),var(--bg);color:var(--text);font-family:'DM Sans',sans-serif}
[data-testid="stHeader"]{background:rgba(7,11,20,.72)} .block-container{max-width:1440px;padding-top:1.5rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0e1728 0%,#0a1020 100%);border-right:1px solid var(--border)}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.035em} h1{color:#f8fafc!important} h2{color:#e8eef9!important} h3{color:#cbd5e1!important}
p,label,.stMarkdown{color:var(--text)} [data-testid="stMetric"]{background:linear-gradient(145deg,rgba(20,33,56,.96),rgba(13,22,39,.96));border:1px solid var(--border);border-radius:16px;padding:16px}
[data-testid="stMetricLabel"]{color:#a9b8ce!important}[data-testid="stMetricValue"]{color:var(--blue)!important;font-family:'Space Grotesk',sans-serif}
div.stButton>button,div.stDownloadButton>button{background:linear-gradient(100deg,#2563eb,#4f46e5);color:white;border:1px solid rgba(147,197,253,.22);border-radius:10px;font-weight:700}
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div{background:#0e192b;border-color:#2a3b56;border-radius:9px}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid var(--border);border-radius:12px;overflow:hidden} hr{border-color:var(--border)!important}
[data-testid="stProgressBar"]>div>div{background:linear-gradient(90deg,#3b82f6,#22d3ee)} small,.stCaption,[data-testid="stCaptionContainer"]{color:var(--muted)!important}
@media(max-width:768px){.block-container{padding:1rem .8rem 2rem}}
</style>
<div style="padding:1.3rem 1.5rem;margin:.2rem 0 1.25rem;border:1px solid rgba(96,165,250,.24);border-radius:20px;background:linear-gradient(115deg,rgba(20,38,69,.92),rgba(17,24,48,.82) 60%,rgba(49,29,83,.55));">
<div style="font-size:.76rem;font-weight:700;letter-spacing:.16em;color:#67e8f9;text-transform:uppercase">Academic intelligence platform</div>
<div style="font-family:'Space Grotesk',sans-serif;font-size:clamp(2rem,4vw,3rem);font-weight:700;letter-spacing:-.045em;color:#f8fafc;margin-top:.3rem">SemScore <span style="color:#60a5fa">AI</span></div>
<div style="font-size:1rem;color:#b6c5da;margin-top:.25rem">Understand your marks, calculate realistic targets, and build a focused recovery plan.</div>
<div style="display:flex;flex-wrap:wrap;gap:.5rem;margin-top:1rem"><span style="padding:.35rem .7rem;border-radius:999px;background:rgba(96,165,250,.12);color:#bfdbfe;font-size:.8rem">CIA Recovery</span><span style="padding:.35rem .7rem;border-radius:999px;background:rgba(103,232,249,.08);color:#a5f3fc;font-size:.8rem">CGPA Planning</span><span style="padding:.35rem .7rem;border-radius:999px;background:rgba(167,139,250,.09);color:#ddd6fe;font-size:.8rem">Personal Study Plan</span></div>
</div>
""", unsafe_allow_html=True)

# ---------------- SETTINGS ----------------
st.sidebar.title("Academic Settings")
target_cgpa = st.sidebar.number_input("Target CGPA", 0.0, 10.0, 8.5, 0.1)
cia_max = st.sidebar.number_input("Maximum marks per CIA", 1, 200, 50)
internal_max = st.sidebar.number_input("Maximum internal marks", 1, 100, 40)
exam_max = st.sidebar.number_input("Maximum semester exam marks", 1, 300, 100)
internal_weight = st.sidebar.number_input("Internal contribution (%)", 0, 100, 40)
exam_weight = st.sidebar.number_input("Semester exam contribution (%)", 0, 100, 60)
if internal_weight + exam_weight == 0:
    st.sidebar.error("Internal and exam contributions cannot both be zero.")
    st.stop()
if internal_weight + exam_weight != 100:
    st.sidebar.warning("Weights do not add to 100. Calculations normalize by their combined total.")

cia_method = st.sidebar.selectbox(
    "CIA aggregation assumption",
    ["Average of all 3 CIAs", "Best 2 of 3 CIAs"],
    help="Use only if it matches your course rules. Otherwise enter the official Final Internal Marks for each subject."
)
st.sidebar.caption("The CIA aggregation choices are configurable assumptions, not a claim about KRCE regulations. Confirm the official method with your course faculty.")

st.sidebar.subheader("Grade boundaries (%)")
grade_cutoffs = {
    "O": st.sidebar.number_input("O grade minimum", 0, 100, 90),
    "A+": st.sidebar.number_input("A+ grade minimum", 0, 100, 80),
    "A": st.sidebar.number_input("A grade minimum", 0, 100, 70),
    "B+": st.sidebar.number_input("B+ grade minimum", 0, 100, 60),
    "B": st.sidebar.number_input("B grade minimum", 0, 100, 50),
    "C": st.sidebar.number_input("C grade minimum", 0, 100, 40),
}
if len(set(grade_cutoffs.values())) != len(grade_cutoffs):
    st.sidebar.warning("Some grade cutoffs are equal. Check your college's grade scale.")

st.sidebar.subheader("Grade points")
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
previous_cgpa = st.sidebar.number_input("Current CGPA", 0.0, 10.0, 7.54, 0.01)
completed_credits = st.sidebar.number_input("Credits completed before this semester", 0, 300, 20)

# ---------------- GOALS ----------------
st.header("1. Your Study Goals")
c1, c2, c3 = st.columns(3)
with c1:
    study_hours = st.number_input("Daily study hours", 1.0, 12.0, 3.5, 0.5)
with c2:
    expected_exam = st.slider("Expected semester exam score (%)", 0, 100, 75)
with c3:
    desired_final = st.slider("Target final subject score (%)", 0, 100, 80)

st.info("Enter actual marks where available. Missing marks are treated as pending, not silently counted as earned marks. Projections depend on your configured assessment and grade rules.")

# ---------------- DATA INPUT ----------------
st.header("2. Feed Your Academic Data")
st.caption("Add each subject, its credits, CIA marks and/or the official final internal mark. Portal-provided final internal marks take priority.")
columns = ["Subject", "Credits", "CIA 1", "CIA 2", "CIA 3 (out of CIA max)", "Final Internal Marks", "Semester Exam Marks"]
if "subjects" not in st.session_state:
    st.session_state.subjects = pd.DataFrame(columns=columns)
else:
    old = st.session_state.subjects.copy()
    rename_map = {"CIA 3 (out of 100)": "CIA 3 (out of CIA max)"}
    old = old.rename(columns=rename_map)
    for col in columns:
        if col not in old:
            old[col] = None
    st.session_state.subjects = old[columns]

sample = pd.DataFrame({"Subject": ["Example subject"], "Credits": [3], "CIA 1": [30], "CIA 2": [30], "CIA 3 (out of CIA max)": [None], "Final Internal Marks": [None], "Semester Exam Marks": [None]})
st.download_button("Download subject template (CSV)", sample.to_csv(index=False).encode("utf-8"), "SemScore_subject_template.csv", "text/csv")
upload = st.file_uploader("Upload subject data (CSV)", type=["csv"], key="subject_csv_upload")
if upload is not None and st.button("Import uploaded subject data"):
    try:
        incoming = pd.read_csv(upload).rename(columns={"CIA 3 (out of 100)": "CIA 3 (out of CIA max)"})
        if not {"Subject", "Credits"}.issubset(incoming.columns):
            st.error("CSV must contain Subject and Credits columns.")
        elif incoming.empty:
            st.error("The CSV contains no subject rows.")
        else:
            for col in columns:
                if col not in incoming:
                    incoming[col] = None
            st.session_state.subjects = incoming[columns].copy()
            st.success(f"Imported {len(incoming)} subject(s). Review the rows below.")
            st.rerun()
    except Exception as exc:
        st.error(f"Could not import CSV: {exc}")

edited = st.data_editor(
    st.session_state.subjects, num_rows="dynamic", use_container_width=True, key="subject_editor",
    column_config={
        "Subject": st.column_config.TextColumn("Subject name", required=True),
        "Credits": st.column_config.NumberColumn("Credits", min_value=1, max_value=30, step=1, required=True),
        "CIA 1": st.column_config.NumberColumn(f"CIA 1 / {cia_max}", min_value=0, max_value=cia_max, step=0.5),
        "CIA 2": st.column_config.NumberColumn(f"CIA 2 / {cia_max}", min_value=0, max_value=cia_max, step=0.5),
        "CIA 3 (out of CIA max)": st.column_config.NumberColumn(f"CIA 3 / {cia_max}", min_value=0, max_value=cia_max, step=0.5),
        "Final Internal Marks": st.column_config.NumberColumn(f"Official final internal / {internal_max}", min_value=0, max_value=internal_max, step=0.01),
        "Semester Exam Marks": st.column_config.NumberColumn(f"Semester exam / {exam_max}", min_value=0, max_value=exam_max, step=0.5),
    },
)
st.session_state.subjects = edited.copy()
if edited.empty:
    st.warning("Add at least one subject to see your dashboard and study plan.")
    st.stop()

# ---------------- VALIDATION ----------------
work = edited.copy()
work["Subject"] = work["Subject"].fillna("").astype(str).str.strip()
for col in columns[1:]:
    work[col] = pd.to_numeric(work[col], errors="coerce")
if (work["Subject"] == "").any():
    st.error("Every subject needs a name.")
    st.stop()
if work["Subject"].duplicated().any():
    st.warning("Some subject names are duplicated. Check whether these are separate courses.")
if work["Credits"].isna().any() or (work["Credits"] <= 0).any():
    st.error("Enter a valid positive credit value for every subject.")
    st.stop()
for col, maxval in [("CIA 1", cia_max), ("CIA 2", cia_max), ("CIA 3 (out of CIA max)", cia_max), ("Final Internal Marks", internal_max), ("Semester Exam Marks", exam_max)]:
    invalid = work[col].notna() & ((work[col] < 0) | (work[col] > maxval))
    if invalid.any():
        st.error(f"{col} values must be between 0 and {maxval}.")
        st.stop()

# ---------------- CALCULATION HELPERS ----------------
def get_grade(score):
    for grade, cutoff in sorted(grade_cutoffs.items(), key=lambda item: item[1], reverse=True):
        if score >= cutoff:
            return grade
    return "U"

def grade_point(score):
    return grade_points[get_grade(score)]

def internal_percent_from_cias(cia_values):
    """Return normalized CIA percentage under the selected, explicitly assumed rule."""
    valid = [float(x) for x in cia_values if pd.notna(x)]
    if not valid:
        return None
    normalized = [max(0.0, min(100.0, x / cia_max * 100)) for x in valid]
    if cia_method == "Best 2 of 3 CIAs":
        if len(normalized) >= 2:
            normalized = sorted(normalized, reverse=True)[:2]
        # With only one entered CIA, this is a provisional partial estimate.
    return sum(normalized) / len(normalized)

def required_cia3_raw(cia1, cia2, target_internal_percent):
    """Solve for CIA 3 under the selected assumption; returns raw marks on CIA scale."""
    a = float(cia1) if pd.notna(cia1) else None
    b = float(cia2) if pd.notna(cia2) else None
    target = max(0.0, min(100.0, target_internal_percent))
    if cia_method == "Average of all 3 CIAs":
        if a is None or b is None:
            return None, "Enter CIA 1 and CIA 2 to calculate a CIA 3 target."
        required_percent = 3 * target - (a / cia_max * 100) - (b / cia_max * 100)
    else:
        if a is None or b is None:
            return None, "Enter CIA 1 and CIA 2 to calculate a CIA 3 target."
        # Best-two average: the two highest of CIA1, CIA2, CIA3 must average to target.
        # If current two already meet target, a zero CIA3 is sufficient to maintain best-two average.
        a_pct, b_pct = a / cia_max * 100, b / cia_max * 100
        if (a_pct + b_pct) / 2 >= target:
            required_percent = 0.0
        else:
            # CIA3 must be high enough to pair with the better existing CIA.
            required_percent = 2 * target - max(a_pct, b_pct)
    raw = required_percent / 100 * cia_max
    if raw <= 0:
        return 0.0, "Target already covered by the entered CIAs under this assumption."
    if raw > cia_max:
        return None, f"Target is not reachable with CIA 3 alone; it would require {raw:.1f}/{cia_max}."
    return math.ceil(raw), "Calculated from entered CIA 1/2 and selected CIA rule; verify the rule with faculty."

def combine_final(internal_marks, exam_marks):
    total_weight = internal_weight + exam_weight
    internal_pct = internal_marks / internal_max * 100 if internal_max else 0.0
    exam_pct = exam_marks / exam_max * 100 if exam_marks is not None and exam_max else expected_exam
    return (internal_pct * internal_weight + exam_pct * exam_weight) / total_weight

# ---------------- BUILD RESULTS ----------------
rows = []
for _, row in work.iterrows():
    subject = row["Subject"]
    credits = int(row["Credits"])
    cia1, cia2, cia3 = row["CIA 1"], row["CIA 2"], row["CIA 3 (out of CIA max)"]
    portal_internal = row["Final Internal Marks"]
    exam_marks = row["Semester Exam Marks"]
    portal_internal_entered = pd.notna(portal_internal)
    exam_entered = pd.notna(exam_marks)

    cia_values = [cia1, cia2, cia3]
    cia_percent = internal_percent_from_cias(cia_values)
    if portal_internal_entered:
        current_internal = float(portal_internal)
        internal_source = "Official final internal entered"
        current_internal_pct = current_internal / internal_max * 100
    elif cia_percent is not None:
        current_internal_pct = cia_percent
        current_internal = current_internal_pct / 100 * internal_max
        entered_count = sum(pd.notna(x) for x in cia_values)
        internal_source = f"Provisional CIA estimate ({entered_count}/3 CIAs entered; {cia_method})"
    else:
        current_internal = None
        current_internal_pct = None
        internal_source = "Pending — enter CIA marks or official final internal"

    # Calculate required internal percentage to reach target, assuming expected exam mark.
    total_weight = internal_weight + exam_weight
    expected_exam_pct = float(expected_exam)
    if internal_weight > 0:
        required_internal_pct = (desired_final * total_weight - expected_exam_pct * exam_weight) / internal_weight
    else:
        required_internal_pct = 0.0 if desired_final <= expected_exam_pct else float("inf")

    # Required exam marks based on current internal score.
    if current_internal is None:
        required_exam_pct = None
        exam_needed = "Enter internal/CIA marks"
        exam_status = "Pending input"
        projected_final = (0 * internal_weight + expected_exam_pct * exam_weight) / total_weight
    else:
        if exam_weight > 0:
            req_exam_pct = (desired_final * total_weight - current_internal_pct * internal_weight) / exam_weight
        else:
            req_exam_pct = 0.0 if current_internal_pct >= desired_final else float("inf")
        if req_exam_pct <= 0:
            exam_needed, exam_status = f"0/{exam_max}", "Current internal covers target"
        elif req_exam_pct <= 100:
            exam_needed, exam_status = f"{math.ceil(req_exam_pct / 100 * exam_max)}/{exam_max}", "Achievable under configured weights"
        else:
            exam_needed, exam_status = f"More than {exam_max}", "Target not achievable with current internal"
        required_exam_pct = round(req_exam_pct, 1) if math.isfinite(req_exam_pct) else ">100%"
        projected_final = combine_final(current_internal, float(exam_marks) if exam_entered else None)

    if current_internal is None:
        cia_target, cia_note = required_cia3_raw(cia1, cia2, required_internal_pct) if math.isfinite(required_internal_pct) else (None, "Target cannot be calculated with these weights.")
    else:
        # If official internal is supplied, CIA target is still a separate planning estimate only.
        cia_target, cia_note = required_cia3_raw(cia1, cia2, required_internal_pct) if math.isfinite(required_internal_pct) else (None, "Target cannot be calculated with these weights.")

    grade = get_grade(projected_final)
    rows.append({
        "Subject": subject,
        "Credits": credits,
        "CIA 1": cia1 if pd.notna(cia1) else "Pending",
        "CIA 2": cia2 if pd.notna(cia2) else "Pending",
        "CIA 3 actual": cia3 if pd.notna(cia3) else "Pending",
        "CIA 3 target": f"{cia_target}/{cia_max}" if cia_target is not None else "Not calculable",
        "CIA 3 target note": cia_note,
        "Final Internal Marks": round(float(portal_internal), 2) if portal_internal_entered else "Not entered",
        "Current Internal Used": round(current_internal, 2) if current_internal is not None else "Pending",
        "Internal Data Source": internal_source,
        "Exam marks needed": exam_needed,
        "Exam target status": exam_status,
        "Semester Exam Marks": float(exam_marks) if exam_entered else "Pending",
        "Projected Final Score (%)": round(projected_final, 2),
        "Score Type": "Actual exam + official internal" if exam_entered and portal_internal_entered else ("Projection using official internal" if portal_internal_entered else "Projection; CIA estimate or pending input"),
        "Estimated Grade": grade,
        "Grade Point": grade_point(projected_final),
    })

result_df = pd.DataFrame(rows)
credits_total = int(result_df["Credits"].sum())
semester_gpa = float((result_df["Credits"] * result_df["Grade Point"]).sum() / credits_total)
total_future_credits = completed_credits + credits_total
projected_cgpa = ((previous_cgpa * completed_credits + semester_gpa * credits_total) / total_future_credits) if total_future_credits else semester_gpa
required_semester_gpa = ((target_cgpa * total_future_credits - previous_cgpa * completed_credits) / credits_total) if credits_total else 0.0

# ---------------- DASHBOARD ----------------
st.header("3. Your Academic Dashboard")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Target CGPA", f"{target_cgpa:.2f}")
m2.metric("Required Semester GPA", f"{required_semester_gpa:.2f}")
m3.metric("Projected Semester GPA", f"{semester_gpa:.2f}")
m4.metric("Projected CGPA", f"{projected_cgpa:.2f}")
if required_semester_gpa > 10:
    st.error("Your target CGPA requires a semester GPA above 10 with the entered credit assumptions. Consider a longer-term target.")
elif required_semester_gpa < 0:
    st.success("Your existing CGPA already exceeds the target under these credit assumptions.")
elif projected_cgpa >= target_cgpa:
    st.success("Your current projection meets the target. This is an estimate, not an official result.")
else:
    st.warning("Your current projection is below the target. Review subject recovery and exam targets below.")
st.caption("CGPA projections use entered credits, grade cutoffs and grade points. Actual institutional results may differ.")

st.header("4. CIA Analysis & Target Predictor")
if cia_method == "Average of all 3 CIAs":
    st.caption("CIA target assumes all three CIAs contribute equally to the CIA average.")
else:
    st.caption("CIA target assumes the best two of three CIAs are averaged. Confirm this matches your official rule.")
chart_data = work.set_index("Subject")[["CIA 1", "CIA 2", "CIA 3 (out of CIA max)"]].apply(pd.to_numeric, errors="coerce")
chart_data = chart_data.rename(columns={"CIA 3 (out of CIA max)": "CIA 3"})
left, right = st.columns([1.5, 1])
with left:
    st.markdown("#### CIA marks by subject")
    st.bar_chart(chart_data, height=300)
with right:
    st.markdown("#### Study targets")
    st.metric("Target final subject score", f"{desired_final}%")
    st.metric("Expected semester exam score", f"{expected_exam}%")
    st.metric("Subjects in plan", len(result_df))
    st.metric("Daily study time", f"{study_hours:.1f} hours")

st.markdown("#### Subject-wise recovery details")
st.dataframe(result_df[["Subject", "CIA 1", "CIA 2", "CIA 3 actual", "CIA 3 target", "CIA 3 target note", "Current Internal Used", "Internal Data Source", "Exam marks needed", "Exam target status", "Projected Final Score (%)", "Estimated Grade"]], use_container_width=True, hide_index=True)
st.download_button("Download subject recovery plan (CSV)", result_df.to_csv(index=False).encode("utf-8"), "SemScore_subject_recovery_plan.csv", "text/csv")

# ---------------- PRIORITY PLAN ----------------
st.header("5. Subject-wise Recovery Plan")
priority_df = result_df.copy()
priority_df["Priority score"] = pd.to_numeric(priority_df["Projected Final Score (%)"], errors="coerce").fillna(0)
priority_df = priority_df.sort_values("Priority score", ascending=True)
for i, row in priority_df.iterrows():
    score = float(row["Priority score"])
    with st.container(border=True):
        a, b = st.columns([3, 1])
        a.markdown(f"**{row['Subject']}**")
        a.caption(f"Priority based on projected score: {score:.1f}%")
        b.metric("Priority", "High" if score < 50 else ("Medium" if score < 70 else "Maintain"))
        if score < 50:
            st.write("Action: review core concepts, solve guided examples, then attempt questions without notes.")
        elif score < 70:
            st.write("Action: revise weak topics and complete timed practice questions. Review each mistake after practice.")
        else:
            st.write("Action: maintain performance with spaced revision and one timed practice set.")

# ---------------- STUDY TIMETABLE ----------------
st.header("6. Your Daily Study Timetable")
st.write(f"This timetable uses **{study_hours:.1f} hours per day** and gives earlier slots to the lowest projected subjects.")
ranked = priority_df["Subject"].tolist()
slots = [
    ("Session 1", 0.35, "Learn concepts and review class notes"),
    ("Session 2", 0.30, "Solve problems and important questions"),
    ("Session 3", 0.25, "Write CIA/semester-exam answers from memory"),
    ("Quick review", 0.10, "Recall formulas and record mistakes"),
]
schedule = []
for idx, (session, fraction, task) in enumerate(slots):
    duration = round(study_hours * fraction, 2)
    schedule.append({"Session": session, "Duration (hours)": duration, "Priority subject": ranked[idx % len(ranked)], "Task": task})
schedule_df = pd.DataFrame(schedule)
st.dataframe(schedule_df, use_container_width=True, hide_index=True)
st.download_button("Download daily study timetable (CSV)", schedule_df.to_csv(index=False).encode("utf-8"), "SemScore_daily_study_timetable.csv", "text/csv")

# ---------------- WEEKLY CHECKLIST ----------------
st.header("7. Weekly Checklist")
checklist = ["Review CIA 1 and CIA 2 mistakes for each subject", "Finish one difficult topic in the highest-priority subject", "Practice important problems without viewing solutions", "Write at least one exam-style answer per theory subject", "Revise formulas, definitions and key diagrams", "Take a timed self-test and record the score", "Update CIA 3 targets after each practice test"]
for item in checklist:
    st.checkbox(item, key="check_" + item)

# ---------------- SCENARIOS ----------------
st.header("8. CGPA Scenario Planner")
st.caption("Scenario estimates use the same current CGPA and credit assumptions as the dashboard.")
scenario_rows = []
for gpa in [6.0, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]:
    cgpa = (previous_cgpa * completed_credits + gpa * credits_total) / total_future_credits if total_future_credits else gpa
    scenario_rows.append({"Semester GPA scenario": gpa, "Projected CGPA": round(cgpa, 2), "Meets target": "Yes" if cgpa >= target_cgpa else "No"})
scenario_df = pd.DataFrame(scenario_rows)
st.dataframe(scenario_df, use_container_width=True, hide_index=True)
st.download_button("Download CGPA scenarios (CSV)", scenario_df.to_csv(index=False).encode("utf-8"), "SemScore_CGPA_scenarios.csv", "text/csv")

st.divider()
st.caption("SemScore AI is a planning prototype. CIA conversion, grade boundaries, grade points, credit rules and assessment weightings must be confirmed against KRCE's official autonomous regulations. Rule-based suggestions are not a trained AI prediction and cannot guarantee grades.")
