import paramiko, io, time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("188.209.138.33", 22, "root", "pcJOm45Ijao1xlv", timeout=60)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err and "Warning" not in err and "auto imported" not in err: print("ERR:", err[:200])

# Wait for migrations to finish
print("=== Waiting for migrations ===")
time.sleep(60)
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml logs backend --tail=5 2>&1 | grep -E 'Starting development|System check|ERROR'")

# Create admin via file
print("\n=== Creating admin user ===")
script = """from common.models import User, Org, Profile
u = User.objects.create_superuser(phone='09136603902', email='admin2@localhost', password='admin123')
o = Org.objects.create(name='Default Org', is_active=True)
Profile.objects.create(user=u, org=o, is_active=True, role='ADMIN')
print('OK: user=' + u.phone + ' org=' + o.name)
"""
sftp = ssh.open_sftp()
sftp.putfo(io.BytesIO(script.encode()), "/tmp/seed_admin2.py")
sftp.close()

run("docker cp /tmp/seed_admin2.py bottlecrm-backend-1:/tmp/seed_admin2.py")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend bash -c 'python manage.py shell < /tmp/seed_admin2.py'")

# Verify
print("\n=== Verify users and orgs ===")
script2 = """from common.models import User, Org
print('Users:', User.objects.count())
print('Orgs:', Org.objects.count())
"""
sftp = ssh.open_sftp()
sftp.putfo(io.BytesIO(script2.encode()), "/tmp/check_db.py")
sftp.close()
run("docker cp /tmp/check_db.py bottlecrm-backend-1:/tmp/check_db.py")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend bash -c 'python manage.py shell < /tmp/check_db.py'")

ssh.close()
