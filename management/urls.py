from django.urls import path
from . import views


urlpatterns = [

    # =====================================================
    # PUBLIC WEBSITE
    # =====================================================

    path(
        '',
        views.user_home,
        name='user_home'
    ),


    # =====================================================
    # AUTHENTICATION
    # =====================================================

    path(
        'login/',
        views.login_view,
        name='login'
    ),

    path(
        'register/',
        views.register_view,
        name='register'
    ),

    path(
        'register/patient/',
        views.patient_register,
        name='patient_register'
    ),

    path(
        'register/doctor/',
        views.doctor_register,
        name='doctor_register'
    ),

    path(
        'register/nurse/',
        views.nurse_register,
        name='nurse_register'
    ),

    path(
        'register/staff/',
        views.staff_register,
        name='staff_register'
    ),

    path(
        'forgot-password/',
        views.forgot_password,
        name='forgot_password'
    ),

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),


    # =====================================================
    # MAIN DASHBOARD
    # =====================================================

    path(
        'dashboard/',
        views.home,
        name='dashboard'
    ),


    # =====================================================
    # ROLE DASHBOARDS
    # =====================================================

    path(
        'staff-dashboard/',
        views.staff_dashboard,
        name='staff_dashboard'
    ),

    path(
        'doctor-dashboard/',
        views.doctor_dashboard,
        name='doctor_dashboard'
    ),

    path(
        'nurse-dashboard/',
        views.nurse_dashboard,
        name='nurse_dashboard'
    ),

    path(
        'patient-dashboard/',
        views.patient_dashboard,
        name='patient_dashboard'
    ),


    # =====================================================
    # PATIENT MODULE
    # =====================================================

    path(
        'patient/appointments/',
        views.patient_appointments,
        name='patient_appointments'
    ),

    path(
        'patient/appointment/',
        views.patient_new_appointment,
        name='patient_new_appointment'
    ),

    path(
        'patient/book-appointment/',
        views.patient_book_appointment,
        name='patient_book_appointment'
    ),

    path(
        'patient/check-doctor-availability/',
        views.doctor_availability,
        name='check_doctor_availability'
    ),

    path(
        'patient/bills/',
        views.patient_bills,
        name='patient_bills'
    ),

    path(
        'patient/laboratory/',
        views.patient_laboratory,
        name='patient_laboratory'
    ),

    path(
        'patient/pharmacy/',
        views.patient_pharmacy,
        name='patient_pharmacy'
    ),

    path(
        'patient/profile/',
        views.patient_profile,
        name='patient_profile'
    ),


    # =====================================================
    # DOCTOR MODULE
    # =====================================================

    path(
        'doctors/',
        views.doctors,
        name='doctors'
    ),

    path(
        'doctors/add/',
        views.add_doctor,
        name='add_doctor'
    ),

    path(
        'doctors/edit/<int:id>/',
        views.edit_doctor,
        name='edit_doctor'
    ),

    path(
        'doctors/delete/<int:id>/',
        views.delete_doctor,
        name='delete_doctor'
    ),


    # =====================================================
    # PATIENT ADMIN MODULE
    # =====================================================

    path(
        'patients/',
        views.patients,
        name='patients'
    ),

    path(
        'patients/add/',
        views.add_patient,
        name='add_patient'
    ),

    path(
        'patients/edit/<int:id>/',
        views.edit_patient,
        name='edit_patient'
    ),

    path(
        'patients/delete/<int:id>/',
        views.delete_patient,
        name='delete_patient'
    ),


    # =====================================================
    # ADMIN APPOINTMENT MODULE
    # =====================================================

    path(
        'appointments/',
        views.appointments,
        name='appointments'
    ),

    path(
        'appointments/add/',
        views.add_appointment,
        name='add_appointment'
    ),

    path(
        'appointments/edit/<int:id>/',
        views.edit_appointment,
        name='edit_appointment'
    ),

    path(
        'appointments/delete/<int:id>/',
        views.delete_appointment,
        name='delete_appointment'
    ),


    # =====================================================
    # BILLING
    # =====================================================

    path(
        'billing/',
        views.billing_list,
        name='billing_list'
    ),

    path(
        'billing/add/',
        views.add_bill,
        name='add_bill'
    ),

    path(
        'billing/edit/<int:id>/',
        views.edit_bill,
        name='edit_bill'
    ),

    path(
        'billing/delete/<int:id>/',
        views.delete_bill,
        name='delete_bill'
    ),

    path(
        'billing/print/<int:id>/',
        views.print_bill,
        name='print_bill'
    ),


    # =====================================================
    # PHARMACY
    # =====================================================

    path(
        'pharmacy/',
        views.medicines,
        name='medicines'
    ),

    path(
        'pharmacy/add/',
        views.add_medicine,
        name='add_medicine'
    ),

    path(
        'pharmacy/edit/<int:id>/',
        views.edit_medicine,
        name='edit_medicine'
    ),

    path(
        'pharmacy/delete/<int:id>/',
        views.delete_medicine,
        name='delete_medicine'
    ),

    path(
        'pharmacy/issue/',
        views.issue_medicine,
        name='issue_medicine'
    ),

    path(
        'pharmacy/issue-history/',
        views.medicine_issue_list,
        name='medicine_issue_list'
    ),

    path(
        'pharmacy/issue/print/<int:id>/',
        views.print_medicine_issue,
        name='print_medicine_issue'
    ),


    # =====================================================
    # LABORATORY
    # =====================================================

    path(
        'laboratory/',
        views.laboratory,
        name='laboratory'
    ),

    path(
        'laboratory/add/',
        views.add_test,
        name='add_test'
    ),

    path(
        'laboratory/edit/<int:id>/',
        views.edit_test,
        name='edit_test'
    ),

    path(
        'laboratory/delete/<int:id>/',
        views.delete_test,
        name='delete_test'
    ),

    path(
        'laboratory/print/<int:id>/',
        views.print_test_report,
        name='print_test_report'
    ),


    # =====================================================
    # REPORTS
    # =====================================================

    path(
        'reports/',
        views.reports,
        name='reports'
    ),


    # =====================================================
    # ACCOUNT APPROVAL
    # =====================================================

    path(
        'account-approvals/',
        views.account_approval_list,
        name='account_approval_list'
    ),

    path(
        'account-approvals/approve/<int:id>/',
        views.approve_account,
        name='approve_account'
    ),

    path(
        'account-approvals/reject/<int:id>/',
        views.reject_account,
        name='reject_account'
    ),


    # =====================================================
    # CUSTOM ADMIN PANEL
    # =====================================================

    path(
        'admin-panel/',
        views.admin_panel,
        name='admin_panel'
    ),

]