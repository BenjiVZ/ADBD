from django.db import transaction
from django.shortcuts import redirect, render
from django.views import View

from ..models import Cendis, Sucursal


class AdminCedisView(View):
    template_name = "admin_cedis.html"

    def get(self, request, *args, **kwargs):
        cedis_list = Cendis.objects.all().order_by('origin')
        return render(request, self.template_name, {
            "cedis_list": cedis_list,
        })

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        
        if action == "delete":
            cedis_id = request.POST.get("cedis_id")
            try:
                Cendis.objects.filter(id=cedis_id).delete()
            except Exception as e:
                return render(request, self.template_name, {
                    "cedis_list": Cendis.objects.all().order_by('origin'),
                    "error": f"Error al eliminar: {str(e)}",
                })
        
        elif action == "edit":
            cedis_id = request.POST.get("cedis_id")
            new_origin = request.POST.get("new_origin")
            new_code = request.POST.get("new_code")
            try:
                cedis = Cendis.objects.get(id=cedis_id)
                if new_origin:
                    cedis.origin = new_origin.strip()
                if new_code:
                    cedis.code = new_code.strip()
                cedis.save()
            except Exception as e:
                return render(request, self.template_name, {
                    "cedis_list": Cendis.objects.all().order_by('origin'),
                    "error": f"Error al editar: {str(e)}",
                })
        
        elif action == "create":
            new_origin = request.POST.get("new_origin")
            new_code = request.POST.get("new_code")
            if new_origin and new_code:
                try:
                    Cendis.objects.create(
                        origin=new_origin.strip(),
                        code=new_code.strip()
                    )
                except Exception as e:
                    return render(request, self.template_name, {
                        "cedis_list": Cendis.objects.all().order_by('origin'),
                        "error": f"Error al crear: {str(e)}",
                    })
        
        return redirect("admin_cedis")


class AdminSucursalesView(View):
    template_name = "admin_sucursales.html"

    def get(self, request, *args, **kwargs):
        sucursales_list = Sucursal.objects.all().order_by('name')
        return render(request, self.template_name, {
            "sucursales_list": sucursales_list,
        })

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        
        if action == "delete":
            sucursal_id = request.POST.get("sucursal_id")
            try:
                Sucursal.objects.filter(id=sucursal_id).delete()
            except Exception as e:
                return render(request, self.template_name, {
                    "sucursales_list": Sucursal.objects.all().order_by('name'),
                    "error": f"Error al eliminar: {str(e)}",
                })
        
        elif action == "edit":
            sucursal_id = request.POST.get("sucursal_id")
            new_name = request.POST.get("new_name")
            new_bpl_id = request.POST.get("new_bpl_id")
            try:
                sucursal = Sucursal.objects.get(id=sucursal_id)
                if new_name:
                    sucursal.name = new_name.strip()
                if new_bpl_id:
                    sucursal.bpl_id = int(new_bpl_id)
                sucursal.save()
            except Exception as e:
                return render(request, self.template_name, {
                    "sucursales_list": Sucursal.objects.all().order_by('name'),
                    "error": f"Error al editar: {str(e)}",
                })
        
        elif action == "create":
            new_name = request.POST.get("new_name")
            new_bpl_id = request.POST.get("new_bpl_id")
            if new_name and new_bpl_id:
                try:
                    Sucursal.objects.create(
                        name=new_name.strip(),
                        bpl_id=int(new_bpl_id)
                    )
                except Exception as e:
                    return render(request, self.template_name, {
                        "sucursales_list": Sucursal.objects.all().order_by('name'),
                        "error": f"Error al crear: {str(e)}",
                    })
        
        return redirect("admin_sucursales")
