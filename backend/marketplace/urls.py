"""
URL configuration for marketplace project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from utils.router.api import BaseAPI
from payment.api import payos_webhook, payos_return
from profile.api_chef_payment import router as chef_payment_router


api = BaseAPI()
api.auto_discover_controllers()
#api.add_router("/chef", chef_payment_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/chat/', include('chat.urls')),
    path('api/mongo-chat/', include('mongo_chat.urls')),
    path("api/", api.urls),
    # PayOS callback endpoints
    path("api/payment/payos/webhook", payos_webhook, name="payos_webhook"),
    path("api/payment/payos/return", payos_return, name="payos_return"),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # type: ignore
