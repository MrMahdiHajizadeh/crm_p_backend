from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.models import Attachments, Comment
from common.permissions import HasOrgContext
from common.serializer import AttachmentsSerializer, CommentSerializer
from opportunity import swagger_params
from opportunity.serializer import OpportunityCommentEditSwaggerSerializer


class OpportunityCommentView(APIView):
    model = Comment
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk, org=self.request.profile.org)

    def get_opportunity(self, pk):
        from opportunity.models import Opportunity
        return Opportunity.objects.get(pk=pk, org=self.request.profile.org)

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params.organization_params,
        responses={200: CommentSerializer(many=True)},
        description="List comments for an opportunity, or get a single comment by ID",
    )
    def get(self, request, pk, format=None):
        """Get comments for an opportunity, or a single comment by its ID."""
        try:
            comment = self.get_object(pk)
            return Response(CommentSerializer(comment).data)
        except self.model.DoesNotExist:
            pass

        opportunity = self.get_opportunity(pk)
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(opportunity.__class__)
        comments = self.model.objects.filter(
            content_type=content_type,
            object_id=opportunity.id,
            org=request.profile.org,
        ).order_by("-id")
        return Response(CommentSerializer(comments, many=True).data)

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params.organization_params,
        request=OpportunityCommentEditSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="OpportunityCommentUpdateResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def put(self, request, pk, format=None):
        params = request.data
        obj = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
            or request.profile == obj.commented_by
        ):
            serializer = CommentSerializer(obj, data=params)
            if params.get("comment"):
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        {"error": False, "message": "Comment Submitted"},
                        status=status.HTTP_200_OK,
                    )
                return Response(
                    {"error": True, "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(
            {
                "error": True,
                "errors": "You don't have permission to perform this action.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params.organization_params,
        request=OpportunityCommentEditSwaggerSerializer,
        description="Partial Comment Update",
        responses={
            200: inline_serializer(
                name="OpportunityCommentPatchResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def patch(self, request, pk, format=None):
        """Handle partial updates to a comment."""
        params = request.data
        obj = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
            or request.profile == obj.commented_by
        ):
            serializer = CommentSerializer(obj, data=params, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"error": False, "message": "Comment Updated"},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "error": True,
                "errors": "You don't have permission to perform this action.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="OpportunityCommentDeleteResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
            or request.profile == self.object.commented_by
        ):
            self.object.delete()
            return Response(
                {"error": False, "message": "Comment Deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "error": True,
                "errors": "You do not have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class OpportunityAttachmentView(APIView):
    model = Attachments
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    def get_opportunity(self, pk):
        from opportunity.models import Opportunity
        return Opportunity.objects.get(pk=pk, org=self.request.profile.org)

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params.organization_params,
        responses={200: AttachmentsSerializer(many=True)},
        description="List attachments for an opportunity, or get a single attachment by ID",
    )
    def get(self, request, pk, format=None):
        """Get attachments for an opportunity, or a single attachment by its ID."""
        try:
            attachment = self.get_object(pk)
            return Response(AttachmentsSerializer(attachment).data)
        except self.model.DoesNotExist:
            pass

        opportunity = self.get_opportunity(pk)
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(opportunity.__class__)
        attachments = self.model.objects.filter(
            content_type=content_type,
            object_id=opportunity.id,
            org=request.profile.org,
        ).order_by("-id")
        return Response(AttachmentsSerializer(attachments, many=True).data)

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="OpportunityAttachmentDeleteResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def delete(self, request, pk, format=None):
        self.object = self.model.objects.get(pk=pk)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
            or request.profile == self.object.created_by
        ):
            self.object.delete()
            return Response(
                {"error": False, "message": "Attachment Deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "error": True,
                "errors": "You don't have permission to perform this action.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )
