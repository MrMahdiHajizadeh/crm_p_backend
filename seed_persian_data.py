import os
import random
from datetime import timedelta
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
django.setup()

from django.utils import timezone
from common.models import User, Org, Profile
from leads.models import Lead, InteractionLog
from contacts.models import Contact
from accounts.models import Account
from opportunity.models import Opportunity
from tasks.models import Task
from invoices.models import Invoice

FIRST_NAMES = ["رضا", "سارا", "علی", "مریم", "امیرحسین", "کامران", "الهام", "حامد", "فاطمه", "مهدی", "نیلوفر", "احسان", "زهرا", "محمد", "آرش", "سپیده", "حسین", "سمیرا", "پیمان", "مژگان"]
LAST_NAMES = ["محمدی", "احمدی", "حسینی", "عباسی", "رضایی", "کاظمی", "بهرامی", "نوری", "شریفی", "رستمی", "مرادی", "کریمی", "صادقی", "موسوی", "حیدری", "قاسمی", "طاهری", "نجفی", "ابراهیمی", "سعیدی"]
COMPANY_PREFIXES = ["شرکت فناوری", "گروه صنعتی", "صنایع دارویی", "شرکت داده‌پردازان", "بازرگانی و توسعه", "مجتمع پتروشیمی", "شرکت مهندسی", "گروه تجاری", "صنایع غذایی", "شرکت ساختمانی"]
COMPANY_NAMES = ["عمارت پارس", "آریا فولاد", "سپهر سلامت", "پاسارگاد", "صادقین", "البرز", "پردیس دیجتال", "کیا صنعت", "سیستک", "زاگرس", "خلیج فارس", "نگین شرق", "تمدن آریایی", "توسعه آفتاب", "فن‌آوران نوآوران"]
CITIES = ["تهران", "اصفهان", "شیراز", "مشهد", "تبریز", "کرج", "اهواز", "رشت", "قم", "یزد"]
SOURCES = ["وب‌سایت", "کمپین اینستاگرام", "نمایشگاه بین‌المللی", "ارتباط تلفنی", "معرفی مشتریان", "ارتباط لینکدین", "تبلیغات گوگل"]
LEAD_STATUSES = ["NEW", "IN_PROCESS", "CONVERTED", "RECYCLED", "CLOSED"]
LEAD_RATINGS = ["HOT", "WARM", "COLD"]
STAGES = ["QUALIFICATION", "NEEDS_ANALYSIS", "PROPOSAL", "NEGOTIATION", "CLOSED_WON", "CLOSED_LOST"]
TASK_PRIORITIES = ["Low", "Medium", "High"]
TASK_STATUSES = ["New", "In Progress", "Completed", "Pending"]
INVOICE_STATUSES = ["Draft", "Sent", "Viewed", "Paid", "Partially_Paid", "Overdue"]

