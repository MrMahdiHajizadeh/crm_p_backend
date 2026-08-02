"""Create admin user and verify frontend API URL on VPS"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("188.209.138.33", 22, "root", "pcJOm45Ijao1xlv", timeout=60, banner_timeout=60, auth_timeout=60)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err: print("ERR:", err)
    return out

# Write admin creation script to VPS HOST via SFTP
print("=== Creating admin user ===")
script = """from common.models import User
user, created = User.objects.get_or_create(
    phone="09136603902",
    defaults={"email": "admin2@localhost", "is_superuser": True, "is_staff": True, "is_active": True},
)
user.set_password("admin123")
user.is_superuser = True
user.is_staff = True
user.save()
print("CREATED" if created else "UPDATED")
"""

sftp = ssh.open_sftp()
sftp.putfo(__import__("io").BytesIO(script.encode()), "/tmp/create_admin.py")
sftp.close()

# Copy into container and run
run("docker cp /tmp/create_admin.py bottlecrm-backend-1:/tmp/create_admin.py")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend bash -c 'python manage.py shell < /tmp/create_admin.py'")

# Verify user
print("\n=== Verify user ===")
script2 = """from common.models import User
u = User.objects.get(phone="09136603902")
print(f"Email: {u.email}, Superuser: {u.is_superuser}, Active: {u.is_active}")
"""
sftp = ssh.open_sftp()
sftp.putfo(__import__("io").BytesIO(script2.encode()), "/tmp/verify_admin.py")
sftp.close()

run("docker cp /tmp/verify_admin.py bottlecrm-backend-1:/tmp/verify_admin.py")
run("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend bash -c 'python manage.py shell < /tmp/verify_admin.py'")

# Verify frontend config
print("\n=== Compose API URL ===")
run("grep PUBLIC_DJANGO_API_URL /opt/bottlecrm/docker-compose.vps.yml")

print("\n=== Frontend container ===")
run("docker logs bottlecrm-frontend-1 --tail=5 2>/dev/null")

print("\n=== Runtime API URL in frontend ===")
run('docker exec bottlecrm-frontend-1 node -e "console.log(process.env.PUBLIC_DJANGO_API_URL || \'NOT SET\')" 2>/dev/null')

ssh.close()
print("\n=== Done ===")
print("Login: 09136603902 / admin123")
print("Frontend: http://crm.valerion.ir")
print("Admin: http://fcrm.valerion.ir/admin/")
