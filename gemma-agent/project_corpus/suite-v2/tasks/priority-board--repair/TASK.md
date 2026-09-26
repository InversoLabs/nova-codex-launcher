Complete this browser application: Next Up. Sort tasks by priority and preserve order within each priority. One title,priority per line.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"tasks": "A,low\nB,high\nC,medium"}, {"count": 3, "next": "B", "order": "B → C → A"}]]

Rows title,priority. Valid priorities high,medium,low. Sort in that order, keeping original order for ties. Return count, next (first title or None), and order joined with space-arrow-space ( → ). Reject unknown priorities.
