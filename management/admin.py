from django.contrib import admin

from .models import (
    Appointment,
    Billing,
    Department,
    Doctor,
    Laboratory,
    Medicine,
    MedicineIssue,
    NurseProfile,
    OTPVerification,
    Patient,
    StaffProfile,
    UserProfile,
)


# ==========================================
# Admin Panel Heading
# ==========================================

admin.site.site_header = "City Care Hospital Administration"
admin.site.site_title = "City Care Hospital Admin"
admin.site.index_title = "Hospital Management Control Panel"


# ==========================================
# Doctor Admin
# ==========================================

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "specialization",
        "phone",
        "fee",
    )

    search_fields = (
        "name",
        "specialization",
        "phone",
    )


# ==========================================
# Patient Admin
# ==========================================

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "age",
        "gender",
        "phone",
    )

    search_fields = (
        "name",
        "phone",
        "address",
    )

    list_filter = (
        "gender",
    )


# ==========================================
# Appointment Admin
# ==========================================

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "doctor",
        "appointment_date",
        "appointment_time",
        "status",
    )

    search_fields = (
        "patient__name",
        "doctor__name",
        "status",
    )

    list_filter = (
        "status",
        "appointment_date",
        "doctor",
    )


# ==========================================
# Billing Admin
# ==========================================

@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = (
        "bill_number",
        "patient",
        "doctor",
        "total_amount",
        "bill_date",
    )

    search_fields = (
        "bill_number",
        "patient__name",
        "doctor__name",
    )

    list_filter = (
        "bill_date",
        "doctor",
    )

    readonly_fields = (
        "bill_number",
        "doctor_fee",
        "total_amount",
        "bill_date",
    )


# ==========================================
# Medicine Admin
# ==========================================

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = (
        "medicine_name",
        "company_name",
        "price",
        "stock",
        "expiry_date",
        "status",
    )

    search_fields = (
        "medicine_name",
        "company_name",
    )

    list_filter = (
        "status",
        "expiry_date",
    )


# ==========================================
# Medicine Issue Admin
# ==========================================

@admin.register(MedicineIssue)
class MedicineIssueAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "medicine",
        "quantity",
        "issue_date",
        "issued_by",
    )

    search_fields = (
        "patient__name",
        "medicine__medicine_name",
        "issued_by__username",
    )

    list_filter = (
        "issue_date",
        "medicine",
    )

    readonly_fields = (
        "issue_date",
    )


# ==========================================
# Laboratory Admin
# ==========================================

@admin.register(Laboratory)
class LaboratoryAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "test_name",
        "test_charge",
        "test_date",
    )

    search_fields = (
        "patient__name",
        "test_name",
        "test_result",
    )

    list_filter = (
        "test_date",
        "test_name",
    )

    readonly_fields = (
        "test_date",
    )


# ==========================================
# Department Admin
# ==========================================

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
    )

    list_filter = (
        "is_active",
    )

    readonly_fields = (
        "created_at",
    )


# ==========================================
# User Profile Admin
# ==========================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "role",
        "phone",
        "is_approved",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "phone",
    )

    list_filter = (
        "role",
        "is_approved",
    )

    list_editable = (
        "is_approved",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


# ==========================================
# Staff Profile Admin
# ==========================================

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = (
        "employee_id",
        "user_profile",
        "department",
        "designation",
        "joining_date",
        "salary",
    )

    search_fields = (
        "employee_id",
        "user_profile__user__username",
        "designation",
    )

    list_filter = (
        "department",
        "joining_date",
    )


# ==========================================
# Nurse Profile Admin
# ==========================================

@admin.register(NurseProfile)
class NurseProfileAdmin(admin.ModelAdmin):
    list_display = (
        "employee_id",
        "user_profile",
        "department",
        "qualification",
        "shift",
        "joining_date",
        "salary",
    )

    search_fields = (
        "employee_id",
        "user_profile__user__username",
        "qualification",
    )

    list_filter = (
        "department",
        "shift",
        "joining_date",
    )


# ==========================================
# OTP Verification Admin
# ==========================================

@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "purpose",
        "otp_code",
        "is_verified",
        "attempt_count",
        "created_at",
        "expires_at",
    )

    search_fields = (
        "user__username",
        "user__email",
    )

    list_filter = (
        "purpose",
        "is_verified",
    )

    readonly_fields = (
        "created_at",
    )