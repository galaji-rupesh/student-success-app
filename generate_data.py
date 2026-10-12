"""
generate_data.py — Smart Campus Analytics
Generates a synthetic multi-source student dataset, computes the Student Success
Score, risk flags, and K-Means segments, then writes student_master.csv.

Run once before starting the dashboard:
    python generate_data.py
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

rng = np.random.default_rng(42)
N = 800

# Latent student traits drive correlated outcomes across data sources
ability = rng.normal(0, 1, N)                      # drives academics, attendance, skills
motivation = 0.6 * ability + rng.normal(0, 0.8, N) # drives engagement, LMS activity
prep = 0.5 * ability + rng.normal(0, 0.9, N)       # drives placement readiness

def clip(x, lo, hi):
    return np.clip(x, lo, hi)

# ---------------- Academic ----------------
cgpa = clip(5.5 + 1.6 * ability + rng.normal(0, 0.5, N), 4.0, 10.0).round(2)
backlogs = np.maximum(0, np.round(rng.poisson(np.clip(1.6 - 0.9 * ability, 0.05, 4), N))).astype(int)
sub_perf = clip(cgpa + rng.normal(0, 0.6, N), 3.0, 10.0)

# ---------------- Attendance ----------------
attendance = clip(68 + 12 * ability + rng.normal(0, 9, N), 30, 100).round(1)
subj_att = clip(attendance + rng.normal(0, 6, N), 25, 100).round(1)

# ---------------- LMS ----------------
lms_logins = np.round(clip(28 + 10 * motivation + rng.normal(0, 10, N), 0, 70)).astype(int)
assign_completion = clip(60 + 18 * motivation + rng.normal(0, 12, N), 5, 100).round(1)

# ---------------- Engagement ----------------
events = np.round(np.clip(3 + 2.4 * motivation + rng.normal(0, 2.5, N), 0, 25)).astype(int)
clubs = rng.integers(0, 4, N)
hackathons = np.round(np.clip(0.8 + 1.2 * motivation + rng.normal(0, 1.2, N), 0, 10)).astype(int)
certs = np.round(np.clip(1 + 1.3 * motivation + rng.normal(0, 1.3, N), 0, 12)).astype(int)

# ---------------- Placement ----------------
aptitude = clip(50 + 20 * prep + rng.normal(0, 12, N), 10, 100).round(1)
coding = clip(45 + 25 * prep + rng.normal(0, 15, N), 0, 100).round(1)
mock_interviews = np.round(clip(2 + 3 * prep + rng.normal(0, 2.5, N), 0, 15)).astype(int)

# ---------------- Skills ----------------
tech_skills = clip(50 + 18 * ability + rng.normal(0, 14, N), 5, 100).round(1)
soft_skills = clip(55 + 12 * motivation + rng.normal(0, 15, N), 5, 100).round(1)

# ---------------- Feedback ----------------
satisfaction = clip(3.2 + 0.55 * motivation + rng.normal(0, 0.6, N), 1, 5).round(1)
faculty_feedback = clip(3.0 + 0.5 * ability + rng.normal(0, 0.7, N), 1, 5).round(1)

df = pd.DataFrame({
    "student_id": [f"STU{1000 + i}" for i in range(N)],
    "name": [f"Student {i + 1}" for i in range(N)],
    "department": rng.choice(["CSE", "ECE", "ME", "CE", "IT"], N, p=[.34, .22, .16, .12, .16]),
    "year": rng.choice([2, 3, 4], N, p=[.3, .35, .35]),
    "cgpa": cgpa, "backlogs": backlogs, "avg_subject_marks": sub_perf.round(1),
    "attendance_pct": attendance, "subject_attendance_pct": subj_att,
    "lms_logins_30d": lms_logins, "assignment_completion_pct": assign_completion,
    "events_participated": events, "clubs_joined": clubs,
    "hackathons": hackathons, "certifications": certs,
    "aptitude_score": aptitude, "coding_score": coding, "mock_interviews": mock_interviews,
    "tech_skills_score": tech_skills, "soft_skills_score": soft_skills,
    "satisfaction_score": satisfaction, "faculty_feedback_score": faculty_feedback,
})

# ================= Success Score =================
def minmax(s, invert=False):
    v = (s - s.min()) / (s.max() - s.min()) * 100
    return (100 - v) if invert else v

ind = pd.DataFrame(index=df.index)
ind["CGPA"] = minmax(df.cgpa)
ind["Subject Performance"] = minmax(df.avg_subject_marks)
ind["Backlogs (fewer = better)"] = minmax(df.backlogs.astype(float), invert=True)
ind["Attendance"] = minmax(df.attendance_pct)
ind["Subject-wise Attendance"] = minmax(df.subject_attendance_pct)
ind["LMS Logins (30d)"] = minmax(df.lms_logins_30d.astype(float))
ind["Assignment Completion"] = minmax(df.assignment_completion_pct)
ind["Events & Clubs"] = minmax(df.events_participated + df.clubs_joined * 2)
ind["Hackathons & Certifications"] = minmax(df.hackathons + df.certifications)
ind["Aptitude"] = minmax(df.aptitude_score)
ind["Coding"] = minmax(df.coding_score)
ind["Mock Interviews"] = minmax(df.mock_interviews.astype(float))
ind["Technical Skills"] = minmax(df.tech_skills_score)
ind["Soft Skills"] = minmax(df.soft_skills_score)
ind["Student Satisfaction"] = minmax(df.satisfaction_score)
ind["Faculty Feedback"] = minmax(df.faculty_feedback_score)

pillar_map = {
    "Academic": ["CGPA", "Subject Performance", "Backlogs (fewer = better)"],
    "Attendance": ["Attendance", "Subject-wise Attendance"],
    "LMS Engagement": ["LMS Logins (30d)", "Assignment Completion"],
    "Co-curricular": ["Events & Clubs", "Hackathons & Certifications"],
    "Placement Readiness": ["Aptitude", "Coding", "Mock Interviews"],
    "Skills": ["Technical Skills", "Soft Skills"],
    "Feedback": ["Student Satisfaction", "Faculty Feedback"],
}
pillar_w = {"Academic": 0.22, "Attendance": 0.14, "LMS Engagement": 0.12,
            "Co-curricular": 0.10, "Placement Readiness": 0.20,
            "Skills": 0.12, "Feedback": 0.10}
ind_w = {c: pillar_w[p] / len(cols) for p, cols in pillar_map.items() for c in cols}

raw_score = sum(ind[c] * w for c, w in ind_w.items())
df["success_score"] = (58 + (raw_score - raw_score.mean()) * 0.78).clip(5, 99).round(1)

for p, cols in pillar_map.items():
    df[f"pillar_{p.lower().replace(' ', '_').replace('-', '')}"] = ind[cols].mean(axis=1).round(1)

# ================= Risk flags =================
def flag(row):
    f = []
    if row.pillar_academic < 26 or row.cgpa < 4.8: f.append("Academic Risk")
    if row.attendance_pct < 55: f.append("Attendance Risk")
    if row.pillar_lms_engagement < 22: f.append("Disengagement Risk")
    if row.pillar_placement_readiness < 22: f.append("Placement Risk")
    if row.pillar_skills < 26: f.append("Skill Gap")
    return f

df["risk_flags"] = df.apply(flag, axis=1)
df["n_risks"] = df.risk_flags.str.len()
df["risk_level"] = df.n_risks.map(lambda n: "Critical" if n >= 3 else "High" if n == 2 else "Medium" if n == 1 else "Low")

# ================= Segmentation (K-Means on pillar scores) =================
pcols = [c for c in df.columns if c.startswith("pillar_")]
km = KMeans(n_clusters=5, n_init=10, random_state=7).fit(df[pcols])
df["segment"] = km.labels_
order = df.groupby("segment").success_score.mean().sort_values().index
names = ["Struggling", "Disengaged", "Placement-focused", "Placement-unready", "All-round"]
df["segment_name"] = df.segment.map(dict(zip(order,
    ["Struggling - needs all-round support",
     "Disengaged (attendance/LMS)",
     "Average academics, placement-unready",
     "Placement-focused performers (low co-curricular)",
     "All-round high performers"])))
df["segment_short"] = df.segment.map(dict(zip(order, names)))

# Bonus subgroup: high academics but low placement readiness
df["hi_acad_low_place"] = (df.pillar_academic >= 60) & (df.pillar_placement_readiness < 40)

# ================= Explainability =================
contrib = pd.DataFrame({c: ind[c] * ind_w[c] for c in ind.columns})
df["top_strengths"] = contrib.apply(lambda r: list(r.nlargest(3).index), axis=1)
df["top_gaps"] = contrib.apply(lambda r: list(r.nsmallest(3).index), axis=1)

df.to_csv("student_master.csv", index=False)
ind.to_csv("indicator_scores.csv", index=False)
print(f"Saved student_master.csv with {len(df)} students")
print(df.risk_level.value_counts().to_string())
