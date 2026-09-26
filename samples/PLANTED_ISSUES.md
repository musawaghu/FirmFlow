# Sample manual: answer key

`studio_meridian_manual.pdf` / `.docx` is a deliberately messy onboarding manual for the demo firm, **Studio Meridian Architects**. It is synthetic. The text lives in `manual_source.txt`; rebuild both files with:

```bash
uv run --no-project --with python-docx --with pymupdf samples/build_manual.py
```

If you edit the source, re-check the page numbers below.

Use this file to check that the Manual Enhancer (a) flags every planted problem and (b) never "fixes" one by picking a side or inventing the answer.

## Planted issues (15 pages)

### Broken links (`broken_link`)

| # | Page | Section | What's wrong |
| --- | --- | --- | --- |
| B1 | 3 | 3. Staff Directory | `http://intranet.studiomeridian.example/staff/directory.aspx`: the very next paragraph says the intranet was retired in 2021 |
| B2 | 4 | 4. BIM / Revit | `\\SM-FS01\Standards\BIM\SM_BIM_Standards_v3.pdf`: every other path uses server `SM-FS02`. The FAQ on p15 hints that the link may not work |
| B3 | 9 | 6. Timesheets, step 1 | "the link on the intranet homepage": the intranet was retired |
| B4 | 12 | 8. PTO FAQ | `go/pto-form (old link - will be updated)` |
| B5 | 14 | 10. Harassment Prevention | Anonymous hotline `https://studiomeridian.ethicsline.example/report (LINK TBD)` |

### Outdated references (`outdated_reference`)

| # | Page | Section | What's wrong |
| --- | --- | --- | --- |
| O1 | 4 | 4. BIM / Revit | "All production work ... is done in Autodesk Revit 2019" (the 2024 note on p6 says Revit 2025) |
| O2 | 9 | 6. Timesheets, step 1 | "Log in to Deltek Vision", but the intro says the firm moved to Vantagepoint in 2022 |
| O3 | 9 | 6. Timesheets, step 1 | "Vision works best in Internet Explorer 11" |
| O4 | 14 | 10. Harassment Prevention | "watch the 2017 harassment training video on the DVD" |

### Contradictions (`contradiction`)

| # | Pages | What conflicts |
| --- | --- | --- |
| C1 | 4 vs 6 | Revit 2019 vs "All active projects are now on Revit 2025" |
| C2 | 7 vs 8 | Core hours 10:00 AM–4:00 PM vs "Core hours are 9:30 AM to 3:30 PM" |
| C3 | 9 | Timesheets due Friday by 5:00 PM (current week) vs Monday at 12:00 noon (previous week) |
| C4 | 11 vs 12 | PTO accrual for years 0–2: 15 days (120 h) in the table vs 10 days (80 h) in the FAQ |
| C5 | 11 vs 12 | PTO notice: two weeks vs 5 business days |
| C6 | 14 | Harassment training every two years vs annually |

### Missing steps (`missing_step`)

| # | Page | Procedure | What's missing |
| --- | --- | --- | --- |
| M1 | 9 | How to fill out your timesheet | Numbering jumps 3 → 5, and no step says to **submit** the timesheet |
| M2 | 11 | How to request PTO | Step 2 (talk to PM) jumps to step 3 (HR confirms). There's no step that actually **submits the request** |

## Correct behavior

- **Flag, don't fix.** For C3, the enhancer must not pick Friday or Monday. Both stay visible and the issue goes to the admin. The same applies to C1, C2, C4, C5 and C6.
- **Don't fill gaps.** For M1 and M2, the module must not invent a "Click Submit" or "Submit in the HR portal" step. Flag it instead.
- **Keep the content.** Current links (SharePoint People page p3, HR portal p10) are fine and should survive into the modules.
- **Leave out the noise.** The firm history, softball team and "mentorship: coming soon" belong in no required module. At most they go in a "Later" welcome module.

## Demo modules and where their content lives

| Module | Source sections (pages) | Suggested priority | Critical sections for the final check |
| --- | --- | --- | --- |
| Timesheets | 6 (p9) | Day 1 | Weekly deadline (after the admin resolves C3), project and phase codes, overhead codes |
| Staff Directory | 3 (p3), 11 FAQ (p15) | Day 1 | "If you don't know who to ask, ask the Office Manager"; where project teams are listed |
| Company Policies & Workplace Etiquette | 5 (p7–8), 1 (p2) | Week 1 | Core hours (after C2), plotting rules, design review etiquette |
| How to Use BIM | 4 (p4–6) | Day 1 | **4.1 worksharing rules, 4.2 Detach from Central**, 4.3 keynote rules |
| PTO | 8 (p11–12), 7 payroll (p10) | Week 1 | Carry-over limit, recording PTO on timesheets |
| Privacy & Harassment Training | 9 (p13), 10 (p14) | Day 1 | Who to report to, no retaliation, posting project images, lost devices within 24 h |

**Demo quiz scenario** (p5, §4.2): *"You need a copy of the project's central Revit model to test a design option. What do you do?"* A correct answer:
- opens the central in Revit with **Detach from Central**
- chooses **Detach and preserve worksets**
- saves the copy to the project **Sandbox** folder

Copying the file in File Explorer is wrong.

## Directory cross-check

Every name and title in the Key Contacts table (p3) and the harassment reporting section (p14) matches a row in `supabase/seed.sql`, so the assistant's contact cards and the manual agree.

## Parser note

The PDF uses ligatures, so text extracted with PyMuPDF's defaults contains `ﬀ`/`ﬁ`. Expand them when extracting: leave `TEXT_PRESERVE_LIGATURES` out of the flags. Otherwise grounding checks will see "Staﬀ" ≠ "Staff".
