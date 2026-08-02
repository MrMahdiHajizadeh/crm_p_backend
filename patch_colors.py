import re

with open(r'c:\Users\mrmah\OneDrive\Desktop\CRM p\Django-CRM\frontend\src\app.css', 'r', encoding='utf-8') as f:
    content = f.read()

soft_palette = '''  /* Softer Premium Slate & Blue Palette */
  --color-primary: #3b82f6; /* Modern Blue instead of stark black */
  --color-on-primary: #ffffff;
  
  --color-primary-container: #eff6ff; /* Blue 50 */
  --color-on-primary-container: #1d4ed8; /* Blue 700 */

  --color-background: #f8fafc; /* Slate 50 */
  --color-on-background: #334155; /* Slate 700 */

  --color-surface: #ffffff;
  --color-surface-bright: #ffffff;
  --color-surface-dim: #f1f5f9; /* Slate 100 */
  
  --color-surface-container-lowest: #ffffff;
  --color-surface-container-low: #f8fafc; /* Slate 50 */
  --color-surface-container: #f1f5f9; /* Slate 100 */
  --color-surface-container-high: #e2e8f0; /* Slate 200 */
  --color-surface-container-highest: #cbd5e1; /* Slate 300 */

  --color-on-surface: #1e293b; /* Slate 800 */
  --color-on-surface-variant: #64748b; /* Slate 500 */
  --color-surface-variant: #f1f5f9;

  --color-outline: #94a3b8; /* Slate 400 */
  --color-outline-variant: #e2e8f0; /* Slate 200 - Very soft borders */

  --color-secondary: #64748b; /* Slate 500 */
  --color-on-secondary: #ffffff;
  --color-secondary-container: #f1f5f9;
  --color-on-secondary-container: #334155;

  --color-error: #ef4444; /* Red 500 */
  --color-on-error: #ffffff;
  --color-error-container: #fef2f2; /* Red 50 */
  --color-on-error-container: #b91c1c; /* Red 700 */
'''

# Find the block from --color-primary to --color-on-secondary-fixed and replace
pattern = r'--color-primary: #000000;.*?--color-on-secondary-fixed: #0b1c30;'
content = re.sub(pattern, soft_palette, content, flags=re.DOTALL)

# Soften the border radiuses
content = content.replace('--radius: 0.125rem;', '--radius: 0.375rem;')
content = content.replace('--radius-lg: 0.25rem;', '--radius-lg: 0.5rem;')

with open(r'c:\Users\mrmah\OneDrive\Desktop\CRM p\Django-CRM\frontend\src\app.css', 'w', encoding='utf-8') as f:
    f.write(content)

print("Palette softened")
