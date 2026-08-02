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

    # First, run the seed_data command inside the backend container
    print("Seeding database (this might take a few minutes)...")
    seed_cmd = "cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend python manage.py seed_data"
    run_cmd(ssh, seed_cmd)

    # Next, create/update the requested superuser
    print("Creating/Updating requested admin user...")
    create_user_script = """
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm.settings")
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
phone = '09136603902'
password = 'admin123'
if not User.objects.filter(phone=phone).exists():
    user = User.objects.create_superuser(phone=phone, password=password)
    print("Created admin user: " + phone)
else:
    user = User.objects.get(phone=phone)
    user.set_password(password)
    user.is_active = True
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print("Updated admin user: " + phone)
"""
    # Write script to remote /tmp
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/create_admin.py', 'w') as f:
        f.write(create_user_script)
    sftp.close()

    # Execute script inside container
    cmd = "cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend python /tmp/create_admin.py"
    # Actually wait, we need to copy the script into the container first, or pipe it.
    # It's easier to just run python manage.py shell -c "..."
    cmd = '''cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); phone='09136603902'; password='admin123'; user=User.objects.filter(phone=phone).first(); user=User.objects.create_superuser(phone=phone, password=password) if not user else user; user.set_password(password); user.is_active=True; user.is_staff=True; user.is_superuser=True; user.save(); print('User created/updated!')"'''
    run_cmd(ssh, cmd)

    ssh.close()
    print("Done!")
except Exception as e:
    print(f"Error: {e}")
