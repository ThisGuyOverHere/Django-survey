from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .forms import UserAdminCreationForm, UserAdminChangeForm, GroupAdminForm
from .models import CustomUser
from .models import Question, Topic, SubscribedSurveyQuestion, Survey, Completed


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('id_card', 'first_name', 'last_name', 'email', 'is_superuser', 'is_staff', 'is_active')
    list_filter = ('is_superuser','is_staff')
    fieldsets = (
        ('Credenziali', {'fields': ('id_card','email', 'password')}),
        ('Profilo', {'fields': ('first_name', 'last_name', 'date_of_birth', 'id_card_scan')}),
        ('Residenza', {'fields': ('comune', 'provincia')}),
        ('Permessi', {'fields': ('is_superuser', 'is_staff')}),
        ('Log Info', {'fields': ('date_joined',)}),

    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('id_card', 'email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff')}
        ),
    )
    search_fields = ('id_card', 'first_name', 'last_name')
    ordering = ('id_card',)
    filter_horizontal = ()

class QuestionAdmin(admin.ModelAdmin):
    exclude = ('votes_1','votes_2','votes_3')


# Create a new Group admin.
class GroupAdmin(admin.ModelAdmin):
    # Use our custom form.
    form = GroupAdminForm
    # Filter permissions horizontal as well.
    filter_horizontal = ['permissions']

class SurveyAdmin(admin.ModelAdmin):
    def view_link(self):
        return u"<a href='/report/%d/'>Report</a>" % self.id
    view_link.short_description = ''
    view_link.allow_tags = True
    list_display = ('survey_title', view_link)

# Now register the new UserAdmin...
admin.site.register(CustomUser, UserAdmin)
admin.site.register(Question,QuestionAdmin)
admin.site.register(Topic)
#admin.site.register(TopicSurvey)
#admin.site.register(SubscribedSurveyQuestion)
admin.site.register(Survey, SurveyAdmin)
#admin.site.register(Completed)

# Unregister the original Group admin.
admin.site.unregister(Group)
# Register the new Group ModelAdmin.
admin.site.register(Group, GroupAdmin)