from django.urls import path

from .views import (
    HomeView,
    LandingView,
    MissingProductsView,
    PlanificacionNormalizeView,
    PlanningUploadView,
    SalidaNormalizeView,
    SalidaUploadView,
    TableroNormalizadoView,
    PvpIssuesView,
    UploadMenuView,
    PlanificacionErrorResolverView,
    SalidaErrorResolverView,
)

urlpatterns = [
    path("", LandingView.as_view(), name="home"),
    path("subidas/", UploadMenuView.as_view(), name="upload_menu"),
    path("subidas/excel/", HomeView.as_view(), name="upload_excel"),
    path("planificacion/", PlanningUploadView.as_view(), name="planning_upload"),
    path("planificacion/normalizar/", PlanificacionNormalizeView.as_view(), name="planning_normalize"),
    path("planificacion/errores/", PlanificacionErrorResolverView.as_view(), name="planificacion_error_resolver"),
    path("salidas/", SalidaUploadView.as_view(), name="salida_upload"),
    path("salidas/normalizar/", SalidaNormalizeView.as_view(), name="salida_normalize"),
    path("salidas/errores/", SalidaErrorResolverView.as_view(), name="salida_error_resolver"),
    path("tablero/normalizado/", TableroNormalizadoView.as_view(), name="tablero_normalizado"),
    path("faltantes/", MissingProductsView.as_view(), name="missing_products"),
    path("pvp/faltantes/", PvpIssuesView.as_view(), name="pvp_issues"),
]
