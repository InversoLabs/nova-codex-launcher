Complete this browser application: Away Days. Estimate a trip budget including lodging, meals, and transport.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"nights": "3", "nightly": "90", "daily": "30", "transport": "80"}, {"days": 4, "lodging": 270, "total": 470}]]

nights, nightly room price, daily meals, transport >= 0. There is one more day than nights. Return days, lodging (nights * nightly), and total including meals for all days and transport. Money rounded to 2 decimals.
