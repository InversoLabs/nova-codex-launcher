Complete this browser application: Course Balance. Calculate a weighted average from score,weight rows. Weights must total 100.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"grades": "80,40\n90,60"}, {"average": 86}]]

Rows score,weight. Scores 0..100, weights >=0; total weights must equal 100 (tolerance .0001). average is sum(score*weight)/100 rounded to 2 decimals.
