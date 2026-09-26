Complete this browser application: Focus Blocks. Plan focus blocks and breaks without adding a break after the last block.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"blocks": "4", "focus": "25", "rest": "5"}, {"focusMinutes": 100, "breakMinutes": 15, "totalMinutes": 115}]]

blocks must be a whole integer >=1; focus >=1; rest >=0. There are blocks-1 breaks. Return focusMinutes, breakMinutes, totalMinutes.
