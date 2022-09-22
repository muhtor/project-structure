from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import pre_save, post_save
from django.db.models import Q
from ..accounts.utils.base_email_services import GoBazarEmailServices
from ..accounts.utils.unique_key_generators import unique_key_generator
from ..billing.models import BillingProfile
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager)
from ..core.models import TimestampedModel

DEFAULT_ACTIVATION_DAYS = getattr(settings, 'DEFAULT_ACTIVATION_DAYS', 7)
FRONTEND_BASE_URL = getattr(settings, 'FRONTEND_BASE_URL')
SEND_MAIL = GoBazarEmailServices()


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, is_superuser=False):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(email=self.normalize_email(email), )
        user.set_password(password)
        user.is_superuser = is_superuser
        user.save()
        return user

    def create_staffuser(self, email, password):
        if not password:
            raise ValueError('staff/admins must have a password.')
        user = self.create_user(email, password=password)
        user.is_staff = True
        user.save()
        return user

    def create_billing_user(self, user):
        BillingProfile.objects.get_or_create(user=user, defaults={'user': user})

    def create_superuser(self, email, password):
        if not password:
            raise ValueError('superusers must have a password.')
        user = self.create_user(email, password=password, is_superuser=True)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()
        self.create_billing_user(user=user)
        return user


class User(AbstractBaseUser, TimestampedModel):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        db_index=True,
        unique=True
    )
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # email and password required by default

    objects = UserManager()

    def __str__(self):
        return f"{self.email}"

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True  # does user have a specific permision, simple answer - yes

    def has_module_perms(self, app_label):
        return True  # does user have permission to view the app 'app_label'?


class EmailActivationQuerySet(models.query.QuerySet):
    def confirmable(self):
        now = timezone.now()
        start_range = now - timedelta(days=DEFAULT_ACTIVATION_DAYS)
        # does my object have a timestamp in here
        end_range = now
        return self.filter(
            activated=False, forced_expired=False).filter(
            timestamp__gt=start_range, timestamp__lte=end_range)


class EmailActivationManager(models.Manager):
    def get_queryset(self):
        return EmailActivationQuerySet(self.model, using=self._db)

    def confirmable(self):
        return self.get_queryset().confirmable()

    def email_exists(self, email):
        return self.get_queryset().filter(Q(email=email) | Q(user__email=email)).filter(activated=False)


class EmailActivation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    key = models.CharField(max_length=120, blank=True, null=True)
    activated = models.BooleanField(default=False)
    forced_expired = models.BooleanField(default=False)
    expires = models.IntegerField(default=7)  # 7 Days
    timestamp = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    objects = EmailActivationManager()

    def __str__(self):
        return self.email

    def can_activate(self):
        qs = EmailActivation.objects.filter(pk=self.pk).confirmable()  # 1 object
        if qs.exists():
            return True
        return False

    def activate(self):
        if self.can_activate():
            # pre activation user signal
            user = self.user
            user.is_active = True
            user.save()
            # post activation signal for user
            self.activated = True
            self.save()
            return True
        return False

    def regenerate(self):
        self.key = None
        self.save()
        if self.key is not None:
            return True
        return False

    def send_activation(self):
        if not self.activated and not self.forced_expired:
            if self.key:
                # key_path = reverse("accounts:activated", kwargs={'key': self.key})
                path = FRONTEND_BASE_URL + "activation?key=" + self.key
                sent = SEND_MAIL.email_activator(email=self.email, path=path)
                return sent
            else:
                """KEY NOT"""
            return False


class GoConfiguration(TimestampedModel):
    key = models.CharField(max_length=120, blank=True)
    value = models.CharField(max_length=120, blank=True)

    class Meta:
        verbose_name = "GoConfiguration"
        verbose_name_plural = "GoConfigurations"
        ordering = ['-id']

    def __str__(self):
        return f"{self.key} / {self.value}"

    @classmethod
    def get_config(cls, key, if_not_found):
        qs = cls.objects.filter(key__exact=key)
        if qs.exists():
            return qs.latest('created_at').value
        else:
            return if_not_found if if_not_found else 0


def pre_save_email_activation(sender, instance, *args, **kwargs):
    if not instance.activated and not instance.forced_expired:
        if not instance.key:
            instance.key = unique_key_generator(instance)
pre_save.connect(pre_save_email_activation, sender=EmailActivation)


def post_save_user_create_receiver(sender, instance, created, *args, **kwargs):
    if created and not instance.is_superuser:
        obj = EmailActivation.objects.create(user=instance, email=instance.email)
        obj.send_activation()
post_save.connect(post_save_user_create_receiver, sender=User)
