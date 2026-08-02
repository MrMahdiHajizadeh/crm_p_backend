import paramiko, io
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("188.209.138.33", 22, "root", "pcJOm45Ijao1xlv", timeout=60)

# 1. Test CORS preflight from frontend domain
print("=== CORS preflight ===")
stdin,stdout,stderr = ssh.exec_command("""curl -s -I -X OPTIONS http://127.0.0.1:8000/api/auth/phone-login/ -H "Origin: http://crm.valerion.ir" -H "Access-Control-Request-Method: POST" 2>&1 | grep -iE 'access-control|HTTP'""")
print(stdout.read().decode().strip())

# 2. Check what the frontend actually sends
print("\n=== Frontend container check ===")
stdin,stdout,stderr = ssh.exec_command("docker inspect bottlecrm-frontend-1 --format '{{.Config.Image}}|{{.Created}}'")
print(stdout.read().decode().strip())

# 3. Check if the frontend was built with correct URL
print("\n=== Frontend build check ===")
stdin,stdout,stderr = ssh.exec_command("docker exec bottlecrm-frontend-1 sh -c 'strings /app/build/index.js 2>/dev/null | grep -o \"http[s]*://fcrm.valerion.ir\" | head -3' 2>/dev/null")
out = stdout.read().decode().strip()
print("API URLs in build:", out if out else "NOT FOUND - may be using default")

# 4. Check compose API URL
print("\n=== Compose config ===")
stdin,stdout,stderr = ssh.exec_command("grep -A2 'PUBLIC_DJANGO' /opt/bottlecrm/docker-compose.vps.yml")
print(stdout.read().decode().strip())

ssh.close()
