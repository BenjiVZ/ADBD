"""
Vista para limpiar todas las tablas de Planificación y Salida
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.views import View

from ..models import (
    Planificacion, PlanificacionNormalizada, PlanningBatch, PlanningEntry,
    Salida, SalidaNormalizada
)


class LimpiarTodoView(View):
    """Vista para limpiar todas las tablas"""
    
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        
        if action == 'limpiar_planificacion':
            return self._limpiar_planificacion(request)
        elif action == 'limpiar_salida':
            return self._limpiar_salida(request)
        elif action == 'limpiar_todo':
            return self._limpiar_todo(request)
        
        return redirect('main:home')
    
    def _limpiar_planificacion(self, request):
        """Limpiar todas las tablas de planificación"""
        # Eliminar en orden correcto (primero los que tienen FK)
        count_norm = PlanificacionNormalizada.objects.all().delete()[0]
        count_plan = Planificacion.objects.all().delete()[0]
        count_entry = PlanningEntry.objects.all().delete()[0]
        count_batch = PlanningBatch.objects.all().delete()[0]
        
        total = count_norm + count_plan + count_entry + count_batch
        
        messages.success(
            request,
            f"✅ Planificación limpiada: {count_norm} normalizadas, {count_plan} crudas, "
            f"{count_entry} entries, {count_batch} batches eliminados. Total: {total}"
        )
        
        return redirect('main:home')
    
    def _limpiar_salida(self, request):
        """Limpiar todas las tablas de salida"""
        # Eliminar en orden correcto (primero los que tienen FK)
        count_norm = SalidaNormalizada.objects.all().delete()[0]
        count_sal = Salida.objects.all().delete()[0]
        
        total = count_norm + count_sal
        
        messages.success(
            request,
            f"✅ Salidas limpiadas: {count_norm} normalizadas, {count_sal} crudas eliminadas. Total: {total}"
        )
        
        return redirect('main:home')
    
    def _limpiar_todo(self, request):
        """Limpiar TODAS las tablas de planificación y salida"""
        # Planificación
        count_plan_norm = PlanificacionNormalizada.objects.all().delete()[0]
        count_plan = Planificacion.objects.all().delete()[0]
        count_entry = PlanningEntry.objects.all().delete()[0]
        count_batch = PlanningBatch.objects.all().delete()[0]
        
        # Salida
        count_sal_norm = SalidaNormalizada.objects.all().delete()[0]
        count_sal = Salida.objects.all().delete()[0]
        
        total = count_plan_norm + count_plan + count_entry + count_batch + count_sal_norm + count_sal
        
        messages.success(
            request,
            f"✅ TODO limpiado: Planificación ({count_plan_norm} norm + {count_plan} crudas + {count_entry} entries + {count_batch} batches), "
            f"Salidas ({count_sal_norm} norm + {count_sal} crudas). Total: {total} registros eliminados."
        )
        
        return redirect('main:home')
