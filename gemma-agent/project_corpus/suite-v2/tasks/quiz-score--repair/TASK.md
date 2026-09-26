Complete this browser application: Quiz Studio. Grade comma-separated answers against a comma-separated answer key.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"answers": "a, b, c", "key": "A,B,D"}, {"correct": 2, "total": 3, "percent": 66.67}]]

Split comma-separated answers/key, trim, compare case insensitively. Equal lengths and nonempty key entries required. Return correct, total, percent rounded to 2 decimals.
