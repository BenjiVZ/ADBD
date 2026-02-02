"""
URL configuration for ADB project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import include, path

from main.admin import salidas_admin, planificaciones_admin

urlpatterns = [
    # Admin sites personalizados (deben ir ANTES del admin principal)
    path('salidas-admin/', salidas_admin.urls),
    path('planificaciones-admin/', planificaciones_admin.urls),
    # Admin principal
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
]
