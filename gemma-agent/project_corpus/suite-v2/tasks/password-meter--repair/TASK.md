Complete this browser application: Passphrase Lens. Give local-only password structure feedback. Nothing is transmitted.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"password": "abcdefgh"}, {"length": 8, "categories": 1, "rating": "Weak"}]]

length = JavaScript string length. categories counts lowercase, uppercase, digits, and nonalphanumeric/nonwhitespace punctuation present. Score = categories plus 2 if length>=12, else 1 if >=8, else 0. rating Strong at >=6, Moderate at >=4, otherwise Weak. Never save input or results.
