Complete this browser application: Guest List. Summarize invited guests by response. One name,status per line.
Read README.md, index.html, app.js, and logic.js. Implement the missing run(d) function in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"guests": "Ada,YES\nBen,pending\nCora,no"}, {"attending": 1, "declined": 1, "pending": 1, "total": 3}]]

Each line name,status. Trim; accept status case insensitively as yes/no/pending. Reject unknown status. Return attending, declined, pending, total.
