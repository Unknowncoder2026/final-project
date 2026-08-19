from datetime import date, timedelta
from functools import wraps
import random
import string

from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
)
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    AppointmentForm,
    BillingForm,
    DoctorForm,
    LaboratoryForm,
    MedicineForm,
    MedicineIssueForm,
    PatientForm,
    RegisterForm,
    PatientProfileForm,
    PatientAppointmentForm,
)

from .models import (
    Appointment,
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
# SECURITY / ROLE HELPERS
# =========================================================

def is_admin(user):
    """
    Sirf Django Superuser ko Admin maana jayega.
    """
    return (
        user.is_authenticated
        and user.is_active
        and user.is_staff
        and user.is_superuser
    )


def role_or_admin_required(allowed_roles):
    """Allow the named operational roles plus Django superuser."""
    def decorator(view_function):
        @wraps(view_function)
        @login_required(login_url="login")
        def wrapper(request, *args, **kwargs):
            if is_admin(request.user):
                return view_function(request, *args, **kwargs)
            try:
                profile = request.user.userprofile
            except UserProfile.DoesNotExist:
                messages.error(request, "Your account role is not configured.")
                return redirect("dashboard")
            if not profile.can_login_to_role_dashboard:
                messages.warning(request, "Your account is waiting for admin approval.")
                return redirect("login")
            if profile.role not in allowed_roles:
                messages.error(request, "You do not have permission to open this page.")
                return redirect_user_by_role(request.user)
            return view_function(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_function):
    """
    Sirf Admin/Superuser admin pages open kar sakta hai.
    """
    @wraps(view_function)
    @login_required(login_url="login")
    def wrapper(request, *args, **kwargs):

        if not is_admin(request.user):
            messages.error(
                request,
                "You do not have permission to open the Admin Panel."
            )
            return redirect("dashboard")

        return view_function(request, *args, **kwargs)

    return wrapper


def role_required(allowed_roles):
    """
    Example:
        @role_required(["Patient"])
        @role_required(["Doctor"])
    """

    def decorator(view_function):

        @wraps(view_function)
        @login_required(login_url="login")
        def wrapper(request, *args, **kwargs):

            # Admin ko bhi normal role pages par allow nahi karna.
            # Admin ka apna dashboard hai.
            if request.user.is_superuser:
                return redirect("dashboard")

            try:
                profile = request.user.userprofile

            except UserProfile.DoesNotExist:

                messages.error(
                    request,
                    "Your account role is not configured."
                )

                logout(request)

                return redirect("login")

            # Approval check
            if not profile.can_login_to_role_dashboard:

                messages.warning(
                    request,
                    "Your account is waiting for admin approval."
                )

                logout(request)

                return redirect("login")

            # Role check
            if profile.role not in allowed_roles:

                messages.error(
                    request,
                    "You do not have permission to open this page."
                )

                return redirect_user_by_role(
                    request.user
                )

            return view_function(
                request,
                *args,
                **kwargs
            )

        return wrapper

    return decorator


def generate_captcha():

    characters = (
        string.ascii_uppercase
        + string.digits
    )

    return "".join(
        random.choices(
            characters,
            k=6
        )
    )


# =========================================================
# ROLE REDIRECT
# =========================================================

def redirect_user_by_role(user):

    """
    Login ke baad har user ko uske apne dashboard par bhejta hai.

    Admin      -> dashboard
    Doctor     -> doctor_dashboard
    Nurse      -> nurse_dashboard
    Staff      -> staff_dashboard
    Patient    -> patient_dashboard
    """

    # -----------------------------------------------------
    # ADMIN
    # -----------------------------------------------------

    if user.is_superuser:
        return redirect("dashboard")

    try:
        profile = user.userprofile

    except UserProfile.DoesNotExist:
        return redirect("dashboard")

    # -----------------------------------------------------
    # APPROVAL
    # -----------------------------------------------------

    if not profile.can_login_to_role_dashboard:
        return None

    # -----------------------------------------------------
    # DOCTOR
    # -----------------------------------------------------

    if profile.role == "Doctor":
        return redirect("doctor_dashboard")

    # -----------------------------------------------------
    # NURSE
    # -----------------------------------------------------

    if profile.role == "Nurse":
        return redirect("nurse_dashboard")

    # -----------------------------------------------------
    # STAFF
    # -----------------------------------------------------

    if profile.role == "Staff":
        return redirect("staff_dashboard")

    # -----------------------------------------------------
    # PATIENT
    # -----------------------------------------------------

    if profile.role == "Patient":
        return redirect("patient_dashboard")

    return redirect("dashboard")


# =========================================================
# PUBLIC HOME
# =========================================================

def user_home(request):

    doctors = Doctor.objects.all()[:4]

    context = {
        "doctors": doctors,
        "doctor_count": Doctor.objects.count(),
        "patient_count": Patient.objects.count(),
        "appointment_count": Appointment.objects.count(),
    }

    return render(
        request,
        "user_home.html",
        context
    )


# =========================================================
# REGISTER
# =========================================================

def register_view(request):

    if request.user.is_authenticated:

        response = redirect_user_by_role(
            request.user
        )

        if response is not None:
            return response

    selected_role = request.session.get(
        "selected_role",
        "Patient"
    )

    captcha_code = request.session.get(
        "registration_captcha"
    )

    if not captcha_code:

        captcha_code = generate_captcha()

        request.session[
            "registration_captcha"
        ] = captcha_code

    if request.method == "POST":

        form = RegisterForm(
            request.POST,
            captcha_code=captcha_code
        )

        if form.is_valid():

            user = form.save()

            request.session.pop(
                "registration_captcha",
                None
            )

            # Role profile
            profile = user.userprofile

            if profile.role == "Patient":

                messages.success(
                    request,
                    "Registration successful. Please login."
                )

            else:

                messages.success(
                    request,
                    (
                        f"Registration successful as "
                        f"{profile.role}. "
                        "Your account is waiting for "
                        "administrator approval."
                    )
                )

            return redirect("login")

    else:

        form = RegisterForm(
            captcha_code=captcha_code
        )

    return render(
        request,
        "register.html",
        {
            "form": form,
            "captcha_code": captcha_code,
            "selected_role": selected_role,
        }
    )


def patient_register(request):

    request.session["selected_role"] = "Patient"

    return redirect("register")


def doctor_register(request):

    request.session["selected_role"] = "Doctor"

    return redirect("register")


def nurse_register(request):

    request.session["selected_role"] = "Nurse"

    return redirect("register")


def staff_register(request):

    request.session["selected_role"] = "Staff"

    return redirect("register")


# =========================================================
# LOGIN
# =========================================================

def login_view(request):

    # Required for an initial GET as well as failed POST requests.
    selected_role = ""

    # Already logged in
    if request.user.is_authenticated:

        response = redirect_user_by_role(
            request.user
        )

        if response is not None:
            return response

    error = ""

    if request.method == "POST":

        identifier = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        selected_role = request.POST.get(
            "role",
            ""
        ).strip()

        allowed_login_roles = {
            "Patient",
            "Doctor",
            "Nurse",
            "Staff",
        }

        if selected_role not in allowed_login_roles:
            error = "Please select your account role before login."
            return render(
                request,
                "login.html",
                {
                    "error": error,
                    "selected_role": selected_role,
                }
            )

        remember_me = request.POST.get(
            "remember_me"
        )

        # -------------------------------------------------
        # USERNAME / EMAIL / MOBILE
        # -------------------------------------------------

        account = (
            User.objects
            .filter(
                Q(username__iexact=identifier)
                |
                Q(email__iexact=identifier)
                |
                Q(
                    userprofile__phone__iexact=identifier
                )
            )
            .distinct()
            .first()
        )

        if account is None:

            error = (
                "Username, mobile number or email is incorrect."
            )

        elif not account.is_active:

            error = (
                "Your account is disabled. "
                "Please contact the administrator."
            )

        else:

            user = authenticate(
                request,
                username=account.username,
                password=password
            )

            if user is None:

                error = "Password is incorrect."

            else:

                # Public login is only for hospital roles. Superusers use
                # Django's protected /admin/ login page.
                if user.is_superuser:
                    error = "Administrator accounts must sign in through the Admin Portal."
                    return render(
                        request,
                        "login.html",
                        {"error": error, "selected_role": selected_role},
                    )

                login(
                    request,
                    user
                )

                # Remember me
                if remember_me:

                    request.session.set_expiry(
                        1209600
                    )

                else:

                    request.session.set_expiry(
                        0
                    )

                # -------------------------------------------------
                # NORMAL USER PROFILE + SELECTED ROLE CHECK
                # -------------------------------------------------

                try:

                    profile = user.userprofile

                except UserProfile.DoesNotExist:

                    logout(request)

                    error = (
                        "Your account role is not configured."
                    )

                else:

                    if profile.role != selected_role:

                        logout(request)

                        error = (
                            f"This account is registered as {profile.role}. "
                            f"Please select {profile.role} to login."
                        )

                    elif not profile.can_login_to_role_dashboard:

                        logout(request)

                        error = (
                            "Your account is waiting "
                            "for admin approval."
                        )

                    else:

                        response = redirect_user_by_role(
                            user
                        )

                        if response is not None:
                            return response

                        logout(request)

                        error = (
                            "Your account role "
                            "is not configured."
                        )

    return render(
        request,
        "login.html",
        {
            "error": error,
            "selected_role": selected_role,
        }
    )


# =========================================================
# FORGOT / RESET PASSWORD
# =========================================================

def forgot_password(request):
    """Demo-friendly password reset using an account identifier.

    The form accepts username, email, or registered mobile number.
    For a real production hospital deployment this should be replaced
    by a verified email/SMS OTP flow; this version keeps the college
    project self-contained and usable without SMTP configuration.
    """
    if request.user.is_authenticated:
        response = redirect_user_by_role(request.user)
        if response is not None:
            return response

    error = ""
    success = ""

    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        account = (
            User.objects
            .filter(
                Q(username__iexact=identifier)
                | Q(email__iexact=identifier)
                | Q(userprofile__phone__iexact=identifier)
            )
            .distinct()
            .first()
        )

        if not identifier:
            error = "Enter your username, email or mobile number."
        elif account is None:
            error = "No account was found with these details."
        elif not password1 or len(password1) < 8:
            error = "New password must contain at least 8 characters."
        elif password1 != password2:
            error = "The two new passwords do not match."
        else:
            account.set_password(password1)
            account.save(update_fields=["password"])
            success = "Password changed successfully. You can now login."

    return render(
        request,
        "forgot_password.html",
        {"error": error, "success": success},
    )


# =========================================================
# LOGOUT
# =========================================================

@login_required(login_url="login")
def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("login")


# =========================================================
# MAIN ADMIN DASHBOARD
# =========================================================

@login_required(login_url="login")
def home(request):

    # -----------------------------------------------------
    # ADMIN ONLY
    # -----------------------------------------------------

    if not request.user.is_superuser:

        # Normal user ko apne dashboard par bhejo
        return redirect_user_by_role(
            request.user
        )

    # -----------------------------------------------------
    # ADMIN RECORDS
    # -----------------------------------------------------

    recent_appointments = (
        Appointment.objects
        .select_related(
            "patient",
            "doctor"
        )
        .order_by(
            "-appointment_date",
            "-appointment_time"
        )[:10]
    )

    total_income = (
        Billing.objects.aggregate(
            total=Sum("total_amount")
        )["total"] or 0
    )

    context = {

        "doctor_count":
            Doctor.objects.count(),

        "patient_count":
            Patient.objects.count(),

        "appointment_count":
            Appointment.objects.count(),

        "medicine_count":
            Medicine.objects.count(),

        "laboratory_count":
            Laboratory.objects.count(),

        "bill_count":
            Billing.objects.count(),

        "total_income":
            total_income,

        "recent_appointments":
            recent_appointments,
    }

    return render(
        request,
        "Home.html",
        context
    )


# =========================================================
# STAFF DASHBOARD
# =========================================================

@role_required(["Staff"])
def staff_dashboard(request):

    profile = request.user.userprofile

    context = {

        "profile":
            profile,

        "patient_count":
            Patient.objects.count(),

        "appointment_count":
            Appointment.objects.count(),

        "bill_count":
            Billing.objects.count(),

        "doctor_count":
            Doctor.objects.count(),

        "recent_appointments":
            Appointment.objects
            .select_related(
                "patient",
                "doctor"
            )
            .order_by(
                "-appointment_date",
                "-appointment_time"
            )[:5],
    }

    return render(
        request,
        "staff_dashboard.html",
        context
    )


# =========================================================
# DOCTOR DASHBOARD
# =========================================================

@role_required(["Doctor"])
def doctor_dashboard(request):

    profile = request.user.userprofile

    doctor = profile.doctor_profile

    if doctor:

        doctor_appointments = (
            Appointment.objects
            .filter(
                doctor=doctor
            )
            .select_related(
                "patient",
                "doctor"
            )
            .order_by(
                "-appointment_date",
                "-appointment_time"
            )
        )

    else:

        doctor_appointments = (
            Appointment.objects.none()
        )

    context = {

        "profile":
            profile,

        "doctor":
            doctor,

        "appointment_count":
            doctor_appointments.count(),

        "pending_count":
            doctor_appointments.filter(
                status="Pending"
            ).count(),

        "completed_count":
            doctor_appointments.filter(
                status="Completed"
            ).count(),

        "cancelled_count":
            doctor_appointments.filter(
                status="Cancelled"
            ).count(),

        "appointments":
            doctor_appointments[:10],
    }

    return render(
        request,
        "doctor_dashboard.html",
        context
    )


# =========================================================
# NURSE DASHBOARD
# =========================================================

@role_required(["Nurse"])
def nurse_dashboard(request):

    profile = request.user.userprofile

    today = timezone.localdate()

    today_appointments = (
        Appointment.objects
        .filter(
            appointment_date=today
        )
        .select_related(
            "patient",
            "doctor"
        )
        .order_by(
            "appointment_time"
        )
    )

    pending_tests = (
        Laboratory.objects
        .filter(
            test_result=""
        )
        .select_related(
            "patient"
        )
        .order_by(
            "-test_date"
        )[:10]
    )

    context = {

        "profile":
            profile,

        "today":
            today,

        "patient_count":
            Patient.objects.count(),

        "today_appointments":
            today_appointments,

        "today_appointment_count":
            today_appointments.count(),

        "pending_tests":
            pending_tests,

        "doctor_count":
            Doctor.objects.count(),
    }

    return render(
        request,
        "nurse_dashboard.html",
        context
    )


# =========================================================
# PATIENT DASHBOARD
# =========================================================

@role_required(["Patient"])
def patient_dashboard(request):

    profile = request.user.userprofile

    patient = profile.patient_profile

    if patient:

        patient_appointments = (
            Appointment.objects
            .filter(
                patient=patient
            )
            .select_related(
                "patient",
                "doctor"
            )
            .order_by(
                "-appointment_date",
                "-appointment_time"
            )
        )

        patient_bills = (
            Billing.objects
            .filter(
                patient=patient
            )
            .select_related(
                "patient",
                "doctor"
            )
            .order_by("-id")
        )

        patient_tests = (
            Laboratory.objects
            .filter(
                patient=patient
            )
            .order_by(
                "-test_date",
                "-id"
            )
        )

    else:

        patient_appointments = (
            Appointment.objects.none()
        )

        patient_bills = (
            Billing.objects.none()
        )

        patient_tests = (
            Laboratory.objects.none()
        )

    total_appointments = (
        patient_appointments.count()
    )

    pending_appointments = (
        patient_appointments
        .filter(status="Pending")
        .count()
    )

    completed_appointments = (
        patient_appointments
        .filter(status="Completed")
        .count()
    )

    total_bill_amount = (
        patient_bills.aggregate(
            total=Sum("total_amount")
        )["total"] or 0
    )

    context = {

        "profile":
            profile,

        "patient":
            patient,

        "appointments":
            patient_appointments[:10],

        "appointment_count":
            total_appointments,

        "total_appointments":
            total_appointments,

        "pending_appointments":
            pending_appointments,

        "completed_appointments":
            completed_appointments,

        "bills":
            patient_bills[:10],

        "bill_count":
            patient_bills.count(),

        "total_bill_amount":
            total_bill_amount,

        "tests":
            patient_tests[:10],

        "laboratory_tests":
            patient_tests[:10],

        "test_count":
            patient_tests.count(),
    }

    return render(
        request,
        "patient_dashboard.html",
        context
    )


# =========================================================
# PATIENT BOOK APPOINTMENT
# =========================================================

@role_required(["Patient"])
def patient_book_appointment(request):

    return redirect(
        "patient_new_appointment"
    )


# =========================================================
# PATIENT NEW APPOINTMENT
# =========================================================

@role_required(["Patient"])
def patient_new_appointment(request):
    """Patient appointment booking page.

    Shows every active doctor, lets the patient choose a date/time,
    and prevents double-booking the same doctor/date/time slot.
    """
    profile = request.user.userprofile
    patient = profile.patient_profile

    if not patient:
        messages.error(
            request,
            "Patient profile is not connected with your account."
        )
        return redirect("patient_dashboard")

    doctors = (
        Doctor.objects
        .filter(is_active=True)
        .select_related("department")
        .order_by("name")
    )

    if request.method == "POST":
        form = PatientAppointmentForm(request.POST)

        if form.is_valid():
            doctor = form.cleaned_data["doctor"]
            appointment_date = form.cleaned_data["appointment_date"]
            appointment_time = form.cleaned_data["appointment_time"]
            symptoms = form.cleaned_data.get("symptoms", "").strip()

            if appointment_date < timezone.localdate():
                form.add_error(
                    "appointment_date",
                    "Appointment date cannot be in the past."
                )
            else:
                with transaction.atomic():
                    already_booked = (
                        Appointment.objects
                        .select_for_update()
                        .filter(
                            doctor=doctor,
                            appointment_date=appointment_date,
                            appointment_time=appointment_time,
                            status__in=["Pending", "Completed"],
                        )
                        .exists()
                    )

                    if already_booked:
                        form.add_error(
                            "appointment_time",
                            "This time slot is already booked. Please choose another time."
                        )
                    else:
                        try:
                            Appointment.objects.create(
                                patient=patient,
                                doctor=doctor,
                                appointment_date=appointment_date,
                                appointment_time=appointment_time,
                                symptoms=symptoms,
                                status="Pending",
                            )
                        except IntegrityError:
                            form.add_error(
                                "appointment_time",
                                "This time slot was just booked by another patient. Please choose another slot."
                            )
                        else:
                            messages.success(
                                request,
                                f"Appointment booked successfully with Dr. {doctor.name}."
                            )
                            return redirect("patient_appointments")
    else:
        form = PatientAppointmentForm()

    return render(
        request,
        "patient_new_appointment.html",
        {
            "form": form,
            "patient": patient,
            "doctors": doctors,
            "today": timezone.localdate().isoformat(),
        },
    )


# =========================================================
# DOCTOR AVAILABILITY
# =========================================================

@role_required([
    "Patient",
    "Doctor",
    "Nurse",
    "Staff"
])
def doctor_availability(request):

    doctor_id = request.GET.get(
        "doctor"
    )

    appointment_date = request.GET.get(
        "date"
    )

    if not doctor_id or not appointment_date:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Doctor and date are required."
            }
        )

    try:
        requested_date = date.fromisoformat(appointment_date)
    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid appointment date."
            },
            status=400,
        )

    if requested_date < timezone.localdate():
        return JsonResponse(
            {
                "success": False,
                "message": "Appointment date cannot be in the past."
            },
            status=400,
        )

    doctor = get_object_or_404(
        Doctor,
        id=doctor_id,
        is_active=True
    )

    appointments = (
        Appointment.objects
        .filter(
            doctor=doctor,
            appointment_date=appointment_date,
            status__in=[
                "Pending",
                "Completed"
            ]
        )
        .order_by(
            "appointment_time"
        )
    )

    booked_times = [

        appointment.appointment_time.strftime(
            "%H:%M"
        )

        for appointment in appointments
    ]

    return JsonResponse(
        {
            "success": True,
            "doctor": doctor.name,
            "date": appointment_date,
            "booked_times": booked_times,
            "booked_count": len(booked_times),
        }
    )


