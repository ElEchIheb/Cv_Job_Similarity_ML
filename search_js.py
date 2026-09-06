import re
data = open(r'.venv\Lib\site-packages\streamlit\static\static\js\main.RoKzF5Lw.js', encoding='utf8').read()
matches = set(re.findall(r'data-testid="([^"]+)"', data))
print('\n'.join(sorted([m for m in matches if 'Sidebar' in m or 'Header' in m or 'st' in m or 'collapse' in m.lower()])))
