from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile, Job, Application, Interview
from .models import ChatRoom, ChatMessage, ChatAttachment


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')

    def get_role(self, obj):
        return obj.userprofile.get_role_display() if hasattr(obj, 'userprofile') else '—'
    get_role.short_description = 'Role'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(UserProfile)
admin.site.register(Job)
admin.site.register(Application)
admin.site.register(Interview)


admin.site.register(ChatRoom)
admin.site.register(ChatMessage)
admin.site.register(ChatAttachment)

