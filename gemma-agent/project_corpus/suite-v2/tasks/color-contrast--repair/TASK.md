Complete this browser application: Contrast Desk. Calculate contrast between two six-digit hex colors.
Read README.md, index.html, app.js, and logic.js. Find and repair the calculation defect in logic.js. Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.

Example input/output:
[[{"foreground": "#ffffff", "background": "#000000"}, {"ratio": 21, "normalText": "Pass", "largeText": "Pass"}]]

Accept only #RRGGBB (case insensitive). Convert sRGB channels to linear (x <= .04045: x/12.92; otherwise ((x+.055)/1.055)^2.4). Luminance coefficients .2126, .7152, .0722. Ratio (lighter+.05)/(darker+.05). Return ratio rounded to 2 decimals, normalText Pass at raw ratio >=4.5, largeText Pass at >=3; otherwise Fail.
