import json
import logging
import re
import requests
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Q

from leads.models import Lead, InteractionLog
from contacts.models import Contact
from accounts.models import Account
from opportunity.models import Opportunity
from tasks.models import Task
from invoices.models import Invoice
from cases.models import Case
from common.models import Profile, User

logger = logging.getLogger(__name__)


class CRMSearchEngine:
    """
    Intelligent Search Engine for CRM Entities.
    Extracts phone numbers, emails, names, and search terms from conversational prompts
    and queries across Leads, Contacts, Accounts, Opportunities, Tasks, Invoices, and InteractionLogs.
    """

    STOP_WORDS = {
        "اطلاعات", "سرنخ", "مخاطب", "شرکت", "شماره", "تلفن", "ایمیل", "نام", "رو", "برام", "پیدا",
        "کن", "بگو", "چیست", "است", "مال", "کیه", "داریم", "که", "با", "از", "در", "به", "توسط",
        "وضعیت", "جزئیات", "سوابق", "پیگیری", "فاکتور", "معامله", "پروژه", "سلام", "لطفا", "میخوام", "بده"
    }

    @classmethod
    def search_all(cls, org, query_str):
        if not query_str or len(query_str.strip()) < 2:
            return {}

        prompt = query_str.strip()

        # Extract search patterns from conversational prompt
        phone_tokens = re.findall(r'\+?\d[\d\s-]{3,14}\d', prompt)
        phone_tokens = [p.replace(" ", "").replace("-", "") for p in phone_tokens if len(p.replace(" ", "").replace("-", "")) >= 3]

        email_tokens = re.findall(r'[\w.-]+@[\w.-]+\.\w+', prompt)

        # Extract word tokens excluding stop words
        words = re.findall(r'[\w\u0600-\u06FF]+', prompt)
        clean_terms = [w for w in words if w.lower() not in cls.STOP_WORDS and len(w) >= 2]

        search_terms = list(set(phone_tokens + email_tokens + clean_terms))
        if not search_terms:
            search_terms = [prompt]

        results = {
            "query": prompt,
            "terms": search_terms,
            "leads": [],
            "contacts": [],
            "accounts": [],
            "opportunities": [],
            "tasks": [],
            "invoices": [],
            "interactions": []
        }

        # Build Q filter dynamically for all terms
        q_lead = Q()
        q_contact = Q()
        q_account = Q()
        q_task = Q()
        q_opp = Q()
        q_inv = Q()
        q_interaction = Q()

        for term in search_terms:
            q_lead |= (
                Q(phone__icontains=term) |
                Q(email__icontains=term) |
                Q(first_name__icontains=term) |
                Q(last_name__icontains=term) |
                Q(title__icontains=term) |
                Q(company_name__icontains=term) |
                Q(description__icontains=term) |
                Q(city__icontains=term)
            )
            q_contact |= (
                Q(phone__icontains=term) |
                Q(email__icontains=term) |
                Q(first_name__icontains=term) |
                Q(last_name__icontains=term) |
                Q(description__icontains=term)
            )
            q_account |= (
                Q(name__icontains=term) |
                Q(phone__icontains=term) |
                Q(email__icontains=term) |
                Q(website__icontains=term) |
                Q(city__icontains=term)
            )
            q_task |= (
                Q(title__icontains=term) |
                Q(description__icontains=term)
            )
            q_opp |= (
                Q(name__icontains=term) |
                Q(stage__icontains=term)
            )
            q_inv |= (
                Q(invoice_number__icontains=term) |
                Q(invoice_title__icontains=term) |
                Q(client_name__icontains=term) |
                Q(client_email__icontains=term)
            )
            q_interaction |= (
                Q(subject__icontains=term) |
                Q(description__icontains=term)
            )

        # 1. Search Leads
        leads = Lead.objects.filter(org=org).filter(q_lead).distinct()[:15]
        for item in leads:
            assigned_names = [p.user.name for p in item.assigned_to.all() if p.user]
            person_fullname = f"{item.first_name} {item.last_name}".strip()
            results["leads"].append({
                "id": str(item.id),
                "lead_title": item.title or "بدون عنوان",
                "contact_person": person_fullname or "ثبت‌نشده",
                "name": f"{item.title} (فرد: {person_fullname})",
                "phone": item.phone or "",
                "email": item.email or "",
                "company_name": item.company_name or "",
                "status": item.status or "",
                "rating": item.rating or "",
                "source": item.source or "",
                "assigned_to": ", ".join(assigned_names) if assigned_names else "تخصیص‌نیافته",
                "description": item.description or "",
                "created_at": item.created_at.strftime("%Y-%m-%d") if hasattr(item, "created_at") and item.created_at else ""
            })

        # 2. Search Contacts
        contacts = Contact.objects.filter(org=org).filter(q_contact).distinct()[:15]
        for item in contacts:
            results["contacts"].append({
                "id": str(item.id),
                "name": f"{item.first_name} {item.last_name}".strip() or "مخاطب",
                "phone": item.phone or "",
                "email": item.email or "",
                "account": item.account.name if item.account else "",
                "created_at": item.created_at.strftime("%Y-%m-%d") if hasattr(item, 'created_at') and item.created_at else ""
            })

        # 3. Search Accounts (Companies)
        accounts = Account.objects.filter(org=org).filter(q_account).distinct()[:15]
        for item in accounts:
            results["accounts"].append({
                "id": str(item.id),
                "name": item.name,
                "phone": item.phone or "",
                "email": item.email or "",
                "website": item.website or "",
                "city": item.city or "",
            })

        # 4. Search Tasks
        tasks = Task.objects.filter(org=org).filter(q_task).distinct()[:15]
        for item in tasks:
            results["tasks"].append({
                "id": str(item.id),
                "title": item.title,
                "status": item.status or "",
                "priority": item.priority or "",
                "due_date": str(item.due_date) if item.due_date else "",
            })

        # 5. Search Opportunities
        opps = Opportunity.objects.filter(org=org).filter(q_opp).distinct()[:15]
        for item in opps:
            results["opportunities"].append({
                "id": str(item.id),
                "name": item.name,
                "stage": item.stage or "",
                "amount": float(item.amount or 0),
            })

        # 6. Search Invoices
        invs = Invoice.objects.filter(org=org).filter(q_inv).distinct()[:15]
        for item in invs:
            results["invoices"].append({
                "id": str(item.id),
                "invoice_number": item.invoice_number or "",
                "company_name": item.client_name or "",
                "total_amount": float(item.total_amount or 0),
                "status": item.status or "",
            })

        # 7. Search Interaction Logs
        interactions = InteractionLog.objects.filter(org=org).filter(q_interaction).distinct()[:15]
        for item in interactions:
            results["interactions"].append({
                "id": str(item.id),
                "type": item.interaction_type or "",
                "subject": item.subject or "",
                "notes": item.description or "",
                "created_at": item.interaction_date.strftime("%Y-%m-%d %H:%M") if hasattr(item, 'interaction_date') and item.interaction_date else ""
            })

        return results


