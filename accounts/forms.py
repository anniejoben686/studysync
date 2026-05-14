import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from lms_core.models import User, StudentProfile


class StudentRegistrationForm(UserCreationForm):
    """Student self-registration form with comprehensive validation."""

    GENDER_CHOICES = [('', '-- Select Gender --'), ('Male', 'Male'), ('Female', 'Female')]
    CLASS_CHOICES = [('', '-- Select Class --'), (8, 'Class 8'), (9, 'Class 9'), (10, 'Class 10')]

    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your full name',
            'autocomplete': 'off',
        })
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=True,
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email address',
            'autocomplete': 'off',
        })
    )
    phone_number = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter 10-digit phone number',
            'autocomplete': 'off',
            'inputmode': 'numeric',
            'maxlength': '10',
        })
    )
    current_class = forms.ChoiceField(
        choices=CLASS_CHOICES,
        required=True,
    )
    username = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Choose a username',
            'autocomplete': 'off',
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['full_name', 'gender', 'email', 'phone_number', 'current_class',
                  'username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'placeholder': 'Create a strong password'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm your password'})
        # Clear default Django help texts
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
        self.fields['username'].help_text = ''

    # ── Field-level validators ────────────────────────────────────────────────

    def clean_full_name(self):
        value = self.cleaned_data.get('full_name', '').strip()
        if len(value) < 3:
            raise forms.ValidationError('Enter a valid full name (minimum 3 characters).')
        if not re.match(r'^[A-Za-z ]+$', value):
            raise forms.ValidationError('Enter a valid full name using letters only.')
        return value

    def clean_gender(self):
        value = self.cleaned_data.get('gender', '')
        if not value:
            raise forms.ValidationError('Please select a gender.')
        if value not in ('Male', 'Female'):
            raise forms.ValidationError('Please select a valid gender option.')
        return value

    def clean_email(self):
        value = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=value).exists():
            raise forms.ValidationError('This email address is already registered.')
        return value

    def clean_phone_number(self):
        value = self.cleaned_data.get('phone_number', '').strip()
        if not re.match(r'^\d{10}$', value):
            raise forms.ValidationError('Enter a valid 10-digit phone number.')
        if value[0] not in ('6', '7', '8', '9'):
            raise forms.ValidationError('Enter a valid 10-digit phone number.')
        if StudentProfile.objects.filter(phone_number=value).exists():
            raise forms.ValidationError('This phone number is already registered.')
        return value

    def clean_current_class(self):
        value = self.cleaned_data.get('current_class', '')
        if not value:
            raise forms.ValidationError('Please select your class.')
        return value

    def clean_username(self):
        value = self.cleaned_data.get('username', '').strip().lower()
        if len(value) < 4:
            raise forms.ValidationError('Username must be at least 4 characters long.')
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', value):
            raise forms.ValidationError(
                'Username can only contain letters, numbers, and underscores, and must start with a letter.'
            )
        if User.objects.filter(username=value).exists():
            raise forms.ValidationError('Username already exists.')
        return value

    def clean_password1(self):
        password = self.cleaned_data.get('password1', '')
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError(
                'Password must contain uppercase, lowercase, number, and special character.'
            )
        if not re.search(r'[a-z]', password):
            raise forms.ValidationError(
                'Password must contain uppercase, lowercase, number, and special character.'
            )
        if not re.search(r'\d', password):
            raise forms.ValidationError(
                'Password must contain uppercase, lowercase, number, and special character.'
            )
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-\+=/\\;\[\]\'`~]', password):
            raise forms.ValidationError(
                'Password must contain uppercase, lowercase, number, and special character.'
            )
        return password

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1', '')
        p2 = self.cleaned_data.get('password2', '')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'STUDENT'
        user.email = self.cleaned_data.get('email', '')

        # Split full name into first/last for the User model
        full_name = self.cleaned_data.get('full_name', '')
        parts = full_name.split(' ', 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ''

        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                current_class=self.cleaned_data.get('current_class'),
                gender=self.cleaned_data.get('gender'),
                phone_number=self.cleaned_data.get('phone_number'),
            )
        return user


class AdminUserCreateForm(UserCreationForm):
    """Form for admin to create instructor accounts."""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'INSTRUCTOR'
        user.email = self.cleaned_data.get('email', '')
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
        return user


class StudentAdminLoginForm(AuthenticationForm):
    def clean(self):
        cleaned_data = super().clean()
        user = self.get_user()
        if user is not None:
            if user.role == 'INSTRUCTOR':
                raise forms.ValidationError("Instructors must log in through the Instructor portal.")
        return cleaned_data


class InstructorLoginForm(AuthenticationForm):
    def clean(self):
        cleaned_data = super().clean()
        user = self.get_user()
        if user is not None:
            if user.role != 'INSTRUCTOR':
                raise forms.ValidationError("Only Instructors can log in through this portal.")
        return cleaned_data
