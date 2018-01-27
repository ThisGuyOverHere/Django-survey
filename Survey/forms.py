from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.forms import UserCreationForm
import os
from django.core.exceptions import ValidationError
from .models import CustomUser
from django.contrib.auth.models import Group
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model

# class RegisterForm(forms.ModelForm):
#     # campi da presentare
#     email = forms.EmailField(max_length=254)
#     password = forms.CharField(widget=forms.PasswordInput)
#     password2 = forms.CharField(label='Conferma password', widget=forms.PasswordInput)
#
#     class Meta:
#         model = CustomUser
#         fields = ('id_card','email', 'password', 'password2')   #campi da salvare
#
#     #TODO eliminare?
#     def clean_id_card(self):
#         id_card = self.cleaned_data.get('id_card')
#         qs = CustomUser.objects.filter(id_card=id_card)
#         if qs.exists():
#             raise forms.ValidationError("id card esistente")
#         return id_card
#
#     def clean_password2(self):
#         # Check that the two password entries match
#         password = self.cleaned_data.get("password")
#         password2 = self.cleaned_data.get("password2")
#         if password and password2 and password != password2:
#             raise forms.ValidationError("Le password non corrispondono!")
#         return password2


class UserAdminCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('id_card',)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Le password non corrispondono")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserAdminCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserAdminChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = CustomUser
        fields = ('id_card', 'password', 'is_active', 'is_superuser')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class SignUpForm(UserCreationForm):

    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField(max_length=254)

    class Meta:
        model = CustomUser
        fields = ('id_card', 'first_name', 'last_name', 'email', 'id_card_scan', 'password1', 'password2')   #campi da salvare

    def clean_id_card_scan(self):

        id_card_scan = self.cleaned_data.get('id_card_scan')

        try:
            # Valida estensione
            ext = os.path.splitext(id_card_scan.name)[1]
            valid_extension = ['.pdf', '.jpg']
            if not ext.lower() in valid_extension:
                raise ValidationError(u'Utilizza un file PDF o JPEG')

            # Valida dimensione
            if len(id_card_scan) > (3000 * 1024):
                raise forms.ValidationError("La dimensione del file non deve essere superiore a 3MB")

        except AttributeError:

            pass

        return id_card_scan


class GroupAdminForm(forms.ModelForm):

    class Meta:
        model = Group
        exclude = []

    # Add the users field.
    users = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.all(),
        required=False,
        # Use the pretty 'filter_horizontal widget'.
        widget=FilteredSelectMultiple('users', False),
    )

    # def __init__(self, *args, **kwargs):
    #     instance = kwargs.get('instance', None)
    #     if instance is not None:
    #         initial = kwargs.get('initial', {})
    #         initial['users'] = instance.user_set.all()
    #         kwargs['initial'] = initial
    #     super(GroupAdminForm, self).__init__(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        # Do the normal form initialisation.
        super(GroupAdminForm, self).__init__(*args, **kwargs)
        # If it is an existing group (saved objects have a pk).
        if self.instance.pk:
            # Populate the users field with the current Group users.
            self.fields['users'].initial = self.instance.user_set.all()

    def save_m2m(self):
        # Add the users to the Group.
        self.instance.user_set.set(self.cleaned_data['users'])

    def save(self, *args, **kwargs):
        # Default save
        instance = super(GroupAdminForm, self).save()
        # Save many-to-many data
        self.save_m2m()
        return instance


