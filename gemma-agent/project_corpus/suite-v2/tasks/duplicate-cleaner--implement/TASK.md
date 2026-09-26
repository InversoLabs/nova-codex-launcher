Complete this browser application: Clean List. Deduplicate a list case-insensitively while preserving the first spelling and order.
Read README.md, index.html, app.js, and logic.js. Implement the missing run(d) function in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"items": " Alpha\nbeta\nALPHA "}, {"unique": 2, "removed": 1, "items": "Alpha, beta"}]]

Ignore blank lines and trim each item. Deduplicate case insensitively; keep first spelling and order. Return unique count, removed count, and comma-space joined items.
