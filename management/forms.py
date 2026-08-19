from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import (
    Appointment,
    Department,
    Billing,
    Doctor,
    Laboratory,
    Medicine,
    MedicineIssue,
    Patient,
    UserProfile,
)

User = get_user_model()


# =========================================================
# PUBLIC REGISTRATION FORM
# =========================================================

class RegisterForm(UserCreationForm):

    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter first name",
            }
        ),
    )

    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter last name",
            }
        ),
    )

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter email address",
            }
        ),
    )

    # =====================================================
    # ROLE
    # ADMIN OPTION NAHI HAI
    # =====================================================

    role = forms.ChoiceField(
        choices=[
            ("Patient", "Patient"),
            ("Doctor", "Doctor"),
            ("Nurse", "Nurse"),
            ("Staff", "Staff"),
        ],
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter mobile number",
                "maxlength": "15",
                "inputmode": "numeric",
            }
        ),
    )

    # =====================================================
    # AADHAAR
    # =====================================================

    aadhaar_number = forms.CharField(
        max_length=12,
        min_length=12,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter 12 digit Aadhaar number",
                "maxlength": "12",
                "inputmode": "numeric",
            }
        ),
    )

    address = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Enter address",
                "rows": 3,
            }
        ),
    )

    # =====================================================
    # CAPTCHA
    # =====================================================

    captcha = forms.CharField(
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter captcha code",
                "autocomplete": "off",
                "maxlength": "6",
            }
        ),
    )

    class Meta:

        model = User

        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "phone",
            "aadhaar_number",
            "address",
            "password1",
            "password2",
        ]

    # =====================================================
    # INITIAL SETTINGS
    # =====================================================

    def __init__(self, *args, **kwargs):

        captcha_code = kwargs.pop(
            "captcha_code",
            None
        )

        super().__init__(
            *args,
            **kwargs
        )

        self.captcha_code = captcha_code

        self.fields["username"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Choose username",
                "autocomplete": "username",
            }
        )

        self.fields["password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Create password",
                "autocomplete": "new-password",
            }
        )

        self.fields["password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Confirm password",
                "autocomplete": "new-password",
            }
        )

    # =====================================================
    # EMAIL VALIDATION
    # =====================================================

    def clean_email(self):

        email = (
            self.cleaned_data["email"]
            .strip()
            .lower()
        )

        if User.objects.filter(
            email__iexact=email
        ).exists():

            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    # =====================================================
    # PHONE VALIDATION
    # =====================================================

    def clean_phone(self):

        phone = (
            self.cleaned_data["phone"]
            .strip()
        )

        cleaned_phone = (
            phone
            .replace(" ", "")
            .replace("-", "")
        )

        if not cleaned_phone.replace(
            "+",
            "",
            1
        ).isdigit():

            raise forms.ValidationError(
                "Enter a valid mobile number."
            )

        return phone

    # =====================================================
    # AADHAAR VALIDATION
    # =====================================================

    def clean_aadhaar_number(self):

        aadhaar = (
            self.cleaned_data["aadhaar_number"]
            .replace(" ", "")
            .replace("-", "")
        )

        if not aadhaar.isdigit():

            raise forms.ValidationError(
                "Aadhaar number must contain only digits."
            )

        if len(aadhaar) != 12:

            raise forms.ValidationError(
                "Aadhaar number must be exactly 12 digits."
            )

        if UserProfile.objects.filter(
            aadhaar_number=aadhaar
        ).exists():

            raise forms.ValidationError(
                "This Aadhaar number is already registered."
            )

        return aadhaar

    # =====================================================
    # CAPTCHA VALIDATION
    # =====================================================

    def clean_captcha(self):

        captcha = (
            self.cleaned_data["captcha"]
            .strip()
            .upper()
        )

        if not self.captcha_code:

            raise forms.ValidationError(
                "Captcha expired. Please refresh the page."
            )

        if captcha != self.captcha_code:

            raise forms.ValidationError(
                "Invalid captcha code."
            )

        return captcha

    # =====================================================
    # SAVE USER + PROFILE + PATIENT/DOCTOR
    # =====================================================

    def save(self, commit=True):

        user = super().save(
            commit=False
        )

        user.first_name = (
            self.cleaned_data["first_name"]
            .strip()
        )

        user.last_name = (
            self.cleaned_data["last_name"]
            .strip()
        )

        user.email = (
            self.cleaned_data["email"]
            .strip()
            .lower()
        )

        role = self.cleaned_data["role"]

        # User active rahega.
        # Dashboard access approval se control hoga.
        user.is_active = True

        if commit:

            # =================================================
            # CREATE USER
            # =================================================

            user.save()

            # =================================================
            # CREATE USER PROFILE
            # =================================================

            profile = UserProfile.objects.create(

                user=user,

                role=role,

                phone=self.cleaned_data["phone"],

                email=self.cleaned_data["email"],

                aadhaar_number=self.cleaned_data[
                    "aadhaar_number"
                ],

                address=self.cleaned_data[
                    "address"
                ],

                # Patient direct login
                # Doctor/Nurse/Staff approval required
                is_approved=(
                    role == "Patient"
                ),
            )

            # =================================================
            # PATIENT REGISTRATION
            # =================================================

            if role == "Patient":

                patient = Patient.objects.create(

                    name=(
                        user.get_full_name().strip()
                        or user.username
                    ),

                    email=user.email,

                    phone=self.cleaned_data[
                        "phone"
                    ],

                    aadhaar_number=self.cleaned_data[
                        "aadhaar_number"
                    ],

                    address=self.cleaned_data[
                        "address"
                    ],
                )

                profile.patient_profile = patient

                profile.save(
                    update_fields=[
                        "patient_profile"
                    ]
                )

            # =================================================
            # DOCTOR REGISTRATION
            # =================================================

            elif role == "Doctor":

                doctor = Doctor.objects.create(

                    name=(
                        user.get_full_name().strip()
                        or user.username
                    ),

                    email=user.email,

                    specialization="General Medicine",

                    phone=self.cleaned_data[
                        "phone"
                    ],

                    aadhaar_number=self.cleaned_data[
                        "aadhaar_number"
                    ],

                    address=self.cleaned_data[
                        "address"
                    ],

                    fee=0,
                )

                profile.doctor_profile = doctor

                profile.save(
                    update_fields=[
                        "doctor_profile"
                    ]
                )

            # =================================================
            # NURSE
            # =================================================
            # Nurse ke liye NurseProfile baad me
            # admin/staff details se create kiya ja sakta hai.
            # Abhi UserProfile me role save hoga.

            elif role == "Nurse":

                profile.save()

            # =================================================
            # STAFF
            # =================================================
            # Staff ke liye StaffProfile baad me
            # admin/staff details se create kiya ja sakta hai.

            elif role == "Staff":

                profile.save()

        return user


