"""
Replace the deployed frontend and backend on the VPS with the current local code.

VPS: 87.107.108.69  (root / IoC275YMVRF9e7W)
Frontend: https://front.crm.valerion.ir  -> port 3000
Backend:  https://back.crm.valerion.ir   -> port 8000

What it does:
1. Builds a tar.gz of backend/, frontend/, docker/, Dockerfile, docker-compose.vps.yml, .env.docker
2. Uploads it to the VPS and extracts into /opt/bottlecrm (replacing the old files).
3. docker compose up -d --build --force-recreate  (rebuilds backend + frontend images)
4. Waits, then prints container status + recent logs for verification.
"""
import paramiko
import os
import tarfile
import io
import time

HOST = "87.107.108.69"
PORT = 22
USER = "root"
PASS = "IoC275YMVRF9e7W"
LOCAL_BASE = r"c:\Users\mrmah\OneDrive\Desktop\CRM p\Django-CRM"
REMOTE_DIR = "/opt/bottlecrm"

# Directories we never want to upload to the server
EXCLUDE_DIRS = {
    '.venv', '__pycache__', '.git', 'media', 'staticfiles', 'htmlcov',
    '.pytest_cache', 'node_modules', 'mcp_server', 'mobile', '.svelte-kit',
    'build', '.pnpm-store', '.svelte-kit', 'dist', 'coverage',
}
# Files we never want to upload to the server (local-only or regenerated)
EXCLUDE_FILES = {
    'server.log', 'security_audit.log', '.coverage', 'coverage.xml',
    'db.sqlite3', '.env', 'ruff.toml',
}
EXCLUDE_EXTS = {'.pyc', '.pyo'}


def connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=60)
    return ssh


def run(ssh, cmd, quiet=False):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=600)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if not quiet:
        if out:
            print(out)
        if err:
            print("ERR:", err)
    return out, err


def build_tar():
    print("Building archive of local code...")
    buf = io.BytesIO()
    tf = tarfile.open(fileobj=buf, mode='w:gz')

    # Top-level files
    for f in ['Dockerfile', 'docker-compose.vps.yml', '.env.docker']:
        path = os.path.join(LOCAL_BASE, f)
        if os.path.exists(path):
            tf.add(path, arcname=f)
            print("  +", f)

    # Folders
    for folder in ['docker', 'backend', 'frontend']:
        folder_dir = os.path.join(LOCAL_BASE, folder)
        if not os.path.exists(folder_dir):
            print("  ! missing", folder)
            continue
        count = 0
        for root, dirs, files in os.walk(folder_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for fn in files:
                if fn in EXCLUDE_FILES or os.path.splitext(fn)[1] in EXCLUDE_EXTS:
                    continue
                path = os.path.join(root, fn)
                arcname = os.path.relpath(path, LOCAL_BASE).replace('\\', '/')
                tf.add(path, arcname=arcname)
                count += 1
        print(f"  + {folder}/ ({count} files)")

    tf.close()
    data = buf.getvalue()
    print(f"Archive built: {len(data)/1024/1024:.2f} MB\n")
    return data


def main():
    tar_data = build_tar()

    print("Connecting to VPS...")
    ssh = connect()

    print("Backing up current deployment config...")
    run(ssh, f"cp {REMOTE_DIR}/.env.docker {REMOTE_DIR}/.env.docker.bak 2>/dev/null; echo ok", quiet=True)
    run(ssh, f"cp {REMOTE_DIR}/docker-compose.vps.yml {REMOTE_DIR}/docker-compose.vps.yml.bak 2>/dev/null; echo ok", quiet=True)

    print("Uploading archive...")
    sftp = ssh.open_sftp()
    sftp.putfo(io.BytesIO(tar_data), '/tmp/deploy_replace.tar.gz')
    sftp.close()

    print("Extracting (replacing existing files)...")
    # Extract on top of the existing dir so the bind-mounted postgres data etc stays.
    run(ssh, f"mkdir -p {REMOTE_DIR} && cd {REMOTE_DIR} && tar -xzf /tmp/deploy_replace.tar.gz && rm /tmp/deploy_replace.tar.gz")

    print("\nRebuilding & restarting backend + frontend containers...")
    # Build both, force-recreate so new code is picked up. DB/Redis are untouched.
    run(ssh, f"cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml up -d --build --force-recreate backend frontend 2>&1")

    print("\nWaiting 30s for containers to settle...")
    time.sleep(30)

    print("\n=== Container status ===")
    run(ssh, f'cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml ps 2>&1')

    print("\n=== Backend logs (tail) ===")
    run(ssh, f'cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml logs backend --tail=15 2>&1')

    print("\n=== Frontend logs (tail) ===")
    run(ssh, f'cd {REMOTE_DIR} && docker compose -f docker-compose.vps.yml logs frontend --tail=15 2>&1')

    print("\n=== Quick HTTP checks ===")
    run(ssh, 'curl -sk -o /dev/null -w "front(%{http_code}) " https://front.crm.valerion.ir/ || echo "front FAIL"')
    run(ssh, 'curl -sk -o /dev/null -w "back(%{http_code}) " https://back.crm.valerion.ir/api/schema/ || echo "back FAIL"')

    ssh.close()
    print("\nDone. Frontend: https://front.crm.valerion.ir  |  Backend: https://back.crm.valerion.ir")


if __name__ == "__main__":
    main()