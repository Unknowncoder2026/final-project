from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction


# =========================================================
# DEPARTMENT MODEL
# =========================================================

class Department(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# =========================================================
# DOCTOR MODEL
# =========================================================

class Doctor(models.Model):

    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    name = models.CharField(
        max_length=100
    )

    email = models.EmailField(
        blank=True
    )

    specialization = models.CharField(
        max_length=100
    )

    qualification = models.CharField(
        max_length=150,
        blank=True
    )

    medical_registration_number = models.CharField(
        max_length=100,
        blank=True
    )

    experience = models.PositiveIntegerField(
        default=0,
        help_text="Experience in years"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doctors"
    )

    phone = models.CharField(
        max_length=15
    )

    aadhaar_number = models.CharField(
        max_length=12,
        blank=True
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    joining_date = models.DateField(
        null=True,
        blank=True
    )

    photo = models.ImageField(
        upload_to="doctors/",
        blank=True,
        null=True
    )

    fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# =========================================================
# PATIENT MODEL
# =========================================================

class Patient(models.Model):

    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    BLOOD_GROUP_CHOICES = [
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
    ]

    name = models.CharField(
        max_length=100
    )

    email = models.EmailField(
        blank=True
    )

    age = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True
    )

    phone = models.CharField(
        max_length=15
    )

    aadhaar_number = models.CharField(
        max_length=12,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    blood_group = models.CharField(
        max_length=5,
        choices=BLOOD_GROUP_CHOICES,
        blank=True
    )

    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True
    )

    emergency_contact_phone = models.CharField(
        max_length=15,
        blank=True
    )

    photo = models.ImageField(
        upload_to="patients/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


# =========================================================
# USER PROFILE / ROLE MODEL
# =========================================================

class UserProfile(models.Model):

    ROLE_CHOICES = [
        ("Staff", "Staff"),
        ("Doctor", "Doctor"),
        ("Nurse", "Nurse"),
        ("Patient", "Patient"),
    ]

    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="userprofile"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="Patient"
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    aadhaar_number = models.CharField(
        max_length=12,
        blank=True
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    qualification = models.CharField(
        max_length=150,
        blank=True
    )

    experience = models.PositiveIntegerField(
        default=0,
        help_text="Experience in years"
    )

    designation = models.CharField(
        max_length=100,
        blank=True
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_profiles"
    )

    joining_date = models.DateField(
        null=True,
        blank=True
    )

    profile_photo = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True
    )

    is_approved = models.BooleanField(
        default=False,
        help_text=(
            "Doctor, Nurse and Staff accounts "
            "require admin approval."
        )
    )

    doctor_profile = models.OneToOneField(
        "Doctor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_profile"
    )

    patient_profile = models.OneToOneField(
        "Patient",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_profile"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    @property
    def can_login_to_role_dashboard(self):

        if self.role == "Patient":
            return True

        return self.is_approved


# =========================================================
# APPOINTMENT MODEL
# =========================================================

class Appointment(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    appointment_date = models.DateField()

    appointment_time = models.TimeField()

    symptoms = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    class Meta:
        ordering = [
            "-appointment_date",
            "-appointment_time"
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "doctor",
                    "appointment_date",
                    "appointment_time",
                ],
                condition=models.Q(
                    status__in=["Pending", "Completed"]
                ),
                name="unique_active_doctor_slot",
            )
        ]

    def clean(self):
        from django.utils import timezone

        if self.appointment_date and self.appointment_date < timezone.localdate():
            raise ValidationError({
                "appointment_date": "Appointment date cannot be in the past."
            })

        if self.doctor_id and not self.doctor.is_active:
            raise ValidationError({
                "doctor": "This doctor is currently unavailable."
            })

    def __str__(self):
        return f"{self.patient} - {self.doctor}"


# =========================================================
# BILLING MODEL
# =========================================================

class Billing(models.Model):

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="bills"
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="bills"
    )

    bill_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    doctor_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    medicine_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    test_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    other_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    bill_date = models.DateField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-id"]

    def save(self, *args, **kwargs):

        self.doctor_fee = self.doctor.fee

        self.total_amount = (
            self.doctor_fee
            + self.medicine_charge
            + self.test_charge
            + self.other_charge
        )

        if not self.bill_number:

            last_bill = (
                Billing.objects
                .order_by("-id")
                .first()
            )

            next_number = (
                last_bill.id + 1
                if last_bill
                else 1
            )

            self.bill_number = (
                f"BILL{next_number:04d}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.bill_number


# =========================================================
# MEDICINE MODEL
# =========================================================

class Medicine(models.Model):

    STATUS_CHOICES = [
        ("Available", "Available"),
        ("Out of Stock", "Out of Stock"),
        ("Expired", "Expired"),
    ]

    medicine_name = models.CharField(
        max_length=100
    )

    company_name = models.CharField(
        max_length=100
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    expiry_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Available"
    )

    class Meta:
        ordering = ["medicine_name"]

    def __str__(self):
        return self.medicine_name


# =========================================================
# LABORATORY MODEL
# =========================================================

class Laboratory(models.Model):

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="laboratory_tests"
    )

    test_name = models.CharField(
        max_length=100
    )

    test_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    test_result = models.TextField(
        blank=True
    )

    test_date = models.DateField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-test_date", "-id"]

    def __str__(self):
        return f"{self.test_name} - {self.patient}"


# =========================================================
# MEDICINE ISSUE MODEL
# =========================================================

class MedicineIssue(models.Model):

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="medicine_issues"
    )

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name="issue_records"
    )

    quantity = models.PositiveIntegerField()

    issue_date = models.DateField(
        auto_now_add=True
    )

    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_medicines"
    )

    class Meta:
        ordering = ["-id"]

    def clean(self):

        if self.quantity <= 0:

            raise ValidationError(
                {
                    "quantity":
                    "Quantity must be greater than zero."
                }
            )

        if self.pk is None and self.medicine_id:

            if self.quantity > self.medicine.stock:

                raise ValidationError(
                    {
                        "quantity": (
                            f"Only {self.medicine.stock} "
                            "medicine available in stock."
                        )
                    }
                )

    @transaction.atomic
    def save(self, *args, **kwargs):

        is_new = self.pk is None

        if is_new:

            medicine = (
                Medicine.objects
                .select_for_update()
                .get(pk=self.medicine_id)
            )

            if self.quantity <= 0:
                raise ValidationError(
                    "Quantity must be greater than zero."
                )

            if self.quantity > medicine.stock:

                raise ValidationError(
                    f"Only {medicine.stock} "
                    "medicine available in stock."
                )

            medicine.stock -= self.quantity

            if medicine.stock == 0:

                medicine.status = "Out of Stock"

            elif medicine.status == "Out of Stock":

                medicine.status = "Available"

            medicine.save(
                update_fields=[
                    "stock",
                    "status"
                ]
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient} - {self.medicine}"


