---
name: devlog
description: >
  Write a dated entry into docs/CHECKPOINT.md summarising everything
  that happened in this session or since the last devlog. Trigger this when
  the user types /devlog, asks for a summary, or when a major milestone is
  reached (a feature is complete, a major bug is fixed, a module is finished,
  or a significant refactor is done). Never trigger for small individual steps —
  only at natural stopping points or when explicitly asked.
---

# Devlog Command

When this command runs, Claude writes a structured entry into `docs/CHECKPOINT.md`
at the root of the project. If the file does not exist, create it with a header
first, then write the entry. If it does exist, append the new entry at the top
(most recent first).

---

## Step 1 — Create the file if it doesn't exist

If `docs/CHECKPOINT.md` does not exist, create it with this header first:

```markdown
# Project Checkpoint Log

This file is auto-updated by Claude whenever a checkpoint is triggered.
Entries are ordered newest first.

---
```

---

## Step 2 — Gather everything before writing

Before writing the entry, Claude must mentally collect:

1. What was the goal or task at the start of this session / milestone?
2. What files were created? What files were changed?
3. For each file touched — what functions, classes, or logic blocks were added or modified?
4. Were there any errors, bugs, or failed attempts? What was the fix?
5. Was anything different from what was originally planned?
6. Did any logic change from a previous approach?

Do not write the entry until all six are accounted for.

---

## Step 3 — Write the entry

Append this structure at the TOP of `docs/CHECKPOINT.md`, below the header:

```markdown
---

## Devlog — [DATE] at [TIME]
> Trigger: [manual /devlog | milestone: describe what was completed]

### 🎯 What Was Planned
[1–2 sentences — what the goal or task was going into this session or milestone]

### ✅ What Was Built / Changed

| File | Type | What It Does |
|------|------|--------------|
| `path/to/file.js` | Created | [1 sentence — what this file is for] |
| `path/to/other.js` | Modified | [1 sentence — what changed and why] |

#### Code Summary
For each meaningful function, class, or logic block created or changed:

**`functionName()` — `path/to/file.js`**
What it does: [1–2 sentences — plain English, what it does and its core logic]
Why this way: [1 sentence — why this approach was used]

*(Repeat for each function / class / logic block touched)*

### 🔄 Logic Changes
[If any logic changed from a previous version — what it was before, what it is now, and why.
Write "None" if this is the first implementation or nothing changed.]

### 🐛 Errors Encountered & Fixes

| Error | What Caused It | Fix Applied |
|-------|---------------|-------------|
| [brief error description] | [root cause in plain English] | [what was done to fix it] |

*(Write "None" if no errors occurred)*

### 📋 Planned vs Built
[1–3 sentences — did what got built match what was planned? If not, what changed and why?
Write "Matched plan" if everything went as expected.]

---
```

---

## Formatting Rules

- Date format: `17 Mar 2026`
- Time format: 24hr, e.g. `14:32`
- File paths always in backticks: `` `src/utils/auth.js` ``
- Function and class names always in backticks: `` `authGuard()` ``
- Keep each Code Summary entry to 2–3 lines max — no walls of text
- If more than 6 functions were touched, group minor ones: "Helper utilities in `utils.js`: 3 small functions added for string formatting — `trim()`, `capitalize()`, `slugify()`. Each takes a string and returns a transformed version."
- Errors table: if no errors, write a single row with "None" rather than leaving the table empty
- Never delete or overwrite previous entries — always append at the top

---

## Auto-Milestone Detection

Claude should trigger a checkpoint automatically (without being asked) when:

- A complete feature is finished end-to-end
- A module or file set is fully implemented
- A significant bug is found and fixed
- A major refactor is completed
- The user says anything like "that's done", "ship it", "looks good", "moving on"

When auto-triggering, Claude should say:
> "That looks like a milestone — writing a devlog entry to `docs/CHECKPOINT.md`."

Then run the command immediately.

---

## Example Entry

```markdown
---

## Devlog — 17 Mar 2026 at 14:32
> Trigger: milestone — auth middleware module completed

### 🎯 What Was Planned
Build a reusable auth middleware layer that protects all API routes and rejects
unauthenticated requests before they reach any business logic.

### ✅ What Was Built / Changed

| File | Type | What It Does |
|------|------|--------------|
| `src/middleware/authGuard.js` | Created | Middleware that checks for a valid JWT token on every protected route |
| `src/routes/user.js` | Modified | Added authGuard to all user routes that require login |
| `src/app.js` | Modified | Registered the middleware in the Express app setup |

#### Code Summary

**`authGuard()` — `src/middleware/authGuard.js`**
What it does: Reads the Authorization header on every incoming request. If no token is present it immediately returns a 401 error. If a token exists it calls next() to let the request through to the route handler.
Why this way: Centralised in one middleware so every route gets the check automatically — no need to repeat the logic inside each route.

**`verifyToken()` — `src/middleware/authGuard.js`**
What it does: Takes the raw token string, decodes it using the JWT secret, and returns the decoded payload or throws an error if invalid.
Why this way: Separated from authGuard so token verification logic can be tested independently and reused elsewhere if needed.

### 🔄 Logic Changes
Previous version checked for auth inside each route handler directly. Changed to middleware so auth is decoupled from business logic entirely. Routes no longer contain any auth code.

### 🐛 Errors Encountered & Fixes

| Error | What Caused It | Fix Applied |
|-------|---------------|-------------|
| `Cannot read property 'authorization' of undefined` | Accessing headers before the request object was fully set up | Moved middleware registration after body-parser in app.js |
| JWT verify throwing on expired tokens instead of returning 401 | Error was being thrown uncaught | Wrapped verifyToken in try/catch and mapped the error to a 401 response |

### 📋 Planned vs Built
Matched plan. Middleware works as designed. One unplanned addition: extracted verifyToken into its own function during implementation to make it easier to test — this was not in the original plan but improved the design.

---
```