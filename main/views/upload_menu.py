from django.shortcuts import render
from django.views import View


class UploadMenuView(View):
    template_name = "upload_menu.html"

    def get(self, request, *args, **kwargs):
        uploads = [
            {
                "name": "Cargar Excel Maestro y PVP",
                "description": "Sube el archivo .xlsx con hojas Maestro de Productos y PVP.",
                "url": "/subidas/excel/",
            },
            {
                "name": "Planificación por fecha",
                "description": "Define fecha, elige la hoja del Excel y carga la planificación.",
                "url": "/planificacion/",
            },
            {
                "name": "Salidas",
                "description": "Sube el Excel con la hoja de salidas (única hoja) y cárgala tras previsualizar.",
                "url": "/salidas/",
            },
        ]
        return render(request, self.template_name, {"uploads": uploads})
