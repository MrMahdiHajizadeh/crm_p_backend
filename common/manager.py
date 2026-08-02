import uuid

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, phone=None, email=None, password=None, **extra_fields):
        if not phone and not email:
            raise ValueError("Either phone or email must be set")
        if not phone:
            # Auto-generate a unique placeholder phone so callers that don't
            # provide one don't trip the unique constraint.
            local = (email or "user").split("@")[0]
            phone = f"+000-{local}-{uuid.uuid4().hex[:8]}"
        if not extra_fields.get("name"):
            extra_fields["name"] = email.split("@")[0] if email else phone
        if password:
            extra_fields["password"] = password
        user = self.model(phone=phone, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone=phone, email=email, password=password, **extra_fields)
