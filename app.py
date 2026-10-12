"""
app.py — Smart Campus Analytics: Student Success Platform
Run:  streamlit run app.py
"""

import ast, subprocess, sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Smart Campus Analytics", layout="wide")

# Generate the synthetic dataset on first run. Anchor paths to this file so
# startup works even when the process working directory differs.
APP_DIR = Path(__file__).resolve().parent
DATA_PATH = APP_DIR / "student_master.csv"
if not DATA_PATH.exists():
    subprocess.run([sys.executable, str(APP_DIR / "generate_data.py")], cwd=APP_DIR, check=True)

df = pd.read_csv(DATA_PATH, converters={
    "risk_flags": ast.literal_eval,
    "top_strengths": ast.literal_eval,
    "top_gaps": ast.literal_eval,
})

PILLARS = ["academic", "attendance", "lms_engagement", "cocurricular", "placement_readiness", "skills", "feedback"]
PILLAR_LABELS = ["Academic", "Attendance", "LMS engagement", "Co-curricular", "Placement readiness", "Skills", "Feedback"]
RISK_COLORS = {"Critical": "#d62728", "High": "#ff7f0e", "Medium": "#bcbd22", "Low": "#2ca02c"}

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")
depts = st.sidebar.multiselect("Department", sorted(df.department.unique()), default=sorted(df.department.unique()))
years = st.sidebar.multiselect("Year", sorted(df.year.unique()), default=sorted(df.year.unique()))
risks = st.sidebar.multiselect("Risk level", ["Critical", "High", "Medium", "Low"], default=["Critical", "High", "Medium", "Low"])
search = st.sidebar.text_input("Search student ID (e.g. STU1042)")

view = df[df.department.isin(depts) & df.year.isin(years) & df.risk_level.isin(risks)]
if search:
    st.session_state["lookup"] = search.strip().upper()

st.title("Smart Campus Analytics — Student Success Platform")
st.caption("Unified view of academic, attendance, LMS, engagement, placement, skills and feedback data")

if view.empty:
    st.warning("No students match these filters. Select at least one department, year, and risk level.")
    st.stop()

# ---------------- Tabs ----------------
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "At-risk watchlist", "Segments", "Student 360°"])

# ============ TAB 1: Overview ============
with tab1:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Students", len(view))
    c2.metric("Avg success score", round(view.success_score.mean(), 1))
    c3.metric("Critical risk", int((view.risk_level == "Critical").sum()))
    c4.metric("High + Critical", int(view.risk_level.isin(["High", "Critical"]).sum()))
    c5.metric("High academics / low placement", int(view.hi_acad_low_place.sum()))

    colL, colR = st.columns(2)
    with colL:
        fig = px.histogram(view, x="success_score", nbins=25, color="risk_level",
                           color_discrete_map=RISK_COLORS, title="Success score distribution")
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)
    with colR:
        rc = view.risk_level.value_counts().reindex(["Critical", "High", "Medium", "Low"]).fillna(0)
        fig = px.pie(names=rc.index, values=rc.values, color=rc.index,
                     color_discrete_map=RISK_COLORS, title="Risk levels", hole=0.45)
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)

    colL, colR = st.columns(2)
    with colL:
        pm = view[[f"pillar_{p}" for p in PILLARS]].mean().round(1)
        fig = px.bar(x=PILLAR_LABELS, y=pm.values, title="Average pillar scores (0–100)",
                     labels={"x": "", "y": "Score"}, color=pm.values, color_continuous_scale="Blues")
        fig.update_layout(height=320, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with colR:
        dept = view.groupby("department").agg(score=("success_score", "mean"),
                                              critical=("risk_level", lambda s: (s == "Critical").mean() * 100)).reset_index()
        fig = px.bar(dept, x="department", y="score", title="Avg success score by department",
                     labels={"score": "Score", "department": ""})
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)

# ============ TAB 2: At-risk watchlist ============
with tab2:
    st.subheader("Prioritized intervention list")
    flagged = view[view.n_risks > 0].copy()
    sev = {"Critical": 3, "High": 2, "Medium": 1}
    flagged["severity"] = flagged.risk_level.map(sev)
    flagged = flagged.sort_values(["severity", "success_score"], ascending=[False, True])

    cols = ["student_id", "department", "year", "success_score", "risk_level", "risk_flags", "top_gaps"]
    st.dataframe(flagged[cols].head(200), use_container_width=True, hide_index=True,
                 column_config={"top_gaps": st.column_config.ListColumn("Top contributing gaps")})
    st.caption(f"{len(flagged)} students flagged under current filters. Sorted by severity, then lowest score.")
    st.download_button("Download watchlist (CSV)", flagged[cols].to_csv(index=False),
                       "at_risk_watchlist.csv", "text/csv")

