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

User = get_user_model()
org = Org.objects.first()

if not org:
    org = Org.objects.create(name="Default Org", company_name="Default Org")
    print("Created Default Org.")

assigned_count = 0
for user in User.objects.all():
    if not Profile.objects.filter(user=user, org=org).exists():
        role = "ADMIN" if user.is_superuser else "USER"
        Profile.objects.create(
            user=user,
            org=org,
            role=role,
            is_active=True,
            is_organization_admin=user.is_superuser,
            has_sales_access=True,
            has_marketing_access=True
        )
        assigned_count += 1

print(f"Assigned {assigned_count} users to the organization '{org.name}'.")
"""
    # Write script to remote /tmp
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/assign_all.py', 'w') as f:
        f.write(script)
    sftp.close()

    run_cmd(ssh, "docker cp /tmp/assign_all.py bottlecrm-backend-1:/tmp/assign_all.py")
    cmd = "cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend sh -c 'python manage.py shell < /tmp/assign_all.py'"
    run_cmd(ssh, cmd)

    ssh.close()
    print("Done!")
except Exception as e:
    print(f"Error: {e}")
