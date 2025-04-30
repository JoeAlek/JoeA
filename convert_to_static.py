import os
import re
import shutil

# Create github_static directory if it doesn't exist
os.makedirs('github_static/static', exist_ok=True)
os.makedirs('github_static/static/css', exist_ok=True)
os.makedirs('github_static/static/js', exist_ok=True)
os.makedirs('github_static/static/images', exist_ok=True)

# Copy static files
for root, dirs, files in os.walk('static'):
    for file in files:
        src_path = os.path.join(root, file)
        # Determine the relative path from 'static' directory
        rel_path = os.path.relpath(src_path, 'static')
        dst_path = os.path.join('github_static/static', rel_path)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        
        # Copy the file
        shutil.copy2(src_path, dst_path)
        print(f"Copied: {src_path} -> {dst_path}")

# Function to convert Jinja template to static HTML
def convert_template_to_static(template_path, static_path):
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace extends template
    content = re.sub(r'{%\s*extends\s+"layout.html"\s*%}', '', content)
    
    # Replace url_for with static paths
    content = re.sub(r'{{\s*url_for\(\'static\',\s*filename=\'(.*?)\'\)\s*}}', r'static/\1', content)
    
    # Replace internal links
    content = re.sub(r'{{\s*url_for\(\'index\'\)\s*}}', 'index.html', content)
    content = re.sub(r'{{\s*url_for\(\'features\'\)\s*}}', 'features.html', content)
    content = re.sub(r'{{\s*url_for\(\'about\'\)\s*}}', 'about.html', content)
    content = re.sub(r'{{\s*url_for\(\'status\'\)\s*}}', 'status.html', content)
    content = re.sub(r'{{\s*url_for\(\'command_list\'\)\s*}}', 'commands.html', content)
    
    # Process block content (remove block tags, keep content)
    content = re.sub(r'{%\s*block\s+content\s*%}(.*?){%\s*endblock\s*%}', r'\1', content, flags=re.DOTALL)
    
    # Process extra_head block (remove block tags, keep content)
    content = re.sub(r'{%\s*block\s+extra_head\s*%}(.*?){%\s*endblock\s*%}', r'\1', content, flags=re.DOTALL)
    
    # Process scripts block (remove block tags, keep content)
    content = re.sub(r'{%\s*block\s+scripts\s*%}(.*?){%\s*endblock\s*%}', r'\1', content, flags=re.DOTALL)
    
    # Read the layout template to use as a base
    with open('github_static/layout.html', 'r', encoding='utf-8') as f:
        layout = f.read()
    
    # Extract special sections
    extra_head_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
    extra_head = f'<style>{extra_head_match.group(1)}</style>' if extra_head_match else ''
    
    script_match = re.search(r'<script>(.*?)</script>', content, re.DOTALL)
    script = f'<script>{script_match.group(1)}</script>' if script_match else ''
    
    # Remove extracted sections from content to avoid duplication
    if extra_head_match:
        content = content.replace(f'<style>{extra_head_match.group(1)}</style>', '')
    if script_match:
        content = content.replace(f'<script>{script_match.group(1)}</script>', '')
    
    # Clean up any remaining Jinja syntax
    content = re.sub(r'{%.*?%}', '', content)
    content = re.sub(r'{{.*?}}', '', content)
    
    # Insert content into layout
    layout = layout.replace('<!-- extra_head content will be placed here for each page -->', extra_head)
    layout = layout.replace('<!-- content will be placed here for each page -->', content)
    layout = layout.replace('<!-- scripts content will be placed here for each page -->', script)
    
    # Write the final static HTML
    with open(static_path, 'w', encoding='utf-8') as f:
        f.write(layout)
    
    print(f"Converted: {template_path} -> {static_path}")

# Convert all template files in templates directory
template_files = {
    'templates/index.html': 'github_static/index.html',
    'templates/features.html': 'github_static/features.html',
    'templates/about.html': 'github_static/about.html',
    'templates/status.html': 'github_static/status.html'
}

for template_path, static_path in template_files.items():
    if os.path.exists(template_path):
        convert_template_to_static(template_path, static_path)
    else:
        print(f"Warning: {template_path} does not exist")

print("Conversion complete! Static files are in github_static directory")