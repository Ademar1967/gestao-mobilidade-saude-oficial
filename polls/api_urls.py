from rest_framework import routers
from .api_views import (
    PacienteViewSet,
    ClinicaViewSet,
    CondutorViewSet,
    EnfermagemViewSet,
    VeiculoViewSet,
)

router = routers.DefaultRouter()
router.register(r"pacientes", PacienteViewSet)
router.register(r"clinicas", ClinicaViewSet)
router.register(r"condutores", CondutorViewSet)
router.register(r"enfermagens", EnfermagemViewSet)
router.register(r"veiculos", VeiculoViewSet)

urlpatterns = router.urls