# Compatibility alias
check_doctor_availability = doctor_availability


# =========================================================
# PATIENT APPOINTMENTS
# =========================================================

@role_required(["Patient"])
def patient_appointments(request):

    profile = request.user.userprofile

    patient = profile.patient_profile

    if patient:

        appointments = (
            Appointment.objects
            .filter(
                patient=patient
            )
            .select_related(
                "doctor"
            )
            .order_by(
                "-appointment_date",
                "-appointment_time"
            )
        )

    else:

        appointments = (
            Appointment.objects.none()
        )

    return render(
        request,
        "patient/patient_appointments.html",
        {
            "profile":
                profile,

            "patient":
                patient,

            "appointments":
                appointments,
        }
    )


# =========================================================
# PATIENT BILLS
# =========================================================

@role_required(["Patient"])
def patient_bills(request):

    profile = request.user.userprofile

    patient = profile.patient_profile

    bills = (

        Billing.objects
        .filter(
            patient=patient
        )
        .select_related(
            "doctor"
        )
        .order_by("-id")

        if patient

        else Billing.objects.none()
    )

    return render(
        request,
        "patient_section.html",
        {
            "profile": profile,
            "patient": patient,
            "section": "My Bills",
            "section_icon": "fa-file-invoice-dollar",
            "bills": bills,
        }
    )


