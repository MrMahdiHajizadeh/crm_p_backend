import re

with open('frontend/src/app.css', 'r', encoding='utf-8') as f:
    content = f.read()

new_colors = '''  --color-on-primary-fixed: #111c2d;
  --color-surface-container: #eceef0;
  --color-surface-variant: #e0e3e5;
  --color-secondary-fixed: #dfe3e7;
  --color-on-tertiary-container: #0099d9;
  --color-on-tertiary-fixed: #001e2f;
  --color-on-surface-variant: #45474c;
  --color-inverse-primary: #bcc7de;
  --color-surface-dim: #d8dadc;
  --color-on-primary: #ffffff;
  --color-on-error: #ffffff;
  --color-on-primary-fixed-variant: #3c475a;
  --color-on-tertiary: #ffffff;
  --color-on-secondary-fixed-variant: #43474b;
  --color-secondary: #5a5f62;
  --color-on-secondary: #ffffff;
  --color-surface-tint: #545f73;
  --color-outline: #75777d;
  --color-secondary-container: #dce0e4;
  --color-on-secondary-container: #5e6367;
  --color-on-tertiary-fixed-variant: #004c6e;
  --color-on-error-container: #93000a;
  --color-on-background: #191c1e;
  --color-tertiary-container: #002c42;
  --color-surface-container-low: #f2f4f6;
  --color-error: #ba1a1a;
  --color-primary-fixed-dim: #bcc7de;
  --color-on-primary-container: #8590a6;
  --color-surface-container-high: #e6e8ea;
  --color-inverse-on-surface: #eff1f3;
  --color-error-container: #ffdad6;
  --color-background: #f7f9fb;
  --color-outline-variant: #c5c6cd;
  --color-surface: #f7f9fb;
  --color-primary-fixed: #d8e3fb;
  --color-tertiary: #001624;
  --color-surface-bright: #f7f9fb;
  --color-surface-container-lowest: #ffffff;
  --color-on-surface: #191c1e;
  --color-primary-container: #1e293b;
  --color-primary: #091426;
  --color-inverse-surface: #2d3133;
  --color-tertiary-fixed-dim: #89ceff;
  --color-surface-container-highest: #e0e3e5;
  --color-secondary-fixed-dim: #c3c7cb;
  --color-on-secondary-fixed: #171c1f;
  --color-tertiary-fixed: #c9e6ff;'''

# Replace colors in :root { ... }
content = re.sub(r':root\s*\{[^}]*--color-primary:.*?(?=\s*/* Fonts */)', ':root {\n  /* Stitch Minimal Palette */\n' + new_colors + '\n\n', content, flags=re.DOTALL)

# Fonts & Sizes (Hanken Grotesk and Vazirmatn)
fonts = '''  --font-display-lg: 'Hanken Grotesk', 'Vazirmatn', sans-serif;
  --font-body-md: 'Hanken Grotesk', 'Vazirmatn', sans-serif;
  --font-body-lg: 'Hanken Grotesk', 'Vazirmatn', sans-serif;
  --font-headline-md: 'Hanken Grotesk', 'Vazirmatn', sans-serif;
  --font-display-lg-mobile: 'Hanken Grotesk', 'Vazirmatn', sans-serif;
  --font-label-sm: 'Hanken Grotesk', 'Vazirmatn', sans-serif;'''

content = re.sub(r'/\*\s*Fonts\s*\*/.*?(?=\s*/\*\s*Radius\s*\*/)', '/* Fonts */\n' + fonts + '\n\n', content, flags=re.DOTALL)

# Add spacing variables if they don't exist in :root
spacings = '''
  /* Spacings */
  --spacing-gutter: 24px;
  --spacing-stack-lg: 32px;
  --spacing-margin-mobile: 16px;
  --spacing-stack-sm: 8px;
  --spacing-margin-desktop: 40px;
  --spacing-unit: 4px;
  --spacing-container-max: 1280px;
  --spacing-stack-md: 16px;
'''
if '/* Spacings */' not in content:
    content = content.replace('/* Radius */', spacings + '\n  /* Radius */')

# Now update @theme inline 
theme_block = '''@theme inline {
  --color-*: initial;
''' + '\n'.join(['  ' + line.strip().replace(':', ': var(').replace(';', ');') for line in new_colors.split('\n') if '--color-' in line]) + '''
  
''' + '\n'.join(['  ' + line.strip().replace(':', ': var(').replace(';', ');') for line in fonts.split('\n')]) + '''

  --spacing-gutter: var(--spacing-gutter);
  --spacing-stack-lg: var(--spacing-stack-lg);
  --spacing-margin-mobile: var(--spacing-margin-mobile);
  --spacing-stack-sm: var(--spacing-stack-sm);
  --spacing-margin-desktop: var(--spacing-margin-desktop);
  --spacing-unit: var(--spacing-unit);
  --spacing-container-max: var(--spacing-container-max);
  --spacing-stack-md: var(--spacing-stack-md);
  
  --radius-lg: var(--radius-lg);
  --radius-md: var(--radius-md);
  --radius-sm: var(--radius-sm);
  --radius-xl: var(--radius-xl);

  --animate-accordion-down: accordion-down 0.2s ease-out;
  --animate-accordion-up: accordion-up 0.2s ease-out;
  --animate-caret-blink: caret-blink 1.25s ease-out infinite;

  @keyframes accordion-down {
    from { height: 0; }
    to { height: var(--radix-accordion-content-height); }
  }
  @keyframes accordion-up {
    from { height: var(--radix-accordion-content-height); }
    to { height: 0; }
  }
  @keyframes caret-blink {
    0%, 70%, 100% { opacity: 1; }
    20%, 50% { opacity: 0; }
  }
}
'''
content = re.sub(r'@theme inline \{.*?\}\n', theme_block, content, flags=re.DOTALL)

with open('frontend/src/app.css', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated app.css")
