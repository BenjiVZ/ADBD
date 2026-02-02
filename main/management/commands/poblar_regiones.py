from django.core.management.base import BaseCommand
from main.models import GerenteRegional, Region, Sucursal


class Command(BaseCommand):
    help = "Poblar datos de Gerentes Regionales, Regiones y vincular Sucursales"

    def handle(self, *args, **options):
        # Datos de la estructura organizacional
        # Formato: gerente -> [(region, tienda), ...]
        data = {
            "Paholo Silva": [
                ("Gran Caracas R1", "BARBUR"),
                ("Gran Caracas R1", "CHARALLAVE"),
                ("Gran Caracas R1", "EL PARAISO"),
                ("Gran Caracas R1", "GUATIRE 2022"),
                ("Gran Caracas R1", "LAS MERCEDES"),
                ("Gran Caracas R1", "LOS TEQUES"),
                ("Gran Caracas R1", "LOS TEQUES II"),
                ("Gran Caracas R1", "MUEBLERIA"),
                ("Gran Caracas R1", "MUEBLES ANTUAN"),
                ("Gran Caracas R1", "SABANA GRANDE"),
                ("Gran Caracas R1", "TIENDA TORRE"),
                ("Centro", "VALLE DE LA PASCUA"),  # Tienda en región Centro pero gerenciada por Paholo
            ],
            "Madeline Marquez": [
                ("Gran Caracas R2", "CCCT"),
                ("Gran Caracas R2", "LA CALIFORNIA"),
                ("Gran Caracas R2", "LA CANDELARIA"),
                ("Gran Caracas R2", "TERMINAL LA GUAIRA"),
                ("Gran Caracas R2", "LA TRINIDAD"),
                ("Gran Caracas R2", "NUEVA GRANADA"),
                ("Gran Caracas R2", "SAN MARTIN 1"),
                ("Gran Caracas R2", "SAN MARTIN 2"),
                ("Gran Caracas R2", "SAN MARTIN 4"),
            ],
            "Jhonny Ibarah": [
                ("Centro", "CAGUA"),
                ("Centro", "CAGUA II"),
                ("Centro", "MARACAY"),
                ("Centro", "MARACAY II"),
                ("Centro", "SAN DIEGO"),
                ("Centro", "VALENCIA"),
                ("Centro", "VALENCIA 2"),
            ],
            "Carmen Mijares": [
                ("Oriente", "CUMANA"),
                ("Oriente", "LECHERIA"),
                ("Oriente", "MARGARITA"),
                ("Oriente", "MATURIN"),
                ("Oriente", "PUERTO LA CRUZ"),
                ("Oriente", "PUERTO ORDAZ"),
            ],
            "Marbelys Araujo": [
                ("Occidente", "ACARIGUA"),
                ("Occidente", "BARINAS"),
                ("Occidente", "BARQUISIMETO"),
                ("Occidente", "BARQUISIMETO 2"),
                ("Occidente", "MARACAIBO"),
                ("Occidente", "MARACAIBO II"),
                ("Occidente", "MERIDA"),
                ("Occidente", "SAN FELIPE"),
                ("Occidente", "TACHIRA"),
                ("Occidente", "TRUJILLO"),
            ],
        }

        self.stdout.write(self.style.NOTICE("Iniciando población de datos..."))
        
        total_gerentes = 0
        total_regiones = 0
        total_sucursales_vinculadas = 0
        total_sucursales_no_encontradas = 0

        # Crear todas las regiones primero
        all_regions = set()
        for tiendas in data.values():
            for region_name, _ in tiendas:
                all_regions.add(region_name)
        
        for region_name in all_regions:
            region, created = Region.objects.get_or_create(name=region_name)
            if created:
                total_regiones += 1
                self.stdout.write(f"  ✅ Región creada: {region_name}")

        for gerente_name, tiendas in data.items():
            # Crear o obtener gerente
            gerente, created = GerenteRegional.objects.get_or_create(name=gerente_name)
            if created:
                total_gerentes += 1
                self.stdout.write(f"\n  ✅ Gerente creado: {gerente_name}")
            else:
                self.stdout.write(f"\n  ℹ️ Gerente existente: {gerente_name}")

            for region_name, tienda_name in tiendas:
                if not tienda_name.strip():
                    continue
                
                # Obtener región
                region = Region.objects.filter(name=region_name).first()
                
                # Buscar sucursal por nombre (insensible a mayúsculas)
                try:
                    sucursal = Sucursal.objects.get(name__iexact=tienda_name.strip())
                    sucursal.region = region
                    sucursal.gerente = gerente
                    sucursal.save()
                    total_sucursales_vinculadas += 1
                    self.stdout.write(f"    🔗 {sucursal.name} -> Región: {region_name}, Gerente: {gerente_name}")
                except Sucursal.DoesNotExist:
                    total_sucursales_no_encontradas += 1
                    self.stdout.write(
                        self.style.WARNING(f"    ⚠️ Sucursal NO encontrada: {tienda_name}")
                    )
                except Sucursal.MultipleObjectsReturned:
                    self.stdout.write(
                        self.style.ERROR(f"    ❌ Múltiples sucursales: {tienda_name}")
                    )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("RESUMEN:"))
        self.stdout.write(f"  Gerentes creados: {total_gerentes}")
        self.stdout.write(f"  Regiones creadas: {total_regiones}")
        self.stdout.write(f"  Sucursales vinculadas: {total_sucursales_vinculadas}")
        if total_sucursales_no_encontradas:
            self.stdout.write(
                self.style.WARNING(f"  Sucursales NO encontradas: {total_sucursales_no_encontradas}")
            )
        self.stdout.write(self.style.SUCCESS("=" * 50))