# =========================================================
# PATIENT LABORATORY
# =========================================================

@role_required(["Patient"])
def patient_laboratory(request):

    profile = request.user.userprofile

    patient = profile.patient_profile

    tests = (

        Laboratory.objects
        .filter(
            patient=patient
        )
        .order_by(
            "-test_date",
            "-id"
        )

        if patient

        else Laboratory.objects.none()
    )

    return render(
        request,
        "patient_section.html",
        {
            "profile": profile,
            "patient": patient,
            "section": "Laboratory Reports",
            "section_icon": "fa-flask",
            "tests": tests,
        }
    )


# =========================================================
# PATIENT PHARMACY
# =========================================================

@role_required(["Patient"])
def patient_pharmacy(request):

    profile = request.user.userprofile

    patient = profile.patient_profile

    issues = (

        MedicineIssue.objects
        .filter(
            patient=patient
        )
        .select_related(
            "medicine",
            "issued_by"
        )
        .order_by("-id")

        if patient

        else MedicineIssue.objects.none()
    )

    return render(
        request,
        "patient_section.html",
        {
            "profile": profile,
            "patient": patient,
            "section": "Pharmacy",
            "section_icon": "fa-pills",
            "issues": issues,
        }
    )


# =========================================================
# PATIENT PROFILE
# =========================================================

