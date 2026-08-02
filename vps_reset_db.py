import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("188.209.138.33", 22, "root", "pcJOm45Ijao1xlv", timeout=60)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err and "Warning" not in err: print("ERR:", err[:200])

print("=== 1. Check current DB state ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend bash -c 'python manage.py shell -c \"from common.models import User; print(f(\\\"Users: {User.objects.count()}\\\")); from common.models import Org; print(f(\\\"Orgs: {Org.objects.count()}\\\"))\"' 2>&1")

print("\n=== 2. Reset database (recreate) ===")
# Stop backend first
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml stop backend celery-worker celery-beat 2>&1")

# Drop and recreate DB
stdin,stdout,stderr = ssh.exec_command("docker exec bottlecrm-db-1 sh -c \"psql -U postgres -c 'DROP DATABASE IF EXISTS crm_db;' && psql -U postgres -c 'CREATE DATABASE crm_db OWNER crm_user;'\" 2>&1")
print(stdout.read().decode().strip())
err = stderr.read().decode().strip()
if err: print("DB ERR:", err[:200])

# Also need to re-run init SQL for crm_user permissions
run("docker exec bottlecrm-db-1 sh -c 'psql -U postgres -d crm_db -c \"GRANT ALL ON SCHEMA public TO crm_user;\"' 2>&1")

print("\n=== 3. Run migrations ===")
# Start backend (it will run migrations)
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml up -d backend 2>&1")

import time
print("  Waiting 60s for migrations...")
time.sleep(60)

print("\n=== 4. Check migrations applied ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml logs backend --tail=10 2>&1 | grep -E 'Applying|migration|OK|System check|Starting development'")

print("\n=== 5. Re-create admin user ===")
script = """from common.models import User, Org, Profile, Organization
user = User.objects.create_superuser(phone='09136603902', email='admin2@localhost', password='admin123')
org = Org.objects.create(name='Default Org', is_active=True)
Profile.objects.create(user=user, org=org, is_active=True, role='ADMIN')
print(f'Created: user={user.phone}, org={org.name}')
"""
import io
sftp = ssh.open_sftp()
sftp.putfo(io.BytesIO(script.encode()), "/tmp/seed_admin.py")
sftp.close()
run("docker cp /tmp/seed_admin.py bottlecrm-backend-1:/tmp/seed_admin.py")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend bash -c 'python manage.py shell < /tmp/seed_admin.py'")

print("\n=== 6. Start celery ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml up -d celery-worker celery-beat 2>&1")

print("\n=== 7. Verify ===")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend bash -c \"python manage.py shell -c 'from common.models import User, Org; print(f(\\\"Users: {User.objects.count()}\\\")); print(f(\\\"Orgs: {Org.objects.count()}\\\"))'\" 2>&1")

ssh.close()
print("\n=== Fresh database ready ===")
