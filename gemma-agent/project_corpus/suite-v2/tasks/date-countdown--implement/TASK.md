Complete this browser application: Day Marker. Count calendar days between ISO dates using UTC.
Read README.md, index.html, app.js, and logic.js. Implement the missing run(d) function in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"start": "2024-02-28", "end": "2024-03-01"}, {"days": 2, "direction": "Future"}]]

Require real calendar ISO YYYY-MM-DD dates; UTC midnight. days is signed end minus start in calendar days. direction Future for positive, Past for negative, Today for zero.
