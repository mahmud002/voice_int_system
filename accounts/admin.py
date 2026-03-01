from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User       # ← ADD THIS IMPORT

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


# Unregister the default User admin and replace it with our customized version
admin.site.unregister(User)               # ← now User is known
admin.site.register(User, CustomUserAdmin)