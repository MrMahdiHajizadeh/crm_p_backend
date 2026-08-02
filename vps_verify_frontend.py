import paramiko, io
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("188.209.138.33", 22, "root", "pcJOm45Ijao1xlv", timeout=60)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err and "Warning" not in err and "/docker-entrypoint" not in err: print("ERR:", err[:200])

print("=== 1. Verify frontend container ===")
run("docker ps --filter name=bottlecrm-frontend --format '{{.Status}}'")

print("\n=== 2. Verify API URL baked into frontend JS ===")
run("docker exec bottlecrm-frontend-1 sh -c 'grep -rl \"fcrm.valerion.ir\" /app/build/ 2>/dev/null | head -3' || echo 'Not found in build files'")
run("docker exec bottlecrm-frontend-1 sh -c 'grep -rl \"PUBLIC_DJANGO\" /app/build/ 2>/dev/null | head -3' || echo 'No PUBLIC_DJANGO refs'")

# Search for any API URL pattern
run("docker exec bottlecrm-frontend-1 sh -c 'grep -roh \"http[s]*://[^/\\\"]*\" /app/build/*.js 2>/dev/null | sort -u | grep -i \"api\\|valerion\\|8000\\|3000\" | head -10' || echo 'No API URLs found'")

print("\n=== 3. Test login via Nginx ===")
stdin,stdout,stderr = ssh.exec_command("curl -s -X POST http://127.0.0.1/api/auth/phone-login/ -H 'Content-Type: application/json' -H 'Origin: http://crm.valerion.ir' -d '{\"phone\":\"09136603902\",\"password\":\"admin123\"}' | python3 -c \"import sys,json; d=json.load(sys.stdin); print('ORG:', d.get('current_org',{}).get('name','NO ORG'), '| TOKEN:', d.get('access_token','NO TOKEN')[:20]+'...')\" 2>&1")
print(stdout.read().decode().strip())

print("\n=== 4. Check if Nginx routes frontend correctly ===")
stdin,stdout,stderr = ssh.exec_command("curl -s -I http://127.0.0.1/ 2>&1 | head -5")
print(stdout.read().decode().strip())

print("\n=== 5. Frontend serving content ===")
stdin,stdout,stderr = ssh.exec_command("curl -s http://127.0.0.1/ 2>&1 | head -c 200")
print(stdout.read().decode().strip()[:200])

ssh.close()