def seed_large_persian_crm_data():
    print("[INFO] Starting Large Persian CRM Data Seeding...")

    # 1. Org setup
    org = Org.objects.first()
    if not org:
        org = Org.objects.create(name="سازمان توسعه عمارت")

    # 2. Main Admin User
    admin_user = User.objects.filter(phone='09120000000').first()
    if not admin_user:
        admin_user = User.objects.create(
            phone='09120000000',
            email='admin@example.com',
            name='رضا محمدی (مدیر کل)',
            is_staff=True,
            is_superuser=True
        )
        admin_user.set_password('admin123')
        admin_user.save()

    admin_profile, _ = Profile.objects.get_or_create(user=admin_user, org=org, defaults={'role': 'ADMIN'})

    # 3. Create 10 Team Member Profiles
    team_members_data = [
        {"phone": "09121111111", "email": "sara.ahmadi@example.com", "name": "سارا احمدی (سرپرست فروش)", "role": "ADMIN"},
        {"phone": "09122222222", "email": "ali.hosseini@example.com", "name": "علی حسینی (ارشد فروش)", "role": "USER"},
        {"phone": "09123333333", "email": "maryam.abbasi@example.com", "name": "مریم عباسی (پشتیبانی فنی)", "role": "USER"},
        {"phone": "09124444444", "email": "amir.rezaei@example.com", "name": "امیرحسین رضایی (کارشناس دیجیتال)", "role": "USER"},
        {"phone": "09125555555", "email": "kamran.kazemi@example.com", "name": "کامران کاظمی (فروش B2B)", "role": "USER"},
        {"phone": "09126666666", "email": "elham.bahrami@example.com", "name": "الهام بهرامی (پیگیری و CRM)", "role": "USER"},
        {"phone": "09127777777", "email": "hamed.noori@example.com", "name": "حامد نوری (فروش سازمانی)", "role": "USER"},
        {"phone": "09128888888", "email": "fatemeh.sharifi@example.com", "name": "فاطمه شریفی (پشتیبانی مشتریان)", "role": "USER"},
        {"phone": "09129999999", "email": "mehdi.rostami@example.com", "name": "مهدی رستمی (کارشناس بازاریابی)", "role": "USER"},
    ]

    profiles = [admin_profile]
    for tm in team_members_data:
        u, _ = User.objects.get_or_create(
            phone=tm["phone"],
            defaults={"email": tm["email"], "name": tm["name"]}
        )
        u.name = tm["name"]
        u.set_password("test1234")
        u.save()

        p, _ = Profile.objects.get_or_create(user=u, org=org, defaults={"role": tm["role"]})
        profiles.append(p)

    # 4. Create 25 Accounts (Companies)
    created_accounts = []
    for i in range(25):
        c_name = f"{random.choice(COMPANY_PREFIXES)} {random.choice(COMPANY_NAMES)} #{i+1}"
        phone = f"021{random.randint(88000000, 88999999)}"
        email = f"info{i+1}@company{i+1}.ir"
        city = random.choice(CITIES)

        acc, _ = Account.objects.get_or_create(
            org=org,
            name=c_name,
            defaults={
                "phone": phone,
                "email": email,
                "city": city,
                "website": f"https://company{i+1}.ir"
            }
        )
        created_accounts.append(acc)

    # 5. Create 30 Contacts
    created_contacts = []
    for i in range(30):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        phone = f"0912{random.randint(1000000, 9999999)}"
        email = f"contact{i+100}@domain{i+100}.ir"
        acc = random.choice(created_accounts)

        cnt, _ = Contact.objects.get_or_create(
            org=org,
            email=email,
            defaults={
                "first_name": fn,
                "last_name": ln,
                "phone": phone,
                "account": acc
            }
        )
        created_contacts.append(cnt)

    # 6. Create 50 Leads
    created_leads = []
    for i in range(50):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        phone = f"0935{random.randint(1000000, 9999999)}"
        email = f"lead{i+1}@client{i+1}.ir"
        company = f"{random.choice(COMPANY_PREFIXES)} {random.choice(COMPANY_NAMES)}"
        status = random.choice(LEAD_STATUSES)
        rating = random.choice(LEAD_RATINGS)
        source = random.choice(SOURCES)
        city = random.choice(CITIES)
        assigned_profile = random.choice(profiles)

        title = f"استعلام و خرید پروژه شماره {i+1} ({company})"
        desc = f"درخواست خرید و استعلام قیمت برای پروژه سازمانی {i+1}. پیگیری توسط {assigned_profile.user.name} انجام می‌شود."

        lead_obj, _ = Lead.objects.get_or_create(
            org=org,
            email=email,
            defaults={
                "title": title,
                "first_name": fn,
                "last_name": ln,
                "phone": phone,
                "company_name": company,
                "status": status,
                "rating": rating,
                "source": source,
                "city": city,
                "description": desc,
            }
        )
        lead_obj.assigned_to.add(assigned_profile)
        created_leads.append(lead_obj)

    # 7. Create 35 Opportunities
    opp_titles = [
        "پروژه پیاده‌سازی CRM سازمانی",
        "توسعه نرم‌افزار هوش مصنوعی و اتوماسیون",
        "تجهیز سرورها و زیرساخت شبکه",
        "قرارداد پشتیبانی و نگهداری سالانه",
        "پورتال جامع سازمانی و خدمات دیجیتال",
        "مشاوره دیجیتال مارکتینگ و فروش",
        "لایسنس نرم‌افزاری ۵۰ کاربره",
    ]

    for i in range(35):
        title = f"{random.choice(opp_titles)} - کد {i+101}"
        amount = random.randint(30, 950) * 1000000
        stage = random.choice(STAGES)
        acc = random.choice(created_accounts)
        assigned_profile = random.choice(profiles)

        opp_obj, _ = Opportunity.objects.get_or_create(
            org=org,
            name=title,
            defaults={
                "amount": amount,
                "stage": stage,
                "account": acc,
            }
        )
        opp_obj.assigned_to.add(assigned_profile)

    # 8. Create 40 Tasks & Follow-ups
    task_titles = [
        "تماس پیگیری جهت نهایی‌سازی پیش‌فاکتور",
        "جلسه حضوری دموی محصول و پاسخ به ابهامات فنی",
        "ارسال مدارک مناقصه و فرم‌های ارزیابی",
        "پیگیری واریز پیش‌پرداخت قرارداد",
        "بررسی تغییرات درخواستی در لایسنس نرم‌افزار",
        "⚠️ پیگیری معوق: بررسی عدم واریز فاکتور سررسیدشده",
        "تنظیم جلسه با مدیران ارشد مالی شرکت",
    ]

    now = timezone.now()
    due_dates = [
        now.date() - timedelta(days= random.randint(1, 5)),  # Overdue
        now.date(),  # Today
        now.date() + timedelta(days=1),  # Tomorrow
        now.date() + timedelta(days=random.randint(2, 6)),  # This week
        now.date() + timedelta(days=random.randint(7, 20)),  # Later
    ]

    for i in range(40):
        t_title = f"{random.choice(task_titles)} (شماره {i+1})"
        t_status = random.choice(TASK_STATUSES)
        t_priority = random.choice(TASK_PRIORITIES)
        t_due = random.choice(due_dates)
        assigned_profile = random.choice(profiles)

        task_obj, _ = Task.objects.get_or_create(
            org=org,
            title=t_title,
            defaults={
                "status": t_status,
                "priority": t_priority,
                "due_date": t_due,
            }
        )
        task_obj.assigned_to.add(assigned_profile)

    # 9. Create 50 Interaction Logs with follow-ups
    for i in range(50):
        lead_target = random.choice(created_leads)
        assigned_profile = random.choice(profiles)

        follow_up_d = random.choice(due_dates)

        InteractionLog.objects.create(
            org=org,
            entity_type="Lead",
            entity_id=lead_target.id,
            interaction_type=random.choice(["CALL", "MEETING", "EMAIL", "NOTE"]),
            subject=f"پیگیری تعامل شماره {i+1} با {lead_target.first_name} {lead_target.last_name}",
            description=f"پیگیری کارشناس {assigned_profile.user.name} درباره پروژه {lead_target.company_name}. توضیحات ثبت شده.",
            follow_up_date=timezone.now() + timedelta(days=random.randint(-3, 15)),
            created_by=assigned_profile.user
        )

    # 10. Create 20 Invoices
    for i in range(20):
        acc = random.choice(created_accounts)
        inv_num = f"INV-1403-{i+200}"
        amount = random.randint(50, 600) * 1000000
        inv_status = random.choice(INVOICE_STATUSES)

        Invoice.objects.get_or_create(
            org=org,
            invoice_number=inv_num,
            defaults={
                "invoice_title": f"فاکتور فروش خدمات و تجهیزات شماره {i+1}",
                "client_name": acc.name,
                "client_email": acc.email,
                "total_amount": amount,
                "status": inv_status
            }
        )

    print("[SUCCESS] Large Persian CRM Data Seeding Completed Successfully!")

if __name__ == "__main__":
    seed_large_persian_crm_data()
