import paramiko, io
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("188.209.138.33", 22, "root", "pcJOm45Ijao1xlv", timeout=60)

script = """from common.models import User, Org, Profile
u = User.objects.get(phone="09136603902")
org, c = Org.objects.get_or_create(name="Default Org", defaults={"is_active": True})
print("CREATED org" if c else "EXISTING org", org.name, org.id)
profile, pc = Profile.objects.get_or_create(user=u, org=org, defaults={"is_active": True, "role": "ADMIN"})
print("CREATED profile" if pc else "EXISTING profile", "role=ADMIN")
"""

sftp = ssh.open_sftp()
sftp.putfo(io.BytesIO(script.encode()), "/tmp/create_org.py")
sftp.close()

stdin,stdout,stderr = ssh.exec_command("docker cp /tmp/create_org.py bottlecrm-backend-1:/tmp/create_org.py 2>&1 && cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml exec -T backend bash -c 'python manage.py shell < /tmp/create_org.py' 2>&1")
out = stdout.read().decode()
print(out)

# Test login
print("\n=== Retest login ===")
stdin,stdout,stderr = ssh.exec_command("""curl -s -X POST http://127.0.0.1:8000/api/auth/phone-login/ -H "Content-Type: application/json" -d '{"phone":"09136603902","password":"admin123"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('LOGIN OK - org:', d.get('current_org',{}).get('name','NO ORG'))" 2>&1""")
print(stdout.read().decode().strip())

ssh.close()
