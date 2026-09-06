import os
import glob

for f in glob.glob('frontend/**/*.py', recursive=True):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    new_content = content.replace('use_container_width=True', 'width="stretch"')
    new_content = new_content.replace('use_container_width=False', 'width="content"')
    
    if content != new_content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Updated {f}")
