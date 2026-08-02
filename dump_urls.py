import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
import django
django.setup()
from django.urls import get_resolver
resolver = get_resolver()
urls = set()
def get_urls(r, pre=''):
    for p in r.url_patterns:
        if hasattr(p, 'url_patterns'):
            get_urls(p, pre + str(p.pattern))
        else:
            urls.add(pre + str(p.pattern))
get_urls(resolver)
for u in sorted(urls):
    print(u)
