Complete this browser application: Open Doors. Check remaining seats and group admission for an event.
Read README.md, index.html, app.js, and logic.js. Implement the missing run(d) function in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"capacity": "10", "booked": "7", "group": "3"}, {"remaining": 3, "admitted": "Yes"}]]

capacity and booked >= 0, group >= 1. Reject booked > capacity. remaining = capacity - booked. admitted is Yes if the whole group fits, including exactly filling the venue; otherwise No.
