# PeopleMind AI Demo Guide

This guide provides a repeatable presentation flow for the local PeopleMind AI MVP.

The demo should use safe sample data and must never expose passwords, JWT secrets, private CVs, confidential HR documents, or generated credential files.

## 1. Pre-Demo Checklist

Before presenting:

- Confirm Ollama is running
- Confirm `qwen3:4b-instruct` is available
- Confirm `embeddinggemma` is available
- Start the FastAPI backend
- Start the React frontend
- Confirm the API health endpoint works
- Confirm HR/Admin login works
- Confirm the dashboard loads
- Use only safe demo/sample data
- Keep local credential files off-screen

Application:

`http://localhost:5173`

API health:

`http://127.0.0.1:8000/api/health`

## 2. Login Experience

Open the PeopleMind AI login page.

Demonstrate:

- Local-first product identity
- Secure HR workspace login
- Animated AI visual
- HR/Admin authentication

Do not display the password during a presentation or screen recording.

## 3. Dashboard

After HR/Admin login, show the dashboard.

Highlight:

- Employee count
- Attendance rate
- Candidate count
- Document count
- Attendance overview
- Workspace summary
- Recent activity
- Quick actions

Explain that dashboard values are loaded from backend application data rather than hardcoded statistics.

## 4. Document Intelligence

Recommended flow:

1. Open Document Assistant.
2. Show the document library.
3. Upload a safe sample HR policy PDF if necessary.
4. Process and index the document.
5. Ask a question that has a clear answer inside the PDF.
6. Show the generated answer.
7. Show the source document and page citation.
8. Open the cited page when useful.
9. Demonstrate document search.
10. Optionally demonstrate rename or delete.

Key message:

> PeopleMind AI answers from locally indexed HR documents and returns source references for human verification.

## 5. CV Intelligence

Recommended flow:

1. Open CV Intelligence.
2. Show candidate profiles.
3. Show available job profiles.
4. Select or create a safe demo job.
5. Assign demo candidates.
6. Run ATS analysis.
7. Run candidate-to-job matching.
8. Show ranking or comparison support.
9. Show human review controls.

Key message:

> PeopleMind AI supports candidate review, but final employment decisions remain with the human reviewer.

## 6. Attendance Management

As HR/Admin, demonstrate:

1. Open Attendance Management.
2. Show teams and shifts.
3. Show the employee roster.
4. Show weekly holiday configuration.
5. Open Daily Attendance.
6. Show attendance history.
7. Show leave management.
8. Show attendance analytics.
9. Show an employee monthly report.
10. Demonstrate CSV, print, or PDF reporting when useful.

Important attendance states:

- Present
- Absent
- On Leave
- Weekly Holiday

## 7. Shared Attendance Account

This flow demonstrates restricted operational access.

1. Log out from HR/Admin.
2. Log in using a locally generated shared attendance account.
3. Show that only permitted attendance functionality is available.
4. Show the assigned team and shift scope.
5. Select the actual submitting employee when required.
6. Submit attendance for a safe demo date/team/shift.
7. Show that the submission becomes locked for the shared account.
8. Log out.
9. Log back in as HR/Admin.
10. Correct one demo attendance record if required.
11. Confirm that the original submission audit remains preserved.

Never expose the shared-account password or local credential file during the demo.

Key message:

> Shared attendance accounts receive restricted operational access while HR/Admin retains correction authority and audit history.

## 8. Attendance Report Administration

For disposable demo data only:

1. Open Attendance History / Reports.
2. Select a demo report.
3. Choose the delete action.
4. Confirm the warning.
5. Enter a meaningful deletion reason.
6. Complete the deletion.
7. Show that history and analytics recalculate.

Report deletion is HR/Admin-only and retains deletion audit information.

Do not delete real operational attendance records during a presentation.

## 9. Security Talking Points

Useful technical points to highlight:

- Local Ollama AI inference
- Local SQLite database
- Local document and vector storage
- Password hashing
- JWT authentication
- HR/Admin route protection
- Scoped shared attendance access
- Attendance submission audit history
- Attendance deletion audit history
- Human review for candidate decisions
- Private credential files excluded from Git

## 10. Final Smoke Test

Before presenting, verify:

- [ ] Login page opens
- [ ] HR/Admin login works
- [ ] Dashboard loads live data
- [ ] Document library loads
- [ ] Document Q&A works
- [ ] Document citations display
- [ ] Candidate list loads
- [ ] Job profiles load
- [ ] Attendance roster loads
- [ ] Daily attendance loads
- [ ] Attendance history loads
- [ ] Attendance analytics loads
- [ ] Monthly attendance report loads
- [ ] Shared attendance login works
- [ ] Shared account cannot access HR/Admin-only modules
- [ ] Logout works

## 11. Development Verification

Backend:

```powershell
& ".\.venv\Scripts\python.exe" -m pytest backend\tests -q
```

Frontend:

```powershell
Set-Location ".\frontend"
npm.cmd run lint
npm.cmd run build
Set-Location ".."
```

Git:

```powershell
git diff --check
git status --short
```

## 12. Demo Data Safety

For screenshots, recordings, GitHub, portfolio use, or interviews:

- Prefer fictional or authorized HR documents
- Prefer fictional or authorized CVs
- Avoid unnecessary personal employee information
- Never expose passwords
- Never expose JWT secrets
- Never expose `.env`
- Never expose generated attendance credential files
- Never commit the SQLite database
- Never commit uploaded private files

## 13. Closing Message

> PeopleMind AI combines local document intelligence, human-reviewed candidate analysis, and operational attendance management in one privacy-focused HR workspace.
