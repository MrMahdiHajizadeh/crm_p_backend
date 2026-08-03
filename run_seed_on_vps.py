#!/usr/bin/env python3
"""
Seed fake Persian CRM data on the VPS via Docker exec.
Copies seed script to the container and runs it.
"""
import subprocess
import sys

VPS_IP = "87.107.108.69"
VPS_PASS = "IoC275YMVRF9e7W"
SEED_SCRIPT = "seed_persian_data.py"


def run_remote(cmd, capture=True):
    full_cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        f"root@{VPS_IP}",
        cmd
    ]
    result = subprocess.run(full_cmd, capture_output=capture, text=True, timeout=120)
    return result


def scp_file(local_path, remote_path):
    cmd = [
        "scp",
        "-o", "StrictHostKeyChecking=no",
        local_path,
        f"root@{VPS_IP}:{remote_path}"
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)


def main():
    print("=" * 60)
    print("  CRM VPS Fake Data Seeder")
    print("=" * 60)

    # Step 1: Find container name
    print("\n[1] Finding backend Docker container...")
    r = run_remote("docker ps --format '{{.Names}}' | grep -i back | head -1")
    if r.returncode != 0:
        print(f"SSH failed: {r.stderr}")
        sys.exit(1)
    container = r.stdout.strip()
    if not container:
        r = run_remote("docker ps --format '{{.Names}}' | head -5")
        print(f"Available containers:\n{r.stdout}")
        container = r.stdout.strip().split('\n')[0]
    print(f"    Container: {container}")

    # Step 2: Copy seed script to VPS
    print(f"\n[2] Copying {SEED_SCRIPT} to VPS...")
    r = scp_file(SEED_SCRIPT, f"/tmp/{SEED_SCRIPT}")
    if r.returncode != 0:
        print(f"SCP failed: {r.stderr}")
        sys.exit(1)
    print("    Done.")

    # Step 3: Copy from VPS into container
    print(f"\n[3] Copying script into container {container}...")
    r = run_remote(f"docker cp /tmp/{SEED_SCRIPT} {container}:/app/{SEED_SCRIPT}")
    if r.returncode != 0:
        print(f"docker cp failed: {r.stderr}")
        sys.exit(1)
    print("    Done.")

    # Step 4: Run seed script inside container
    print("\n[4] Running seed script inside container...")
    r = run_remote(
        f"docker exec {container} python /app/{SEED_SCRIPT}",
        capture=True
    )
    print(r.stdout)
    if r.stderr:
        print("[STDERR]:", r.stderr[:2000])
    if r.returncode != 0:
        print("\n[ERROR] Seed script failed!")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Fake data seeded successfully!")

    # Step 5: Quick verification
    print("\n[5] Verifying data counts...")
    verify_cmd = """docker exec {} python -c "
import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'crm.settings'
django.setup()
from leads.models import Lead
from contacts.models import Contact
from accounts.models import Account
from opportunity.models import Opportunity
from tasks.models import Task
from invoices.models import Invoice
from leads.models import InteractionLog
print(f'Leads: {{Lead.objects.count()}}')
print(f'Contacts: {{Contact.objects.count()}}')
print(f'Accounts: {{Account.objects.count()}}')
print(f'Opportunities: {{Opportunity.objects.count()}}')
print(f'Tasks: {{Task.objects.count()}}')
print(f'InteractionLogs: {{InteractionLog.objects.count()}}')
print(f'Invoices: {{Invoice.objects.count()}}')
" """.format(container)
    r = run_remote(verify_cmd)
    print(r.stdout)
    if r.stderr:
        print(r.stderr[:500])

    print("\n" + "=" * 60)
    print("  All done! Login at: https://front.crm.valerion.ir")
    print("  Admin: 09120000000 / admin123")
    print("  Team members: 0912XXXXXXX / test1234")
    print("=" * 60)


if __name__ == "__main__":
    main()
