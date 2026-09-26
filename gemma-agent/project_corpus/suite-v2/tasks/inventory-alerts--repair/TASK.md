Complete this browser application: Stock Watch. Find items at or below their reorder threshold. One name,stock,threshold per line.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"items": "Paper,5,5\nInk,8,3"}, {"reorderCount": 1, "items": "Paper"}]]

Rows are name,stock,threshold. Trim whitespace; stock and threshold >= 0. Include equality when selecting low stock. Return reorderCount and comma-space joined items, or None.
