Complete this browser application: Kitchen Scale. Scale recipe quantities without losing fractional portions.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"amount": "250", "servings": "4", "target": "6"}, {"quantity": 375, "factor": 1.5}]]

amount >= 0; servings and target >= 0.01. quantity = amount * target / servings; factor = target / servings. Round both to 2 decimals.