@role_required(["Patient"])
def patient_profile(request):

    profile = request.user.userprofile

    patient = profile.patient_profile

    if patient is None:

        messages.error(
            request,
            "Patient profile is not linked to your account."
        )

        return redirect(
            "patient_dashboard"
        )

    if request.method == "POST":

        form = PatientProfileForm(
            request.POST,
            instance=patient
        )

        if form.is_valid():

            updated_patient = form.save()

            user = request.user

            name_parts = (
                updated_patient.name
                .strip()
                .split(" ", 1)
            )

            user.first_name = name_parts[0]

            if len(name_parts) > 1:
                user.last_name = name_parts[1]
            else:
                user.last_name = ""

            user.email = updated_patient.email

            user.save(
                update_fields=[
                    "first_name",
                    "last_name",
                    "email"
                ]
            )

            profile.phone = updated_patient.phone
            profile.email = updated_patient.email
            profile.aadhaar_number = (
                updated_patient.aadhaar_number
            )
            profile.address = updated_patient.address
            profile.date_of_birth = (
                updated_patient.date_of_birth
            )
            profile.gender = updated_patient.gender

            profile.save()

            messages.success(
                request,
                "Profile updated successfully."
            )

            return redirect(
                "patient_profile"
            )

    else:

        form = PatientProfileForm(
            instance=patient
        )

    return render(
        request,
        "patient_profile_edit.html",
        {
            "form": form,
            "patient": patient,
        }
    )


