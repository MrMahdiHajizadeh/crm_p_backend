from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AISetting, AIChatSession, AIChatMessage
from .serializers import (
    AISettingSerializer,
    AIChatSessionSerializer,
    AIChatMessageSerializer,
)
from .services import AIEngineService


class AISettingView(APIView):
    """
    API endpoint for getting and updating AI settings (API key, proxy, model, endpoints).
    Admin permissions required.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        org = request.profile.org
        setting, _ = AISetting.objects.get_or_create(org=org)
        serializer = AISettingSerializer(setting)
        return Response(serializer.data)

    def patch(self, request):
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "فقط مدیران سیستم امکان تغییر تنظیمات هوش مصنوعی را دارند."},
                status=status.HTTP_403_FORBIDDEN,
            )

        org = request.profile.org
        setting, _ = AISetting.objects.get_or_create(org=org)

        serializer = AISettingSerializer(setting, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        return self.patch(request)


class AIChatSessionListView(APIView):
    """
    List user's AI chat sessions or all team sessions if request user is Admin.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        org = request.profile.org
        is_admin = request.profile.role == "ADMIN" or request.user.is_superuser
        filter_all = request.query_params.get("all_team") == "true" or request.query_params.get("user_id")

        if is_admin and filter_all:
            user_id = request.query_params.get("user_id")
            if user_id:
                sessions = AIChatSession.objects.filter(org=org, user_id=user_id)
            else:
                sessions = AIChatSession.objects.filter(org=org)
        else:
            sessions = AIChatSession.objects.filter(org=org, user=request.user)

        serializer = AIChatSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    def post(self, request):
        org = request.profile.org
        title = request.data.get("title", "گفتگوی جدید")
        session = AIChatSession.objects.create(
            org=org,
            user=request.user,
            title=title
        )
        serializer = AIChatSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AIChatSessionDetailView(APIView):
    """
    Retrieve message history or delete a session.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, session_id):
        org = request.profile.org
        is_admin = request.profile.role == "ADMIN" or request.user.is_superuser

        try:
            if is_admin:
                session = AIChatSession.objects.get(id=session_id, org=org)
            else:
                session = AIChatSession.objects.get(id=session_id, org=org, user=request.user)
        except AIChatSession.DoesNotExist:
            return Response({"error": "جلسه گفتگو یافت نشد."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AIChatSessionSerializer(session)
        return Response(serializer.data)

    def delete(self, request, session_id):
        org = request.profile.org
        is_admin = request.profile.role == "ADMIN" or request.user.is_superuser

        try:
            if is_admin:
                session = AIChatSession.objects.get(id=session_id, org=org)
            else:
                session = AIChatSession.objects.get(id=session_id, org=org, user=request.user)
            session.delete()
            return Response({"success": True}, status=status.HTTP_200_OK)
        except AIChatSession.DoesNotExist:
            return Response({"error": "جلسه گفتگو یافت نشد."}, status=status.HTTP_404_NOT_FOUND)


class AIChatMessageView(APIView):
    """
    Post a message to an AI chat session and receive AI data-backed report response.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, session_id):
        org = request.profile.org
        user_prompt = request.data.get("prompt", "").strip()

        if not user_prompt:
            return Response({"error": "متن سوال نمی‌تواند خالی باشد."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = AIChatSession.objects.get(id=session_id, org=org)
        except AIChatSession.DoesNotExist:
            return Response({"error": "جلسه گفتگو یافت نشد."}, status=status.HTTP_404_NOT_FOUND)

        # 1. Save User Message
        user_msg = AIChatMessage.objects.create(
            session=session,
            role="user",
            content=user_prompt
        )

        # Auto-update session title if it's the first message or default title
        if session.messages.count() <= 2 and (session.title == "گفتگوی جدید" or not session.title):
            derived_title = user_prompt[:40] + ("..." if len(user_prompt) > 40 else "")
            session.title = derived_title
            session.save()

        # 2. Retrieve AI settings
        ai_setting = getattr(org, "ai_setting", None)

        # 3. Process AI query with DB Analyzer & LLM / Fallback
        content, reasoning, snapshot = AIEngineService.process_query(
            org=org,
            user_prompt=user_prompt,
            ai_setting=ai_setting
        )

        # 4. Save Assistant Message with reasoning & DB evidence
        assistant_msg = AIChatMessage.objects.create(
            session=session,
            role="assistant",
            content=content,
            reasoning=reasoning,
            data_evidence=snapshot
        )

        serializer = AIChatMessageSerializer(assistant_msg)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
