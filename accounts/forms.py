# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile


class RegisterForm(UserCreationForm):
    user_type = forms.ChoiceField(
        choices=Profile.USER_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Register as"
    )

    class Meta:
        model = User
        fields = [
            "username",
            "password1",
            "password2",
            "user_type",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: nicer appearance / placeholders
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username',
            'autofocus': True,
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password',
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        # No email → we leave user.email empty (or set to '' if you want)
        user.email = ''
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                user_type=self.cleaned_data["user_type"]
            )
        return user

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
        })
    )