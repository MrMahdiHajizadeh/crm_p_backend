import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("188.209.138.33", 22, "root", "pcJOm45Ijao1xlv", timeout=60)

# Check CORS config
print("=== CORS settings ===")
stdin,stdout,stderr = ssh.exec_command("grep -E 'CORS_ALLOW|CSRF_TRUSTED' /opt/bottlecrm/.env.docker")
print(stdout.read().decode().strip())

# Revert CORS to allow all for now
print("\n=== Fixing CORS ===")
stdin,stdout,stderr = ssh.exec_command("sed -i 's/^CORS_ALLOW_ALL=.*/CORS_ALLOW_ALL=True/' /opt/bottlecrm/.env.docker")
print("Set CORS_ALLOW_ALL=True")

# Restart backend
print("\n=== Restarting backend ===")
stdin,stdout,stderr = ssh.exec_command("cd /opt/bottlecrm && docker compose -f docker-compose.vps.yml up -d --force-recreate backend 2>&1")
out = stdout.read().decode().strip()
print(out[-200:] if len(out) > 200 else out)

ssh.close()
