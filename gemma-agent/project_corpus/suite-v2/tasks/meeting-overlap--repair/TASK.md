Complete this browser application: Meet Window. Find the overlap of two same-day availability windows in 24-hour time.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"startA": "09:00", "endA": "12:00", "startB": "11:00", "endB": "14:00"}, {"overlapMinutes": 60, "available": "Yes"}]]

Strict HH:MM 24-hour values, same day. Reject an end before its start. Return nonnegative overlapMinutes and available (Yes for positive overlap, No otherwise).
