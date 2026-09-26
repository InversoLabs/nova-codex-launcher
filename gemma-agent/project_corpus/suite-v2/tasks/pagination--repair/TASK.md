Complete this browser application: Page Window. Calculate page ranges for a paginated results list.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"total": "42", "size": "10", "page": "5"}, {"pages": 5, "page": 5, "first": 41, "last": 42}]]

total >=0, size >=1, page >=1, all integers. pages = ceiling(total/size); cap requested page at last page. Empty results: all output values zero. Otherwise return pages, page, first 1-based index, last capped at total.
