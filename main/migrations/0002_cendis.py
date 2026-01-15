from django.db import migrations, models


def seed_cendis(apps, schema_editor):
    cendis = apps.get_model("main", "cendis")
    data = [
        ("La Yaguara", "1000101"),
        ("Guatire I", "1000105"),
        ("Guatire II", "1000106"),
        ("Guatire 4", "1000114"),
        ("Guatire 5", "1000115"),
    ]
    for origin, code in data:
        cendis.objects.get_or_create(code=code, defaults={"origin": origin})


def unseed_cendis(apps, schema_editor):
    cendis = apps.get_model("main", "cendis")
    codes = [
        "1000101",
        "1000105",
        "1000106",
        "1000114",
        "1000115",
    ]
    cendis.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="cendis",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("origin", models.CharField(max_length=255)),
                ("code", models.CharField(max_length=50, unique=True)),
            ],
            options={
                "ordering": ["code"],
                "verbose_name": "Cendis",
                "verbose_name_plural": "Cendis",
            },
        ),
        migrations.RunPython(seed_cendis, reverse_code=unseed_cendis),
    ]
