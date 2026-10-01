"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from users.views import csrf, current_user, session_login, session_logout
from reservation.views import buy_sneaker
from waitlist.views import join_sneaker_waitlist
from payment.views import complete_payment
from inventory.views import sneaker_status
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/csrf/', csrf, name='csrf'),
    path('api/auth/login/', session_login, name='session-login'),
    path('api/auth/me/', current_user, name='current-user'),
    path('api/auth/logout/', session_logout, name='session-logout'),
    path('api/reservations/buy/', buy_sneaker, name='buy-sneaker'),
    path('api/waitlist/join/', join_sneaker_waitlist, name='join-waitlist'),
    path("api/payments/complete/",complete_payment,name="complete-payment"),
    path("api/inventory/", sneaker_status, name="sneaker-status"),
]