# =========================================================
# STAFF PROFILE MODEL
# =========================================================

class StaffProfile(models.Model):

    user_profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="staff_details"
    )

    employee_id = models.CharField(
        max_length=30,
        unique=True
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_members"
    )

    designation = models.CharField(
        max_length=100,
        blank=True
    )

    qualification = models.CharField(
        max_length=150,
        blank=True
    )

    experience = models.PositiveIntegerField(
        default=0,
        help_text="Experience in years"
    )

    joining_date = models.DateField(
        null=True,
        blank=True
    )

    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    aadhaar_number = models.CharField(
        max_length=12,
        blank=True
    )

    def clean(self):

        if self.user_profile.role != "Staff":

            raise ValidationError(
                "Only a Staff role account "
                "can have a Staff Profile."
            )

    def __str__(self):

        name = (
            self.user_profile.user
            .get_full_name()
        )

        if not name:
            name = (
                self.user_profile.user.username
            )

        return f"{self.employee_id} - {name}"


# =========================================================
# NURSE PROFILE MODEL
# =========================================================

class NurseProfile(models.Model):

    SHIFT_CHOICES = [
        ("Morning", "Morning"),
        ("Evening", "Evening"),
        ("Night", "Night"),
    ]

    user_profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="nurse_details"
    )

    employee_id = models.CharField(
        max_length=30,
        unique=True
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nurses"
    )

    qualification = models.CharField(
        max_length=150,
        blank=True
    )

    nursing_registration_number = models.CharField(
        max_length=100,
        blank=True
    )

    experience = models.PositiveIntegerField(
        default=0,
        help_text="Experience in years"
    )

    aadhaar_number = models.CharField(
        max_length=12,
        blank=True
    )

    shift = models.CharField(
        max_length=20,
        choices=SHIFT_CHOICES,
        default="Morning"
    )

    joining_date = models.DateField(
        null=True,
        blank=True
    )

    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    def clean(self):

        if self.user_profile.role != "Nurse":

            raise ValidationError(
                "Only a Nurse role account "
                "can have a Nurse Profile."
            )

    def __str__(self):

        name = (
            self.user_profile.user
            .get_full_name()
        )

        if not name:
            name = (
                self.user_profile.user.username
            )

        return f"{self.employee_id} - {name}"


# =========================================================
# OTP VERIFICATION MODEL
# =========================================================

class OTPVerification(models.Model):

    PURPOSE_CHOICES = [
        ("Registration", "Registration"),
        ("Forgot Password", "Forgot Password"),
        ("Mobile Verification", "Mobile Verification"),
        ("Email Verification", "Email Verification"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="otp_verifications"
    )

    otp_code = models.CharField(
        max_length=6
    )

    purpose = models.CharField(
        max_length=30,
        choices=PURPOSE_CHOICES
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    expires_at = models.DateTimeField()

    is_verified = models.BooleanField(
        default=False
    )

    attempt_count = models.PositiveIntegerField(
        default=0
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):

        return (
            f"{self.user.username} - "
            f"{self.purpose}"
        )

    def is_expired(self):

        from django.utils import timezone

        return timezone.now() > self.expires_at