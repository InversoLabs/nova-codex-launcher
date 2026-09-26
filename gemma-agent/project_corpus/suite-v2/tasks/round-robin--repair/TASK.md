Complete this browser application: Match Day. Calculate pairings for a single round-robin tournament.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"teams": "A\nB\nC"}, {"teams": 3, "matches": 3, "schedule": "A vs B; A vs C; B vs C"}]]

Trim lines and drop blanks. Reject duplicate team names. Each pair exactly once, input order, excluding self matches. Return teams count, matches count, and schedule joined with semicolon-space (A vs B), or No matches.