# =========================================================
# ADMIN - APPOINTMENTS
# =========================================================

@role_or_admin_required(['Staff', 'Doctor', 'Nurse'])
def appointments(request):

    search = request.GET.get(
        "search",
        ""
    ).strip()

    appointment_list = (
        Appointment.objects
        .select_related(
            "patient",
            "doctor"
        )
        .order_by(
            "-appointment_date",
            "-appointment_time"
        )
    )

    if search:

        appointment_list = (
            appointment_list.filter(
                Q(
                    patient__name__icontains=search
                )
                |
                Q(
                    doctor__name__icontains=search
                )
                |
                Q(
                    status__icontains=search
                )
            )
        )

    return render(
        request,
        "appointments.html",
        {
            "appointments":
                appointment_list,

            "search":
                search,
        }
    )


@role_or_admin_required(['Staff', 'Doctor', 'Nurse'])
def add_appointment(request):

    if request.method == "POST":

        form = AppointmentForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Appointment added successfully."
            )

            return redirect(
                "appointments"
            )

    else:

        form = AppointmentForm()

    return render(
        request,
        "add_appointment.html",
        {
            "form": form
        }
    )


@role_or_admin_required(['Staff', 'Doctor', 'Nurse'])
def edit_appointment(request, id):

    appointment = get_object_or_404(
        Appointment,
        id=id
    )

    if request.method == "POST":

        form = AppointmentForm(
            request.POST,
            instance=appointment
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Appointment updated successfully."
            )

            return redirect(
                "appointments"
            )

    else:

        form = AppointmentForm(
            instance=appointment
        )

    return render(
        request,
        "edit_appointment.html",
        {
            "form": form,
            "appointment": appointment
        }
    )


@role_or_admin_required(['Staff', 'Doctor', 'Nurse'])
def delete_appointment(request, id):

    appointment = get_object_or_404(
        Appointment,
        id=id
    )

    if request.method == "POST":

        appointment.delete()

        messages.success(
            request,
            "Appointment deleted successfully."
        )

        return redirect(
            "appointments"
        )

    return render(
        request,
        "delete_appointment.html",
        {
            "appointment": appointment
        }
    )


# =========================================================
# ADMIN - DOCTORS
# =========================================================

@role_or_admin_required(['Staff'])
def doctors(request):

    doctor_list = Doctor.objects.all()

    return render(
        request,
        "doctors.html",
        {
            "doctors":
                doctor_list
        }
    )


@role_or_admin_required(['Staff'])
def add_doctor(request):

    if request.method == "POST":

        form = DoctorForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Doctor added successfully."
            )

            return redirect(
                "doctors"
            )

    else:

        form = DoctorForm()

    return render(
        request,
        "add_doctor.html",
        {
            "form":
                form
        }
    )


