Complete this browser application: Box Office. Quote group tickets with a discount for groups of ten or more.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"adults": "2", "children": "1"}, {"tickets": 3, "total": 52, "discountPercent": 0}]]

Adults cost 20, children 12. Nonnegative counts. At least 10 total tickets earns 15% off the entire order. Return tickets, total rounded to 2 decimals, and discountPercent.
