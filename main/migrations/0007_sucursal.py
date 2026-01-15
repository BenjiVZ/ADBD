from django.db import migrations, models

SUCURSALES = [
    (27, "LA YAGUARA"),
    (28, "SAN MARTIN 1"),
    (29, "SAN MARTIN 2"),
    (31, "MUEBLES ANTUAN"),
    (33, "MUEBLERIA"),
    (37, "VALENCIA"),
    (38, "GUATIRE 2022"),
    (39, "LA TRINIDAD"),
    (40, "LA CALIFORNIA"),
    (41, "BARQUISIMETO"),
    (44, "TERMINAL LA GUAIRA"),
    (46, "BARBUR"),
    (48, "LA CANDELARIA"),
    (49, "CCCT"),
    (51, "LAS MERCEDES"),
    (54, "CAGUA"),
    (58, "LOS TEQUES"),
    (59, "LECHERIA"),
    (63, "MARACAY"),
    (65, "MARACAIBO"),
    (68, "PUERTO ORDAZ"),
    (69, "TACHIRA"),
    (70, "SABANA GRANDE"),
    (72, "NUEVA GRANADA"),
    (74, "SAN MARTIN 4"),
    (75, "VALENCIA 2"),
    (76, "MATURIN"),
    (77, "TRUJILLO"),
    (78, "PUERTO LA CRUZ"),
    (79, "EL PARAISO"),
    (80, "VENTAS ONLINE"),
    (81, "BARQUISIMETO 2"),
    (82, "SAN FELIPE"),
    (83, "MARACAY II"),
    (84, "MERIDA"),
    (85, "CHARALLAVE"),
    (86, "BARINAS"),
    (87, "LOS TEQUES II"),
    (88, "MARACAIBO II"),
    (89, "ACARIGUA"),
    (90, "VALLE DE LA PASCUA"),
    (91, "CUMANA"),
    (92, "SAN DIEGO"),
    (93, "MARGARITA"),
    (94, "CAGUA II"),
    (96, "TIENDA TORRE"),
]


def seed_sucursales(apps, schema_editor):
    Sucursal = apps.get_model("main", "Sucursal")
    for bpl_id, name in SUCURSALES:
        Sucursal.objects.get_or_create(bpl_id=bpl_id, defaults={"name": name})


def unseed_sucursales(apps, schema_editor):
    Sucursal = apps.get_model("main", "Sucursal")
    Sucursal.objects.filter(bpl_id__in=[bpl_id for bpl_id, _ in SUCURSALES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0006_planificacion"),
    ]

    operations = [
        migrations.CreateModel(
            name="Sucursal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("bpl_id", models.IntegerField(unique=True)),
                ("name", models.CharField(max_length=255, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Sucursal",
                "verbose_name_plural": "Sucursales",
                "ordering": ["name"],
            },
        ),
        migrations.RunPython(seed_sucursales, unseed_sucursales),
    ]
