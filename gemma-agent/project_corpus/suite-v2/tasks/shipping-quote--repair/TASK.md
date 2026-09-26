Complete this browser application: Parcel Desk. Quote parcel shipping with rounded-up weight tiers and a free-shipping threshold.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"weight": "1.2", "subtotal": "40"}, {"shipping": 7, "orderTotal": 47}]]

weight >= .01 kg; subtotal >= 0. Shipping is free for subtotal >=75, otherwise 5 for first kg plus 2 per additional started kg. Return shipping and orderTotal rounded to 2 decimals.
