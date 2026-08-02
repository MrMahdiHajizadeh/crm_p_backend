import paramiko

HOST = "87.107.108.69"
PORT = 22
USER = "root"
PASS = "IoC275YMVRF9e7W"

def run_cmd(ssh, cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out.encode('cp1252', errors='replace').decode('cp1252'))
    if err: print("ERR:", err.encode('cp1252', errors='replace').decode('cp1252'))
    return out, err

try:
    print("Connecting to server...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=60)

    script = """
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm.settings")
django.setup()

from django.contrib.auth import get_user_model
from common.models import Profile, Org
from common.serializer import ShowOrganizationListSerializer

User = get_user_model()
user = User.objects.get(phone='09136603902')

profile_list = Profile.objects.filter(user=user)
print("Profile list count:", profile_list.count())
for p in profile_list:
    print("Profile:", p.id, p.org.name, "Active:", p.is_active)

serializer = ShowOrganizationListSerializer(profile_list, many=True)
print("Serializer Data:", serializer.data)

from rest_framework.test import APIRequestFactory
from common.views.organization_views import OrgProfileCreateView

factory = APIRequestFactory()
request = factory.get('/api/org/')
request.user = user

view = OrgProfileCreateView.as_view()
response = view(request)
print("GET /api/org/ response:", response.status_code, response.data)
"""
    # Write script to remote /tmp
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/debug_org.py', 'w') as f:
        f.write(script)
    sftp.close()

    run_cmd(ssh, "docker cp /tmp/debug_org.py bottlecrm-backend-1:/tmp/debug_org.py")
    cmd = "cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend sh -c 'python manage.py shell < /tmp/debug_org.py'"
    run_cmd(ssh, cmd)

    ssh.close()
    print("Done!")
except Exception as e:
    print(f"Error: {e}")
