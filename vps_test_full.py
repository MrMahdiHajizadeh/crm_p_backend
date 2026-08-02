import paramiko, io
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("188.209.138.33", 22, "root", "pcJOm45Ijao1xlv", timeout=60)

# Test API via fcrm domain
print("=== API login via fcrm.valerion.ir ===")
stdin,stdout,stderr = ssh.exec_command("""curl -s -X POST http://127.0.0.1/api/auth/phone-login/ -H 'Host: fcrm.valerion.ir' -H 'Content-Type: application/json' -d '{"phone":"09136603902","password":"admin123"}' -w '|HTTP:%{http_code}' | tail -c 200""")
print(stdout.read().decode().strip())

# Test frontend via crm domain
print("\n=== Frontend via crm.valerion.ir ===")
stdin,stdout,stderr = ssh.exec_command("""curl -s -I http://127.0.0.1/ -H 'Host: crm.valerion.ir' -w '|HTTP:%{http_code}' | head -10""")
print(stdout.read().decode().strip()[:300])

# Full frontend login test via crm domain
print("\n=== Full login flow via crm.valerion.ir (frontend -> backend) ===")
stdin,stdout,stderr = ssh.exec_command("""curl -s -X POST http://127.0.0.1/login -H 'Host: crm.valerion.ir' -H 'Content-Type: application/x-www-form-urlencoded' -d 'phone=09136603902&password=admin123' -w '|HTTP:%{http_code}' | tail -c 200""")
out = stdout.read().decode().strip()
# Check if we got a redirect (307) which means success
print(out[:300])

# Check Nginx config one more time
print("\n=== Nginx config for crm ===")
stdin,stdout,stderr = ssh.exec_command("grep -A30 'server_name crm.valerion.ir' /etc/nginx/sites-available/crm.valerion.ir")
print(stdout.read().decode().strip())

ssh.close()
