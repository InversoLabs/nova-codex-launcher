Complete this browser application: Media Space. Estimate storage for a collection of media files.
Read README.md, index.html, app.js, and logic.js. Implement the missing run(d) function in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"count": "100", "size": "25", "copies": "2"}, {"megabytes": 5000, "gigabytes": 5}]]

count and size >=0; copies >=1. megabytes = count*size*copies. Decimal gigabytes = megabytes/1000. Round to 2 decimals.
