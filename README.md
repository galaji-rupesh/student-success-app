# Smart Campus Analytics — Student Success Platform

A Streamlit dashboard using a reproducible synthetic dataset of 800 students. It shows success scores, risk flags, student segments, and individual student profiles.

## Run locally

Install Python 3.10 or newer, then open this folder in VS Code. Open **Terminal → New Terminal** and run:

```text
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The app creates `student_master.csv` and `indicator_scores.csv` the first time it starts. They are generated outputs and are intentionally excluded from GitHub. The data is synthetic; do not replace it with identifiable student records in a public repository.

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository named `student-success-app`. Choose **Public** for the simplest setup, and leave **Add a README**, `.gitignore`, and license unchecked so the new repository is empty.
2. In VS Code, open this folder (`StudentSuccessApp`) and use **Terminal → New Terminal**.
3. In the GitHub repository page, copy its HTTPS URL, then run these commands in the VS Code terminal, replacing `YOUR-USERNAME` with your GitHub username:

```text
git init -b main
git add .
git commit -m "Add Student Success Streamlit app"
git remote add origin https://github.com/YOUR-USERNAME/student-success-app.git
git push -u origin main
```

If GitHub asks you to sign in, complete its browser sign-in prompt. Do not put a password or token directly in these commands. Refresh the repository page and confirm that `app.py`, `generate_data.py`, and `requirements.txt` are visible.

4. Visit [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub. Choose **Create app**, then **Yup, I have an app**.
5. Select your repository, branch `main`, and the file path `app.py`. Optionally choose an app URL, then click **Deploy**.
6. Wait for the build to finish. The generated page is public to anyone with its URL if the repository/app is public; the app currently contains synthetic data.

## If deployment fails

Open the app in your Streamlit Community Cloud workspace, then open **Manage app** (the menu/gear next to the app) and select **Logs**. Read the first red traceback line and the lines immediately above it. If the log says a package is missing, confirm `requirements.txt` is in the repository root and push the fix to GitHub; Community Cloud rebuilds after a push. If it says a file is missing, check the selected entrypoint is exactly `app.py` and that both Python files are in the repository root. After changing files, push with:

```text
git add .
git commit -m "Fix deployment"
git push
```