@role_or_admin_required(['Staff'])
def edit_doctor(request, id):

    doctor = get_object_or_404(
        Doctor,
        id=id
    )

    if request.method == "POST":

        form = DoctorForm(
            request.POST,
            request.FILES,
            instance=doctor
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Doctor updated successfully."
            )

            return redirect(
                "doctors"
            )

    else:

        form = DoctorForm(
            instance=doctor
        )

    return render(
        request,
        "edit_doctor.html",
        {
            "form": form,
            "doctor": doctor
        }
    )


@role_or_admin_required(['Staff'])
def delete_doctor(request, id):

    doctor = get_object_or_404(
        Doctor,
        id=id
    )

    if request.method == "POST":

        doctor.delete()

        messages.success(
            request,
            "Doctor deleted successfully."
        )

        return redirect(
            "doctors"
        )

    return render(
        request,
        "delete_doctor.html",
        {
            "doctor": doctor
        }
    )


# =========================================================
# ADMIN - PATIENTS
# =========================================================

@role_or_admin_required(['Staff', 'Doctor', 'Nurse'])
def patients(request):

    patient_list = Patient.objects.all()

    return render(
        request,
        "patients.html",
        {
            "patients":
                patient_list
        }
    )


@role_or_admin_required(['Staff', 'Nurse'])
def add_patient(request):

    if request.method == "POST":

        form = PatientForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Patient added successfully."
            )

            return redirect(
                "patients"
            )

    else:

        form = PatientForm()

    return render(
        request,
        "add_patient.html",
        {
            "form":
                form
        }
    )


@role_or_admin_required(['Staff', 'Doctor', 'Nurse'])
def edit_patient(request, id):

    patient = get_object_or_404(
        Patient,
        id=id
    )

    if request.method == "POST":

        form = PatientForm(
            request.POST,
            request.FILES,
            instance=patient
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Patient updated successfully."
            )

            return redirect(
                "patients"
            )

    else:

        form = PatientForm(
            instance=patient
        )

    return render(
        request,
        "edit_patient.html",
        {
            "form": form,
            "patient": patient
        }
    )


@role_or_admin_required(['Staff'])
def delete_patient(request, id):

    patient = get_object_or_404(
        Patient,
        id=id
    )

    if request.method == "POST":

        patient.delete()

        messages.success(
            request,
            "Patient deleted successfully."
        )

        return redirect(
            "patients"
        )

    return render(
        request,
        "delete_patient.html",
        {
            "patient":
                patient
        }
    )


# =========================================================
# ADMIN - BILLING
# =========================================================

@role_or_admin_required(['Staff', 'Doctor'])
def billing_list(request):

    bill_list = (
        Billing.objects
        .select_related(
            "patient",
            "doctor"
        )
        .order_by("-id")
    )

    return render(
        request,
        "billing_list.html",
        {
            "bills":
                bill_list
        }
    )


@role_or_admin_required(['Staff', 'Doctor'])
def add_bill(request):

    if request.method == "POST":

        form = BillingForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Bill created successfully."
            )

            return redirect(
                "billing_list"
            )

    else:

        form = BillingForm()

    return render(
        request,
        "add_bill.html",
        {
            "form":
                form
        }
    )


@role_or_admin_required(['Staff', 'Doctor'])
def edit_bill(request, id):

    bill = get_object_or_404(
        Billing,
        id=id
    )

    if request.method == "POST":

        form = BillingForm(
            request.POST,
            instance=bill
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Bill updated successfully."
            )

            return redirect(
                "billing_list"
            )

    else:

        form = BillingForm(
            instance=bill
        )

    return render(
        request,
        "edit_bill.html",
        {
            "form": form,
            "bill": bill
        }
    )


@role_or_admin_required(['Staff'])
def delete_bill(request, id):

    bill = get_object_or_404(
        Billing,
        id=id
    )

    if request.method == "POST":

        bill.delete()

        messages.success(
            request,
            "Bill deleted successfully."
        )

        return redirect(
            "billing_list"
        )

    return render(
        request,
        "delete_bill.html",
        {
            "bill":
                bill
        }
    )


@role_or_admin_required(['Staff', 'Doctor'])
def print_bill(request, id):

    bill = get_object_or_404(
        Billing,
        id=id
    )

    return render(
        request,
        "print_bill.html",
        {
            "bill":
                bill
        }
    )


# =========================================================
# ADMIN - PHARMACY
# =========================================================

@role_or_admin_required(['Staff', 'Nurse'])
def medicines(request):

    search = request.GET.get(
        "search",
        ""
    ).strip()

    medicine_list = (
        Medicine.objects
        .all()
        .order_by(
            "medicine_name"
        )
    )

    if search:

        medicine_list = (
            medicine_list.filter(
                Q(
                    medicine_name__icontains=search
                )
                |
                Q(
                    company_name__icontains=search
                )
                |
                Q(
                    status__icontains=search
                )
            )
        )

    today = date.today()

    context = {

        "medicines":
            medicine_list,

        "search":
            search,

        "today":
            today,

        "expiry_limit":
            today + timedelta(days=30),

        "total_medicine":
            Medicine.objects.count(),

        "available_count":
            Medicine.objects.filter(
                status="Available"
            ).count(),

        "out_stock_count":
            Medicine.objects.filter(
                status="Out of Stock"
            ).count(),

        "expired_count":
            Medicine.objects.filter(
                status="Expired"
            ).count(),

        "low_stock_count":
            Medicine.objects.filter(
                stock__lte=10
            ).count(),
    }

    return render(
        request,
        "medicines.html",
        context
    )