# =========================================================
# DOCTOR FORM
# =========================================================

class DoctorForm(forms.ModelForm):

    class Meta:

        model = Doctor

        fields = [
            "name",
            "email",
            "specialization",
            "qualification",
            "medical_registration_number",
            "experience",
            "department",
            "phone",
            "aadhaar_number",
            "date_of_birth",
            "gender",
            "address",
            "joining_date",
            "photo",
            "fee",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter doctor name"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter email"}),
            "specialization": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter specialization"}),
            "qualification": forms.TextInput(attrs={"class": "form-control", "placeholder": "MBBS, MD, etc."}),
            "medical_registration_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Registration number"}),
            "experience": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "department": forms.Select(attrs={"class": "form-select"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter phone number", "maxlength": "15"}),
            "aadhaar_number": forms.TextInput(attrs={"class": "form-control", "maxlength": "12", "inputmode": "numeric"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "joining_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "fee": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Consultation fee", "min": "0", "step": "0.01"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].queryset = Department.objects.filter(is_active=True).order_by("name")
        self.fields["gender"].choices = [
            ("", "Select gender"),
            ("Male", "Male"),
            ("Female", "Female"),
            ("Other", "Other"),
        ]


# =========================================================
# PATIENT FORM
# =========================================================

class PatientForm(forms.ModelForm):

    class Meta:

        model = Patient

        fields = [
            "name",
            "age",
            "gender",
            "phone",
            "address",
        ]

        widgets = {

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter patient name",
                }
            ),

            "age": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter age",
                    "min": "0",
                }
            ),

            "gender": forms.Select(
    choices=[
        (",", "Select Gender"),
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ],
    attrs={
        "class": "form-select",
    }
),

            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter phone number",
                }
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter address",
                    "rows": 3,
                }
            ),
        }


# =========================================================
# APPOINTMENT FORM
# =========================================================

class AppointmentForm(forms.ModelForm):

    class Meta:

        model = Appointment

        fields = [
            "patient",
            "doctor",
            "appointment_date",
            "appointment_time",
            "symptoms",
            "status",
        ]

        widgets = {

            "patient": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "doctor": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "appointment_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "appointment_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),

            "symptoms": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter symptoms",
                    "rows": 3,
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),
        }


