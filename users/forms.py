from django import forms
from django.contrib.auth import get_user_model
from allauth.account.forms import SignupForm


User = get_user_model()


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=150,
        label="Ten",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ten"}),
    )
    last_name = forms.CharField(
        max_length=150,
        label="Ho",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ho"}),
    )
    phone_number = forms.CharField(
        max_length=30,
        label="So dien thoai",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "So dien thoai"}),
    )

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.phone_number = self.cleaned_data["phone_number"].strip()
        user.save(update_fields=["first_name", "last_name", "phone_number"])
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "city",
            "country",
            "date_of_birth",
            "gender",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.TextInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ("first_name", "last_name", "email", "phone_number"):
            self.fields[field_name].required = True
            self.fields[field_name].widget.attrs["required"] = True
        for field_name in ("city", "country", "date_of_birth", "gender"):
            self.fields[field_name].required = False
            self.fields[field_name].widget.attrs.pop("required", None)
