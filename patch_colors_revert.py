import re

with open(r'c:\Users\mrmah\OneDrive\Desktop\CRM p\Django-CRM\frontend\src\app.css', 'r', encoding='utf-8') as f:
    content = f.read()

original_palette = '''  --color-primary: #000000;
  --color-surface-container-highest: #e0e3e5;
  --color-on-tertiary-fixed-variant: #484645;
  --color-on-secondary-fixed-variant: #38485d;
  --color-surface-bright: #f7f9fb;
  --color-primary-container: #1c1b1b;
  --color-on-primary-fixed-variant: #474646;
  --color-on-primary-fixed: #1c1b1b;
  --color-on-primary-container: #858383;
  --color-surface-container-lowest: #ffffff;
  --color-on-tertiary-fixed: #1d1b1a;
  --color-inverse-surface: #2d3133;
  --color-secondary-fixed: #d3e4fe;
  --color-outline: #747878;
  --color-on-background: #191c1e;
  --color-surface-variant: #e0e3e5;
  --color-on-tertiary-container: #868381;
  --color-tertiary-container: #1d1b1a;
  --color-on-surface: #191c1e;
  --color-on-secondary: #ffffff;
  --color-on-secondary-container: #54647a;
  --color-surface-dim: #d8dadc;
  --color-surface: #f7f9fb;
  --color-tertiary-fixed-dim: #cac6c3;
  --color-secondary-container: #d0e1fb;
  --color-outline-variant: #c4c7c7;
  --color-secondary-fixed-dim: #b7c8e1;
  --color-on-primary: #ffffff;
  --color-tertiary-fixed: #e6e1df;
  --color-tertiary: #000000;
  --color-inverse-primary: #c8c6c5;
  --color-surface-container: #eceef0;
  --color-surface-container-low: #f2f4f6;
  --color-on-surface-variant: #444748;
  --color-inverse-on-surface: #eff1f3;
  --color-surface-container-high: #e6e8ea;
  --color-primary-fixed-dim: #c8c6c5;
  --color-on-tertiary: #ffffff;
  --color-primary-fixed: #e5e2e1;
  --color-background: #f7f9fb;
  --color-surface-tint: #5f5e5e;
  --color-on-error-container: #93000a;
  --color-on-error: #ffffff;
  --color-error: #ba1a1a;
  --color-error-container: #ffdad6;
  --color-secondary: #505f76;
  --color-on-secondary-fixed: #0b1c30;'''

# Pattern to replace everything from --color-primary up to --color-on-error-container
pattern = r'/\* Softer Premium Slate & Blue Palette \*/.*?--color-on-error-container: #b91c1c;'
content = re.sub(pattern, original_palette, content, flags=re.DOTALL)

# Revert border radiuses
content = content.replace('--radius: 0.375rem;', '--radius: 0.125rem;')
content = content.replace('--radius-lg: 0.5rem;', '--radius-lg: 0.25rem;')

with open(r'c:\Users\mrmah\OneDrive\Desktop\CRM p\Django-CRM\frontend\src\app.css', 'w', encoding='utf-8') as f:
    f.write(content)

print("Palette reverted")
