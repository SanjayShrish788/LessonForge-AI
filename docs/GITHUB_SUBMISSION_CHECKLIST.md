# GitHub submission checklist

Suggested name: `lessonforge-ai`  
Description: Local instructor workspace for research-backed lesson creation and independent AI quality reviews.

- [ ] Review README, source, tests, documentation, package lockfiles and `.env.example` for inclusion.
- [ ] Exclude `.env`, local databases and WAL files, `.venv`, `node_modules`, generated builds, logs, private artifacts and personal information. Confirm `.gitignore` and inspect the actual proposed file list; ignored files are not a substitute for a secret scan.
- [ ] Scan staged content and history for credentials without displaying their values. Remove any secret and rotate it if exposed.
- [ ] Create a clean local repository only after reviewing the file list. Suggested initial commit: `Build LessonForge instructor workspace`.
- [ ] `git init`; `git add .`; inspect `git status --short`, `git diff --cached --stat` and `git diff --cached`; verify no private material; then commit.
- [ ] Verify setup and tests from a clean clone with the documented Python and Node versions.
- [ ] Only after explicit owner approval, create the remote, add it with `git remote add origin <repository-url>`, and push the intended branch. Check a signed-out view and submission links.

No remote repository has been created or published by this work.
