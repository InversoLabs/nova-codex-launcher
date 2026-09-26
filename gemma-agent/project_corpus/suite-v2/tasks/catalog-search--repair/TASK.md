Complete this browser application: Small Shop. Filter a small product catalog by text and maximum price.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"query": " BAG ", "budget": "25"}, {"matches": 1, "products": "Canvas Bag"}]]

Catalog: Canvas Bag 25, Desk Lamp 60, Notebook 12, Travel Mug 25. Trim and lowercase search query; substring match names, maximum price inclusive. Sort ascending price then name. Return matches and comma-space joined products, or None.
