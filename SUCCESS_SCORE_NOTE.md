# Student Success Score — methodology note

## What it is
A single 0–100 score per student that combines academic performance, attendance, LMS
engagement, co-curricular activity, placement readiness, skills, and feedback into one
unified, explainable measure. Higher is better; ~58 is the cohort average after calibration.

## Indicators (16 total, grouped into 7 pillars)

| Pillar | Weight | Indicators |
|---|---|---|
| Academic | 22% | CGPA, subject performance, backlogs (inverted) |
| Attendance | 14% | Overall %, subject-wise % |
| LMS engagement | 12% | Logins (30d), assignment completion % |
| Placement readiness | 20% | Aptitude, coding, mock interviews |
| Skills | 12% | Technical skills, soft skills |
| Co-curricular | 10% | Events & clubs, hackathons & certifications |
| Feedback | 10% | Student satisfaction, faculty feedback |

Every indicator is min–max normalized to 0–100 within the cohort (backlogs inverted so
"fewer = better" points the same direction as everything else). The Success Score is the
weighted sum of the 16 normalized indicators, then linearly recentered to a mean of ~58
with most scores between 35 and 90 for easy interpretation.

## Risk flags
A student is flagged when a pillar or raw metric crosses a threshold:

- **Academic risk** — academic pillar < 26 or CGPA < 4.8
- **Attendance risk** — attendance < 55%
- **Disengagement risk** — LMS pillar < 22
- **Placement risk** — placement pillar < 22
- **Skill gap** — skills pillar < 26

Risk level: **Critical** = 3+ flags, **High** = 2, **Medium** = 1, **Low** = none.

## Explainability
Each student's score decomposes exactly: indicator contribution = indicator weight ×
normalized value. The app surfaces each student's top-3 contributing gaps (dragging the
score down) and top-3 strengths, plus a per-pillar breakdown — so faculty see *why* a
score is what it is, not just the number.

## Segmentation
K-Means (k=5) on the seven pillar scores groups students into: Struggling, Disengaged,
Placement-unready, Placement-focused, and All-round high performers — including the
actionable "high academics / low placement readiness" group for targeted bootcamps.

## Data
800 synthetic students generated with correlated latent traits so realistic patterns
emerge across sources (engaged students attend more, log in more, and score higher).
Swap in real CSV exports from your college systems using the same column names and the
whole pipeline runs unchanged.