@role_or_admin_required(['Staff'])
def add_medicine(request):

    if request.method == "POST":

        form = MedicineForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Medicine added successfully."
            )

            return redirect(
                "medicines"
            )

    else:

        form = MedicineForm()

    return render(
        request,
        "add_medicine.html",
        {
            "form":
                form
        }
    )


@role_or_admin_required(['Staff'])
def edit_medicine(request, id):

    medicine = get_object_or_404(
        Medicine,
        id=id
    )

    if request.method == "POST":

        form = MedicineForm(
            request.POST,
            instance=medicine
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Medicine updated successfully."
            )

            return redirect(
                "medicines"
            )

    else:

        form = MedicineForm(
            instance=medicine
        )

    return render(
        request,
        "edit_medicine.html",
        {
            "form": form,
            "medicine": medicine
        }
    )


@role_or_admin_required(['Staff'])
def delete_medicine(request, id):

    medicine = get_object_or_404(
        Medicine,
        id=id
    )

    if request.method == "POST":

        medicine.delete()

        messages.success(
            request,
            "Medicine deleted successfully."
        )

        return redirect(
            "medicines"
        )

    return render(
        request,
        "delete_medicine.html",
        {
            "medicine":
                medicine
        }
    )


@role_or_admin_required(['Staff', 'Nurse'])
def issue_medicine(request):

    if request.method == "POST":

        form = MedicineIssueForm(
            request.POST
        )

        if form.is_valid():

            medicine_issue = form.save(
                commit=False
            )

            medicine_issue.issued_by = (
                request.user
            )

            medicine_issue.save()

            messages.success(
                request,
                "Medicine issued successfully."
            )

            return redirect(
                "medicine_issue_list"
            )

    else:

        form = MedicineIssueForm()

    return render(
        request,
        "issue_medicine.html",
        {
            "form":
                form
        }
    )


@role_or_admin_required(['Staff', 'Nurse'])
def medicine_issue_list(request):

    search = request.GET.get(
        "search",
        ""
    ).strip()

    issues = (
        MedicineIssue.objects
        .select_related(
            "patient",
            "medicine",
            "issued_by"
        )
        .order_by("-id")
    )

    if search:

        issues = issues.filter(
            Q(
                patient__name__icontains=search
            )
            |
            Q(
                medicine__medicine_name__icontains=search
            )
        )

    return render(
        request,
        "medicine_issue_list.html",
        {
            "issues":
                issues,

            "search":
                search
        }
    )


@role_or_admin_required(['Staff', 'Nurse'])
def print_medicine_issue(request, id):

    issue = get_object_or_404(
        MedicineIssue,
        id=id
    )

    return render(
        request,
        "print_medicine_issue.html",
        {
            "issue":
                issue
        }
    )


# =========================================================
# ADMIN - LABORATORY
# =========================================================

@role_or_admin_required(['Staff', 'Doctor', 'Nurse'])
def laboratory(request):

    search = request.GET.get(
        "search",
        ""
    ).strip()

    tests = (
        Laboratory.objects
        .select_related(
            "patient"
        )
        .order_by(
            "-test_date",
            "-id"
        )
    )

    if search:

        tests = tests.filter(
            Q(
                patient__name__icontains=search
            )
            |
            Q(
                test_name__icontains=search
            )
            |
            Q(
                test_result__icontains=search
            )
        )

    today = timezone.localdate()

    context = {

        "tests":
            tests,

        "search":
            search,

        "total_tests":
            Laboratory.objects.count(),

        "today_tests":
            Laboratory.objects.filter(
                test_date=today
            ).count(),

        "total_lab_income":
            Laboratory.objects.aggregate(
                total=Sum("test_charge")
            )["total"] or 0,
    }

    return render(
        request,
        "laboratory.html",
        context
    )


@role_or_admin_required(['Staff', 'Doctor', 'Nurse'])
def add_test(request):

    if request.method == "POST":

        form = LaboratoryForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Laboratory test added successfully."
            )

            return redirect(
                "laboratory"
            )

    else:

        form = LaboratoryForm()

    return render(
        request,
        "add_test.html",
        {
            "form":
                form
        }
    )


@role_or_admin_required(['Staff', 'Doctor', 'Nurse'])
def edit_test(request, id):

    test = get_object_or_404(
        Laboratory,
        id=id
    )

    if request.method == "POST":

        form = LaboratoryForm(
            request.POST,
            instance=test
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Laboratory test updated successfully."
            )

            return redirect(
                "laboratory"
            )

    else:

        form = LaboratoryForm(
            instance=test
        )

    return render(
        request,
        "edit_test.html",
        {
            "form": form,
            "test": test
        }
    )


@role_or_admin_required(['Staff'])
def delete_test(request, id):

    test = get_object_or_404(
        Laboratory,
        id=id
    )

    if request.method == "POST":

        test.delete()

        messages.success(
            request,
            "Laboratory test deleted successfully."
        )

        return redirect(
            "laboratory"
        )

    return render(
        request,
        "delete_test.html",
        {
            "test":
                test
        }
    )


@role_or_admin_required(['Staff', 'Doctor', 'Nurse'])
def print_test_report(request, id):

    test = get_object_or_404(
        Laboratory,
        id=id
    )

    return render(
        request,
        "print_test_report.html",
        {
            "test":
                test
        }
    )


# =========================================================
# ADMIN - REPORTS
# =========================================================