# ============ TAB 3: Segments ============
with tab3:
    st.subheader("Student segments (K-Means on pillar scores)")
    seg = view.groupby("segment_short").agg(
        students=("student_id", "count"),
        avg_score=("success_score", "mean"),
        academic=("pillar_academic", "mean"),
        placement=("pillar_placement_readiness", "mean"),
        attendance=("pillar_attendance", "mean"),
        engagement=("pillar_lms_engagement", "mean"),
    ).round(1).sort_values("avg_score")
    st.dataframe(seg, use_container_width=True)

    INTERVENTIONS = {
        "Struggling": "Structured remedial classes, mentor pairing, attendance counselling, foundation skill workshops.",
        "Disengaged": "Re-engagement campaigns, advisor check-ins, make the LMS content more interactive, club outreach.",
        "Placement-unready": "Mandatory aptitude/coding bootcamp, mock interview schedule, resume and soft-skills workshops.",
        "Placement-focused": "Encourage co-curricular participation and leadership roles; leverage them as peer mentors.",
        "All-round": "Fast-track to leadership, research projects, and higher-studies or premium placement tracks.",
    }
    for seg_name, action in INTERVENTIONS.items():
        if seg_name in seg.index:
            st.markdown(f"**{seg_name}** ({int(seg.loc[seg_name, 'students'])} students) — {action}")

    colL, colR = st.columns(2)
    with colL:
        fig = px.bar(seg.reset_index(), x="segment_short", y="students",
                     title="Segment sizes", labels={"segment_short": "", "students": "Students"})
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)
    with colR:
        sel = st.selectbox("Radar profile", seg.index, key="radar_sel")
        row = seg.loc[sel]
        fig = go.Figure(go.Scatterpolar(
            r=[row.academic, row.attendance, row.engagement, row.placement, row.avg_score],
            theta=["Academic", "Attendance", "Engagement", "Placement", "Overall score"],
            fill="toself"))
        fig.update_layout(height=320, title=f"Profile: {sel}")
        st.plotly_chart(fig, use_container_width=True)

    st.info(f"Bonus segment — high academic performance but low placement readiness: "
            f"**{int(view.hi_acad_low_place.sum())} students**. Target them with placement bootcamps before recruitment season.")

# ============ TAB 4: Student 360° ============
with tab4:
    st.subheader("Explainable student profile")
    sid = st.text_input("Enter student ID", value=st.session_state.get("lookup", "STU1042")).strip().upper()
    match = df[df.student_id == sid]
    if match.empty:
        st.warning("Student not found. Try e.g. STU1042.")
    else:
        r = match.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Success score", f"{r.success_score:.0f} / 100")
        c2.metric("Risk level", r.risk_level)
        c3.metric("CGPA", f"{r.cgpa:.2f}")
        c4.metric("Attendance", f"{r.attendance_pct:.0f}%")

        colL, colR = st.columns(2)
        with colL:
            fig = go.Figure(go.Indicator(mode="gauge+number", value=r.success_score,
                gauge={"axis": {"range": [0, 100]},
                       "bar": {"color": RISK_COLORS[r.risk_level]},
                       "steps": [{"range": [0, 40], "color": "#f0d5d5"},
                                 {"range": [40, 60], "color": "#f5ecd0"},
                                 {"range": [60, 100], "color": "#d5e8d4"}]}))
            fig.update_layout(height=260, title="Success score")
            st.plotly_chart(fig, use_container_width=True)
        with colR:
            vals = [r[f"pillar_{p}"] for p in PILLARS]
            fig = px.bar(x=PILLAR_LABELS, y=vals, title="Pillar scores",
                         labels={"x": "", "y": "0–100"}, color=vals, color_continuous_scale="Blues")
            fig.update_layout(height=260, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Top contributing gaps (drag the score down)**")
            for g in r.top_gaps:
                st.markdown(f"- {g}")
            if r.risk_flags:
                st.markdown("**Risk flags**")
                for f_ in r.risk_flags:
                    st.markdown(f"- {f_}")
        with c2:
            st.markdown("**Top strengths (holding the score up)**")
            for s in r.top_strengths:
                st.markdown(f"- {s}")
            st.markdown(f"**Segment:** {r.segment_name}")

        st.markdown("**Suggested actions**")
        suggestions = []
        if "Academic Risk" in r.risk_flags: suggestions.append("Remedial classes and subject mentoring")
        if "Attendance Risk" in r.risk_flags: suggestions.append("Attendance counselling with class advisor")
        if "Disengagement Risk" in r.risk_flags: suggestions.append("Re-engagement: advisor check-in and LMS nudges")
        if "Placement Risk" in r.risk_flags: suggestions.append("Aptitude/coding bootcamp + mock interviews")
        if "Skill Gap" in r.risk_flags: suggestions.append("Targeted technical/soft-skill workshops")
        if not suggestions: suggestions.append("Maintain trajectory; consider advanced or leadership opportunities")
        for s in suggestions:
            st.markdown(f"- {s}")
