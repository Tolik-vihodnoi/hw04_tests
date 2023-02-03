from django.contrib.auth.views import (
    LogoutView, PasswordChangeDoneView, PasswordResetConfirmView,
    PasswordResetDoneView, PasswordResetView
)
from django.urls import path

from .views import Login, PasswordChange, SignUp

app_name = 'users'

urlpatterns = [
    path('logout/',
         LogoutView.as_view(template_name='users/logged_out.html'),
         name='logout'),
    path('signup/',
         SignUp.as_view(),
         name='signup'),
    path('login/',
         Login.as_view(),
         name='login'),
    path('password_change/',
         PasswordChange.as_view(),
         name='password_change'),
    path('password_change/done/',
         PasswordChangeDoneView.as_view(
             template_name='users/password_change_done.html'),
         name='password_change_done'),
    path('password_reset/',
         PasswordResetView.as_view(
             template_name='users/password_reset_form.html'),
         name='password_reset_form'),
    path('password_reset/done/',
         PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uuid:uidb64>/<uuid:token>/',
         PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm'),
         name='password_reset_confirm')
]
