Complete this browser application: Draft Lens. Count words, characters, and reading minutes for a draft.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"text": " hello   world\nagain "}, {"words": 3, "characters": 21, "readingMinutes": 1}]]

Words are nonempty whitespace-separated tokens. Characters counts Unicode code points, including whitespace. Reading speed 200 words/minute; round readingMinutes UP, zero for empty text. Return words, characters, readingMinutes.