class CRMDataAnalyzer:
    """
    Scrapes and analyzes tenant database records safely in read-only mode for a specific organization.
    Provides complete visibility into Leads, Contacts, Accounts, and Tasks records.
    """

    @staticmethod
    def get_organization_snapshot(org, query_prompt=""):
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # 1. Leads Analysis & Recent Records List
        lead_qs = Lead.objects.filter(org=org)
        total_leads = lead_qs.count()
        leads_today = lead_qs.filter(created_at__gte=start_of_today).count()
        leads_this_week = lead_qs.filter(created_at__gte=seven_days_ago).count()
        leads_this_month = lead_qs.filter(created_at__gte=thirty_days_ago).count()

        status_breakdown = list(
            lead_qs.values("status").annotate(count=Count("id")).order_by("-count")
        )
        rating_breakdown = list(
            lead_qs.values("rating").annotate(count=Count("id")).order_by("-count")
        )

        # Top recent leads snapshot list for direct LLM visibility
        recent_leads_sample = []
        for l in lead_qs.order_by("-created_at")[:25]:
            assigned_names = [p.user.name for p in l.assigned_to.all() if p.user]
            recent_leads_sample.append({
                "lead_title": l.title or "بدون عنوان",
                "contact_person": f"{l.first_name} {l.last_name}".strip() or "ثبت‌نشده",
                "phone": l.phone or "",
                "email": l.email or "",
                "company": l.company_name or "",
                "status": l.status or "",
                "rating": l.rating or "",
                "assigned_to": ", ".join(assigned_names) if assigned_names else "تخصیص‌نیافته"
            })

        # 2. Accounts & Contacts
        total_accounts = Account.objects.filter(org=org).count()
        total_contacts = Contact.objects.filter(org=org).count()

        contacts_sample = []
        for c in Contact.objects.filter(org=org).order_by("-created_at")[:15]:
            contacts_sample.append({
                "name": f"{c.first_name} {c.last_name}".strip(),
                "phone": c.phone or "",
                "email": c.email or "",
                "company": c.account.name if c.account else ""
            })

        # 3. Opportunities (Deals) Analysis
        opp_qs = Opportunity.objects.filter(org=org)
        total_opportunities = opp_qs.count()
        total_pipeline_value = opp_qs.aggregate(total=Sum("amount"))["total"] or 0

        # 4. Tasks & Urgent Work
        task_qs = Task.objects.filter(org=org)
        total_tasks = task_qs.count()
        overdue_tasks = task_qs.filter(
            Q(status="In Progress") | Q(status="New"),
            due_date__lt=now.date()
        ).count()

        # 5. Invoices & Revenue
        invoice_qs = Invoice.objects.filter(org=org)
        total_invoices = invoice_qs.count()
        total_invoiced_amount = invoice_qs.aggregate(total=Sum("total_amount"))["total"] or 0

        # 6. Team Performance Breakdown
        profiles = Profile.objects.filter(org=org, is_active=True).select_related("user")
        team_performance = []

        for p in profiles:
            user_name = p.user.name or p.user.email or "کاربر"
            user_phone = p.user.phone or p.user.email or ""

            assigned_leads = lead_qs.filter(assigned_to=p).count()
            converted_leads = lead_qs.filter(assigned_to=p, status="converted").count()
            hot_leads = lead_qs.filter(assigned_to=p, rating="HOT").count()

            assigned_opps = opp_qs.filter(assigned_to=p)
            opp_count = assigned_opps.count()
            opp_value = float(assigned_opps.aggregate(total=Sum("amount"))["total"] or 0)
            won_value = float(assigned_opps.filter(stage="CLOSED_WON").aggregate(total=Sum("amount"))["total"] or 0)

            assigned_tasks = task_qs.filter(assigned_to=p)
            task_count = assigned_tasks.count()
            overdue_task_count = assigned_tasks.filter(
                Q(status="In Progress") | Q(status="New"),
                due_date__lt=now.date()
            ).count()

            logged_interactions = InteractionLog.objects.filter(org=org, created_by=p.user).count()

            team_performance.append({
                "user_name": user_name,
                "phone": user_phone,
                "role": p.role,
                "leads": {
                    "total_assigned": assigned_leads,
                    "converted": converted_leads,
                    "hot": hot_leads
                },
                "opportunities": {
                    "count": opp_count,
                    "pipeline_value": opp_value,
                    "won_value": won_value
                },
                "tasks": {
                    "total": task_count,
                    "overdue": overdue_task_count
                },
                "logged_interactions": logged_interactions
            })

        # 7. Execute Multi-Field Search Engine with Smart Tokenization
        search_results = CRMSearchEngine.search_all(org, query_prompt)

        snapshot_data = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "organization_name": org.name,
            "leads": {
                "total": total_leads,
                "created_today": leads_today,
                "created_this_week": leads_this_week,
                "created_this_month": leads_this_month,
                "by_status": status_breakdown,
                "by_rating": rating_breakdown,
                "recent_sample": recent_leads_sample
            },
            "contacts_count": total_contacts,
            "contacts_sample": contacts_sample,
            "accounts_count": total_accounts,
            "opportunities": {
                "total_count": total_opportunities,
                "pipeline_value": float(total_pipeline_value),
            },
            "tasks": {
                "total": total_tasks,
                "overdue": overdue_tasks,
            },
            "invoices": {
                "total": total_invoices,
                "total_revenue": float(total_invoiced_amount),
            },
            "team_performance": team_performance,
            "search_results": search_results
        }

        return snapshot_data

    @staticmethod
    def format_snapshot_as_prompt_text(snapshot):
        leads = snapshot["leads"]
        opps = snapshot["opportunities"]
        tasks = snapshot["tasks"]
        invs = snapshot["invoices"]
        search = snapshot.get("search_results", {})

        lines = [
            f"=== دیتابیس جامع سازمان ({snapshot['organization_name']}) ===",
            f"تاریخ استخراج: {snapshot['timestamp']}",
            "",
            "📊 خلاصه آمار کل دیتابیس:",
            f"- کل سرنخ‌ها (Leads): {leads['total']} عدد (ورودی جدید ماه: {leads['created_this_month']})",
            f"- مخاطبان (Contacts): {snapshot['contacts_count']} | شرکت‌ها (Accounts): {snapshot['accounts_count']}",
            f"- فرصت‌های فروش: {opps['total_count']} (ارزش کل: {opps['pipeline_value']:,.0f} تومان)",
            f"- وظایف عقب‌افتاده: {tasks['overdue']} | فاکتورها: {invs['total']}",
            "",
            "👥 عملکرد و آمار به تفکیک کارشناسان تیم:",
        ]

        for member in snapshot.get("team_performance", []):
            lines.append(
                f"- **{member['user_name']}** (تلفن: `{member['phone']}` | نقش: {member['role']}):\n"
                f"  • سرنخ‌های تخصیص‌یافته: {member['leads']['total_assigned']} (تبدیل: {member['leads']['converted']} | داغ: {member['leads']['hot']})\n"
                f"  • معامله‌ها: {member['opportunities']['count']} (ارزش کل: {member['opportunities']['pipeline_value']:,.0f} | برنده: {member['opportunities']['won_value']:,.0f})\n"
                f"  • وظایف: {member['tasks']['total']} ({member['tasks']['overdue']} عقب‌افتاده) | تعاملات: {member['logged_interactions']} مورد"
            )

        lines.append("")

        # Include Recent Leads Data Sample with both Lead Title & Contact Person Name
        if leads.get("recent_sample"):
            lines.append("🎯 نمونه رکوردهای سرنخ‌های موجود در دیتابیس (Lead Records):")
            for item in leads["recent_sample"]:
                lines.append(
                    f"• **عنوان/نام سرنخ (Lead Title):** {item['lead_title']} | **نام و نام خانوادگی فرد (Person):** {item['contact_person']} | **تلفن:** `{item['phone']}` | **ایمیل:** `{item['email']}` | **شرکت:** {item['company']} | **وضعیت:** {item['status']} | **مسئول:** {item['assigned_to']}"
                )
            lines.append("")

        # Include Search Results if available
        if search and (search.get("leads") or search.get("contacts") or search.get("accounts") or search.get("tasks") or search.get("opportunities") or search.get("invoices") or search.get("interactions")):
            lines.append(f"🔍 نتایج جستجوی اختصاصی و مستقیم برای عبارت درخواستی کاربر:")

            if search.get("leads"):
                lines.append(f"• سرنخ‌های انطباق‌یافته با جستجو ({len(search['leads'])} مورد):")
                lines.append(json.dumps(search["leads"], ensure_ascii=False))

            if search.get("contacts"):
                lines.append(f"• مخاطبین انطباق‌یافته ({len(search['contacts'])} مورد):")
                lines.append(json.dumps(search["contacts"], ensure_ascii=False))

            if search.get("accounts"):
                lines.append(f"• شرکت‌های انطباق‌یافته ({len(search['accounts'])} مورد):")
                lines.append(json.dumps(search["accounts"], ensure_ascii=False))

            if search.get("tasks"):
                lines.append(f"• پیگیری‌ها و وظایف انطباق‌یافته ({len(search['tasks'])} مورد):")
                lines.append(json.dumps(search["tasks"], ensure_ascii=False))

            if search.get("opportunities"):
                lines.append(f"• فرصت‌های فروش انطباق‌یافته ({len(search['opportunities'])} مورد):")
                lines.append(json.dumps(search["opportunities"], ensure_ascii=False))

            if search.get("interactions"):
                lines.append(f"• سوابق تماس‌ها ({len(search['interactions'])} مورد):")
                lines.append(json.dumps(search["interactions"], ensure_ascii=False))

            lines.append("")

        return "\n".join(lines)


