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

    print("Checking profiles for user...")
    script = """
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm.settings")
django.setup()
from django.contrib.auth import get_user_model
from common.models import Org, Profile
from common.serializer import UserDetailSerializer

User = get_user_model()
phone = '09136603902'

user = User.objects.filter(phone=phone).first()
if not user:
    print("User not found!")
    exit(1)

profiles = Profile.objects.filter(user=user)
print("Profiles for user:", list(profiles.values('id', 'org__name', 'is_active', 'role')))

data = UserDetailSerializer(user).data
print("UserDetailSerializer organizations:", data.get('organizations'))
"""
    # Write script to remote /tmp
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/fix_org.py', 'w') as f:
        f.write(script)
    sftp.close()

    run_cmd(ssh, "docker cp /tmp/fix_org.py bottlecrm-backend-1:/tmp/fix_org.py")
    cmd = "cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend sh -c 'python manage.py shell < /tmp/fix_org.py'"
    run_cmd(ssh, cmd)

    ssh.close()
    print("Done!")
except Exception as e:
    print(f"Error: {e}")
