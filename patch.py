import re

with open(r'c:\Users\mrmah\OneDrive\Desktop\CRM p\Django-CRM\frontend\src\app.css', 'r', encoding='utf-8') as f:
    content = f.read()

# Add shadcn color mappings to the @theme inline block
mappings = '''
  /* Shadcn-svelte mappings to Stitch tokens */
  --color-foreground: var(--color-on-background);
  --color-card: var(--color-surface-container-lowest);
  --color-card-foreground: var(--color-on-surface);
  --color-popover: var(--color-surface-container-lowest);
  --color-popover-foreground: var(--color-on-surface);
  --color-primary-foreground: var(--color-on-primary);
  --color-secondary-foreground: var(--color-on-secondary);
  --color-muted: var(--color-surface-variant);
  --color-muted-foreground: var(--color-on-surface-variant);
  --color-accent: var(--color-surface-container-highest);
  --color-accent-foreground: var(--color-on-surface);
  --color-destructive: var(--color-error);
  --color-destructive-foreground: var(--color-on-error);
  --color-border: var(--color-outline-variant);
  --color-input: var(--color-outline);
  --color-ring: var(--color-primary);
'''

# insert before the closing brace of @theme inline
content = re.sub(r'(--font-headline-md:[^;]+;)\n\}', r'\1\n' + mappings + '\n}', content)

with open(r'c:\Users\mrmah\OneDrive\Desktop\CRM p\Django-CRM\frontend\src\app.css', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated app.css successfully')