class AIEngineService:
    """
    Executes AI requests via configured API URL & Proxy, with fallback logic.
    """

    @classmethod
    def process_query(cls, org, user_prompt, ai_setting=None):
        snapshot = CRMDataAnalyzer.get_organization_snapshot(org, query_prompt=user_prompt)
        prompt_context = CRMDataAnalyzer.format_snapshot_as_prompt_text(snapshot)

        api_key = ai_setting.api_key if ai_setting else ""
        api_url = (ai_setting.api_url if ai_setting and ai_setting.api_url else "https://api.openai.com/v1").rstrip("/")
        model_name = ai_setting.model_name if ai_setting and ai_setting.model_name else "gpt-4o-mini"
        proxy_url = ai_setting.proxy_url if ai_setting else ""

        system_instruction = (
            "شما دستیار هوشمند، جستجوگر دقیق و تحلیل‌گر دیتابیس CRM هستید.\n"
            "نکته بسیار مهم در جداول مشخصات سرنخ‌ها:\n"
            "بین 'عنوان/نام سرنخ (Lead Title)' (مانند استعلام خرید، توسعه پورتال، پروژه اتوماسیون) و 'نام و نام خانوادگی فرد/مخاطب (Person Name)' (مانند حامد طاهری، کامران رستمی) تفکیک قائل شوید و هر دو فیلد را به صورت مجزا در دو ستون یا دو سطر جداگانه نمایش دهید.\n\n"
            "دستورالعمل پاسخگویی:\n"
            "1. اگر کاربر درباره یک شماره تلفن یا مشخصات یک سرنخ پرسید، جدول کامل مشخصات شامل: [عنوان/نام سرنخ | نام و نام خانوادگی فرد | شماره تلفن | ایمیل | شرکت | وضعیت | کارشناس مسئول] را تفکیک‌شده بنویسید.\n"
            "2. هرگز این دو فیلد را با هم ترکیب نکنید.\n"
            "3. پاسخ شما باید کاملاً مستند، روان و همراه با جدول‌ها یا لیست‌های مارک‌داون باشد."
        )

        messages = [
            {"role": "system", "content": f"{system_instruction}\n\n{prompt_context}"},
            {"role": "user", "content": user_prompt}
        ]

        if api_key and ai_setting.is_active:
            try:
                content, reasoning = cls._call_external_llm_api(
                    api_url=api_url,
                    api_key=api_key,
                    model_name=model_name,
                    messages=messages,
                    proxy_url=proxy_url
                )
                return content, reasoning, snapshot
            except Exception as e:
                logger.warning(f"External AI API call failed ({e}). Falling back to CRM Analytics Engine.")

        content, reasoning = cls._generate_internal_analysis(user_prompt, snapshot)
        return content, reasoning, snapshot

    @classmethod
    def _call_external_llm_api(cls, api_url, api_key, model_name, messages, proxy_url=""):
        endpoint = f"{api_url}/chat/completions" if not api_url.endswith("/chat/completions") else api_url

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2000,
        }

        proxies = {}
        if proxy_url:
            proxies = {
                "http": proxy_url,
                "https": proxy_url,
            }

        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            proxies=proxies if proxies else None,
            timeout=30
        )

        if response.status_code != 200:
            raise ValueError(f"API Error ({response.status_code}): {response.text}")

        res_json = response.json()
        choice = res_json["choices"][0]["message"]
        content = choice.get("content", "")
        reasoning = (
            f"پاسخ مستقیم از مدل {model_name} بر اساس رکوردهای دیتابیس CRM و تفکیک عنوان سرنخ و نام مخاطب."
        )
        return content, reasoning

    @classmethod
    def _generate_internal_analysis(cls, user_prompt, snapshot):
        leads = snapshot["leads"]
        opps = snapshot["opportunities"]
        tasks = snapshot["tasks"]
        invs = snapshot["invoices"]
        team_perf = snapshot.get("team_performance", [])
        search = snapshot.get("search_results", {})

        reasoning = (
            "جستجوی هوشمند در تمام فیلدهای دیتابیس همراه با تفکیک عنوان سرنخ و نام مخاطب انجام شد."
        )

        content = []
        prompt_lower = user_prompt.lower()

        has_search_matches = (
            search and (
                search.get("leads") or
                search.get("contacts") or
                search.get("accounts") or
                search.get("tasks") or
                search.get("opportunities") or
                search.get("invoices") or
                search.get("interactions")
            )
        )

        if has_search_matches:
            content.append(f"### 🔍 نتایج جستجوی اختصاصی دیتابیس برای («{search.get('query')}»)\n")

            if search.get("leads"):
                content.append(f"#### 🎯 سرنخ‌های انطباق‌یافته ({len(search['leads'])} مورد):")
                content.append("| عنوان / نام سرنخ | نام و نام خانوادگی فرد | شماره تلفن | ایمیل | نام شرکت | وضعیت | کارشناس مسئول |")
                content.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
                for l in search["leads"]:
                    content.append(f"| **{l.get('lead_title', l.get('name'))}** | **{l.get('contact_person', '---')}** | `{l['phone'] or '---'}` | `{l['email'] or '---'}` | {l['company_name'] or '---'} | {l['status'] or '---'} | {l['assigned_to'] or '---'} |")
                content.append("")

            if search.get("contacts"):
                content.append(f"#### 👤 مخاطبین انطباق‌یافته ({len(search['contacts'])} مورد):")
                content.append("| نام مخاطب | شماره تلفن | ایمیل | شرکت |")
                content.append("| :--- | :--- | :--- | :--- |")
                for c in search["contacts"]:
                    content.append(f"| **{c['name']}** | `{c['phone'] or '---'}` | `{c['email'] or '---'}` | {c['account'] or '---'} |")
                content.append("")

            if search.get("accounts"):
                content.append(f"#### 🏢 شرکت‌های انطباق‌یافته ({len(search['accounts'])} مورد):")
                content.append("| نام شرکت | شماره تلفن | ایمیل | شهر | وب‌سایت |")
                content.append("| :--- | :--- | :--- | :--- | :--- |")
                for a in search["accounts"]:
                    content.append(f"| **{a['name']}** | `{a['phone'] or '---'}` | `{a['email'] or '---'}` | {a['city'] or '---'} | {a['website'] or '---'} |")
                content.append("")

            if search.get("tasks"):
                content.append(f"#### ✅ وظایف و پیگیری‌های مرتبط ({len(search['tasks'])} مورد):")
                for t in search["tasks"]:
                    content.append(f"- **{t['title']}** (وضعیت: {t['status']} | تاریخ سررسید: `{t['due_date'] or '---'}`) ")
                content.append("")

            if search.get("opportunities"):
                content.append(f"#### 💰 فرصت‌های فروش مرتبط ({len(search['opportunities'])} مورد):")
                for o in search["opportunities"]:
                    content.append(f"- **{o['name']}** (مرحله: {o['stage']} | ارزش: {o['amount']:,.0f})")
                content.append("")

            if search.get("interactions"):
                content.append(f"#### 📞 سوابق تماس‌ها و تعاملات ({len(search['interactions'])} مورد):")
                for i in search["interactions"]:
                    content.append(f"- **{i['type']}**: {i['subject']} - {i['notes']} (`{i['created_at']}`)")
                content.append("")

        elif "سرنخ" in prompt_lower or "تلفن" in prompt_lower or "شماره" in prompt_lower or "پیدا" in prompt_lower:
            content.append(f"### 🎯 رکوردهای سرنخ‌های موجود در دیتابیس CRM ({snapshot['organization_name']})\n")
            content.append("| عنوان / نام سرنخ | نام و نام خانوادگی فرد | شماره تلفن | ایمیل | شرکت | وضعیت | کارشناس مسئول |")
            content.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
            for l in leads.get("recent_sample", []):
                content.append(f"| **{l['lead_title']}** | **{l['contact_person']}** | `{l['phone'] or '---'}` | `{l['email'] or '---'}` | {l['company'] or '---'} | {l['status']} | {l['assigned_to']} |")

        elif "اعضا" in prompt_lower or "کارشناس" in prompt_lower or "تیم" in prompt_lower or "عملکرد" in prompt_lower:
            content.append(f"### 👥 گزارش و تحلیل عملکرد تفکیکی اعضا و کارشناسان ({snapshot['organization_name']})\n")
            content.append("| نام کارشناس / عضو | نقش | سرنخ‌های تخصیص‌یافته | ارزش معامله‌ها | وظایف عقب‌افتاده | تعاملات ثبت‌شده |")
            content.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for m in team_perf:
                content.append(
                    f"| **{m['user_name']}** | {m['role']} | {m['leads']['total_assigned']} (تبدیل: {m['leads']['converted']}) | {m['opportunities']['pipeline_value']:,.0f} تومان | {m['tasks']['overdue']} مورد | {m['logged_interactions']} تماس/جلسه |"
                )

        else:
            content.append(f"### 📊 گزارش و تحلیل جامع داده‌های CRM ({snapshot['organization_name']})\n")
            content.append("#### 🎯 رکوردهای اخیر سرنخ‌های دیتابیس (با تفکیک عنوان سرنخ و نام مخاطب):")
            content.append("| عنوان / نام سرنخ | نام و نام خانوادگی فرد | شماره تلفن | شرکت | کارشناس |")
            content.append("| :--- | :--- | :--- | :--- | :--- |")
            for l in leads.get("recent_sample", [])[:10]:
                content.append(f"| **{l['lead_title']}** | **{l['contact_person']}** | `{l['phone']}` | {l['company']} | {l['assigned_to']} |")

            content.append("\n#### 📈 خلاصه آمار کل:")
            content.append(f"- **کل سرنخ‌ها:** {leads['total']} سرنخ | **مخاطبین:** {snapshot['contacts_count']} | **شرکت‌ها:** {snapshot['accounts_count']}")
            content.append(f"- **فروش:** {opps['total_count']} معامله به ارزش کل {opps['pipeline_value']:,.0f} تومان.")
            content.append(f"- **وظایف عقب‌افتاده:** {tasks['overdue']} مورد.")

        return "\n".join(content), reasoning
