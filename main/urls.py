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
    AdminCedisView,
    AdminSucursalesView,
    BibliotecaCedisView,
    BibliotecaSucursalesView,
    CorreccionCedisView,
    CorreccionSucursalesView,
    NormalizarTodoView,
    LimpiarTodoView,
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
    # Admin maestros (legacy)
    path("admin/cedis/", AdminCedisView.as_view(), name="admin_cedis"),
    path("admin/sucursales/", AdminSucursalesView.as_view(), name="admin_sucursales"),
    # Biblioteca - Investigación desde datos crudos
    path("biblioteca/cedis/", BibliotecaCedisView.as_view(), name="biblioteca_cedis"),
    path("biblioteca/sucursales/", BibliotecaSucursalesView.as_view(), name="biblioteca_sucursales"),
    # Corrección de datos crudos
    path("correccion/cedis/", CorreccionCedisView.as_view(), name="correccion_cedis"),
    path("correccion/sucursales/", CorreccionSucursalesView.as_view(), name="correccion_sucursales"),
    # Normalizar todo de un golpe
    path("normalizar/", NormalizarTodoView.as_view(), name="normalizar_todo"),
    # Limpiar datos
    path("limpiar/", LimpiarTodoView.as_view(), name="limpiar_todo"),
]

