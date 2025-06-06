from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from servicio_facturacion.views import FacturaViewSet

router = DefaultRouter()
router.register(r'facturas', FacturaViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]