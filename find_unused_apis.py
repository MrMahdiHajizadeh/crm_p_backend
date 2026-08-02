import os
import re
import subprocess

backend_urls_file = 'dump_urls.py'
result = subprocess.run([os.path.join(os.getcwd(), 'backend', '.venv', 'Scripts', 'python.exe'), 'dump_urls.py'], capture_output=True, text=True)
backend_urls = [line.strip() for line in result.stdout.split('\n') if line.strip() and line.startswith('api/')]

def url_to_regex(url):
    # api/cases/approvals/<str:pk>/approve/ -> api/cases/approvals/[^/]+/approve/?
    # Convert django URL patterns to regex to search in JS/Dart code
    # We replace <...> with [^/]+ (meaning anything except slash)
    # Because JS will have ${id} or similar
    pattern = re.sub(r'<[^>]+>', r'[^/\'"`]+', url)
    return pattern

url_patterns = [(url, url_to_regex(url)) for url in backend_urls]

client_dirs = [
    os.path.join(os.getcwd(), 'frontend', 'src'),
    os.path.join(os.getcwd(), 'mobile', 'lib'),
    os.path.join(os.getcwd(), 'mcp_server')
]

client_files = []
for d in client_dirs:
    for root, _, files in os.walk(d):
        for file in files:
            if file.endswith(('.js', '.svelte', '.ts', '.dart', '.py')):
                client_files.append(os.path.join(root, file))

client_code = ""
for file in client_files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            client_code += f.read() + "\n"
    except Exception:
        pass

crud_entities = ['accounts', 'leads', 'contacts', 'opportunities', 'cases', 'tasks', 'invoices']

unused_urls = []
for url, pattern in url_patterns:
    is_used = False
    
    # Check if pattern matches in the code
    # We remove the trailing slash for regex matching to be safe
    search_pattern = pattern.rstrip('/')
    
    # Try searching with api/
    if re.search(search_pattern, client_code):
        is_used = True
    # Try searching without api/ (in case frontend uses apiRequest('/cases/...'))
    elif search_pattern.startswith('api/'):
        without_api = search_pattern[4:]
        if re.search(r'[\'"`/]'+without_api, client_code):
            is_used = True
            
    if not is_used:
        for entity in crud_entities:
            if url.startswith(f'api/{entity}/'):
                rest = url[len(f'api/{entity}/'):]
                if rest in ['', '<str:pk>/', '<uuid:pk>/', '<uuid:invoice_id>/', 'comment/<str:pk>/', 'attachment/<str:pk>/']:
                    is_used = True
                    break
                if entity == 'invoices' and rest in ['<uuid:invoice_id>/comments/', '<uuid:invoice_id>/attachments/']:
                    is_used = True
                    break
                
    if not is_used:
        unused_urls.append(url)

print("Found unused API endpoints:")
for url in unused_urls:
    print(url)