@role_or_admin_required(['Staff', 'Doctor'])
def reports(request):

    start_date = request.GET.get(
        "start_date",
        ""
    )

    end_date = request.GET.get(
        "end_date",
        ""
    )

    appointments_data = (
        Appointment.objects
        .select_related(
            "patient",
            "doctor"
        )
    )

    bills_data = (
        Billing.objects
        .select_related(
            "patient",
            "doctor"
        )
    )

    laboratory_data = (
        Laboratory.objects
        .select_related(
            "patient"
        )
    )

    if start_date:

        appointments_data = (
            appointments_data.filter(
                appointment_date__gte=start_date
            )
        )

        bills_data = (
            bills_data.filter(
                bill_date__gte=start_date
            )
        )

        laboratory_data = (
            laboratory_data.filter(
                test_date__gte=start_date
            )
        )

    if end_date:

        appointments_data = (
            appointments_data.filter(
                appointment_date__lte=end_date
            )
        )

        bills_data = (
            bills_data.filter(
                bill_date__lte=end_date
            )
        )

        laboratory_data = (
            laboratory_data.filter(
                test_date__lte=end_date
            )
        )

    total_income = (
        bills_data.aggregate(
            total=Sum("total_amount")
        )["total"] or 0
    )

    laboratory_income = (
        laboratory_data.aggregate(
            total=Sum("test_charge")
        )["total"] or 0
    )

    context = {

        "start_date":
            start_date,

        "end_date":
            end_date,

        "doctor_count":
            Doctor.objects.count(),

        "patient_count":
            Patient.objects.count(),

        "appointment_count":
            appointments_data.count(),

        "pending_appointments":
            appointments_data.filter(
                status="Pending"
            ).count(),

        "completed_appointments":
            appointments_data.filter(
                status="Completed"
            ).count(),

        "cancelled_appointments":
            appointments_data.filter(
                status="Cancelled"
            ).count(),

        "bill_count":
            bills_data.count(),

        "total_income":
            total_income,

        "medicine_count":
            Medicine.objects.count(),

        "available_medicines":
            Medicine.objects.filter(
                status="Available"
            ).count(),

        "out_of_stock_medicines":
            Medicine.objects.filter(
                status="Out of Stock"
            ).count(),

        "low_stock_medicines":
            Medicine.objects.filter(
                stock__lte=10
            ).count(),

        "laboratory_count":
            laboratory_data.count(),

        "laboratory_income":
            laboratory_income,

        "recent_appointments":
            appointments_data.order_by(
                "-appointment_date",
                "-appointment_time"
            )[:10],

        "recent_bills":
            bills_data.order_by(
                "-bill_date",
                "-id"
            )[:10],
    }

    return render(
        request,
        "reports.html",
        context
    )


# =========================================================
# ADMIN PANEL
# =========================================================

@admin_required
def admin_panel(request):

    total_income = (
        Billing.objects.aggregate(
            total=Sum("total_amount")
        )["total"] or 0
    )

    context = {

        "doctor_count":
            Doctor.objects.count(),

        "patient_count":
            Patient.objects.count(),

        "appointment_count":
            Appointment.objects.count(),

        "bill_count":
            Billing.objects.count(),

        "medicine_count":
            Medicine.objects.count(),

        "laboratory_count":
            Laboratory.objects.count(),

        "total_income":
            total_income,

        "recent_appointments":
            Appointment.objects
            .select_related(
                "patient",
                "doctor"
            )
            .order_by(
                "-appointment_date",
                "-appointment_time"
            )[:10],
    }

    return render(
        request,
        "admin_panel.html",
        context
    )


# =========================================================
# ACCOUNT APPROVAL
# =========================================================

@admin_required
def account_approval_list(request):

    pending_accounts = (
        UserProfile.objects
        .select_related(
            "user"
        )
        .filter(
            role__in=[
                "Doctor",
                "Nurse",
                "Staff"
            ],
            is_approved=False,
            user__is_active=True
        )
        .order_by(
            "-created_at"
        )
    )

    approved_accounts = (
        UserProfile.objects
        .select_related(
            "user"
        )
        .filter(
            role__in=[
                "Doctor",
                "Nurse",
                "Staff"
            ],
            is_approved=True
        )
        .order_by(
            "-updated_at"
        )
    )

    context = {

        "pending_accounts":
            pending_accounts,

        "approved_accounts":
            approved_accounts,
    }

    return render(
        request,
        "account_approval_list.html",
        context
    )


# =========================================================
# APPROVE ACCOUNT
# =========================================================

@admin_required
def approve_account(request, id):

    profile = get_object_or_404(
        UserProfile,
        id=id
    )

    if request.method == "POST":

        profile.is_approved = True

        profile.user.is_active = True

        profile.user.save(
            update_fields=[
                "is_active"
            ]
        )

        profile.save(
            update_fields=[
                "is_approved",
                "updated_at"
            ]
        )

        messages.success(
            request,
            (
                f"{profile.user.username} "
                "account approved successfully."
            )
        )

    return redirect(
        "account_approval_list"
    )


# =========================================================
# REJECT ACCOUNT
# =========================================================

@admin_required
def reject_account(request, id):

    profile = get_object_or_404(
        UserProfile,
        id=id
    )

    if request.method == "POST":

        profile.is_approved = False

        profile.user.is_active = False

        profile.user.save(
            update_fields=[
                "is_active"
            ]
        )

        profile.save(
            update_fields=[
                "is_approved",
                "updated_at"
            ]
        )

        messages.warning(
            request,
            (
                f"{profile.user.username} "
                "account rejected."
            )
        )

    return redirect(
        "account_approval_list"
    )
