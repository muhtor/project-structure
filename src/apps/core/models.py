from django.db import models
from django.utils.translation import ugettext_lazy as _


class BaseModel(models.Model):
    """ Simply inherit this class to enable soft deletion on a model. """

    class Meta:
        abstract = True

    # objects = SoftDeleteManager()
    # all_objects = AllManager()
    deleted_time = models.DateTimeField(verbose_name=_('deleted_time'), null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)
    created_by = models.ForeignKey("konnex_user.User", null=True, related_name="+", on_delete=models.DO_NOTHING)
    modified_by = models.ForeignKey("konnex_user.User", null=True, related_name="+", on_delete=models.DO_NOTHING)
    deleted_by = models.ForeignKey("konnex_user.User", null=True, related_name="+", on_delete=models.DO_NOTHING)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.before_save()
        # self.is_new = not self.id
        # self.created_by = self.created_by if self.created_by else get_signed_in_user()
        # self.modified_by = get_signed_in_user()
        super().save(force_insert, force_update, using, update_fields)
        self.after_save()
        return self