# =========================================================
# BILLING FORM
# =========================================================

class BillingForm(forms.ModelForm):

    class Meta:

        model = Billing

        fields = [
            "patient",
            "doctor",
            "medicine_charge",
            "test_charge",
            "other_charge",
        ]

        widgets = {

            "patient": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "doctor": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "medicine_charge": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter medicine charge",
                    "min": "0",
                }
            ),

            "test_charge": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter test charge",
                    "min": "0",
                }
            ),

            "other_charge": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter other charge",
                    "min": "0",
                }
            ),
        }


# =========================================================
# MEDICINE FORM
# =========================================================

class MedicineForm(forms.ModelForm):

    class Meta:

        model = Medicine

        fields = [
            "medicine_name",
            "company_name",
            "price",
            "stock",
            "expiry_date",
            "status",
        ]

        widgets = {

            "medicine_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter medicine name",
                }
            ),

            "company_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter company name",
                }
            ),

            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter price",
                    "min": "0",
                }
            ),

            "stock": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter stock quantity",
                    "min": "0",
                }
            ),

            "expiry_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),
        }


# =========================================================
# LABORATORY FORM
# =========================================================

class LaboratoryForm(forms.ModelForm):

    class Meta:

        model = Laboratory

        fields = [
            "patient",
            "test_name",
            "test_charge",
            "test_result",
        ]

        widgets = {

            "patient": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "test_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter test name",
                }
            ),

            "test_charge": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter test charge",
                    "min": "0",
                }
            ),

            "test_result": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter test result",
                    "rows": 4,
                }
            ),
        }


# =========================================================
# MEDICINE ISSUE FORM
# =========================================================

class MedicineIssueForm(forms.ModelForm):

    class Meta:

        model = MedicineIssue

        fields = [
            "patient",
            "medicine",
            "quantity",
        ]

        widgets = {

            "patient": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "medicine": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter quantity",
                    "min": "1",
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        medicine = cleaned_data.get(
            "medicine"
        )

        quantity = cleaned_data.get(
            "quantity"
        )

        if medicine and quantity:

            if quantity > medicine.stock:
                
                raise forms.ValidationError(
                    f"Only {medicine.stock} medicine "
                    f"available in stock."
                )

        return cleaned_data
class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "name",
            "email",
            "age",
            "date_of_birth",
            "gender",
            "phone",
            "aadhaar_number",
            "address",
            "blood_group",
            "emergency_contact_name",
            "emergency_contact_phone",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control"
            }),
            "age": forms.NumberInput(attrs={
                "class": "form-control"
            }),
            "date_of_birth": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date"
                }
            ),
            "gender": forms.Select(attrs={
                "class": "form-control"
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-control"
            }),
            "aadhaar_number": forms.TextInput(attrs={
                "class": "form-control",
                "maxlength": "12"
            }),
            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),
            "blood_group": forms.Select(attrs={
                "class": "form-control"
            }),
            "emergency_contact_name": forms.TextInput(attrs={
                "class": "form-control"
            }),
            "emergency_contact_phone": forms.TextInput(attrs={
                "class": "form-control"
            }),
        }
class PatientAppointmentForm(forms.ModelForm):

    class Meta:
        model = Appointment

        fields = [
            "doctor",
            "appointment_date",
            "appointment_time",
            "symptoms",
        ]

        widgets = {
            "doctor": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_doctor",
                }
            ),

            "appointment_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "appointment_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),

            "symptoms": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Describe your symptoms...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["doctor"].queryset = (
            Doctor.objects
            .filter(is_active=True)
            .select_related("department")
            .order_by("name")
        )
        self.fields["doctor"].label = "Doctor"
        self.fields["appointment_date"].label = "Appointment date"
        self.fields["appointment_time"].label = "Available time"

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get("doctor")
        appointment_date = cleaned_data.get("appointment_date")
        appointment_time = cleaned_data.get("appointment_time")

        if appointment_date and appointment_date < timezone.localdate():
            self.add_error(
                "appointment_date",
                "Appointment date cannot be in the past."
            )

        if doctor and not doctor.is_active:
            self.add_error(
                "doctor",
                "This doctor is currently unavailable."
            )

        if doctor and appointment_date and appointment_time:
            if Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status__in=["Pending", "Completed"],
            ).exists():
                self.add_error(
                    "appointment_time",
                    "This time slot is already booked. Please choose another time."
                )

        return cleaned_data