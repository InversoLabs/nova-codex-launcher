Complete this browser application: Monthly View. Convert subscription prices to a monthly and annual total.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"monthly": "20", "annual": "120"}, {"monthlyEquivalent": 30, "yearlyTotal": 360}]]

monthly and annual >=0. monthlyEquivalent = monthly + annual/12. yearlyTotal = monthly*12 + annual. Round to 2 decimals.
