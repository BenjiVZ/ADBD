from django.db.models import Count, Q
from django.shortcuts import render
from django.views import View

from ..models import Product


class MissingProductsView(View):
    template_name = "missing_products.html"

    def get(self, request, *args, **kwargs):
        optional_fields = ["group", "manufacturer", "category", "subcategory", "size"]
        hidden = set(request.GET.getlist("hide"))
        visible_fields = [f for f in optional_fields if f not in hidden]

        # Build Q to find products with any empty string field among the set
        condition = Q()
        for field in optional_fields:
            condition |= Q(**{f"{field}__exact": ""})
        products = Product.objects.filter(condition).order_by("code")

        rows = []
        for p in products:
            missing_visible = [f for f in visible_fields if not getattr(p, f)]
            if not missing_visible:
                continue  # skip rows whose only missing fields are hidden
            rows.append((p, missing_visible))

        # Duplicates by code
        duplicate_keys = (
            Product.objects.values("code")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
            .order_by("-count", "code")
        )
        duplicate_codes = [d["code"] for d in duplicate_keys]
        duplicates = {}
        if duplicate_codes:
            for row in Product.objects.filter(code__in=duplicate_codes).order_by("code", "id"):
                duplicates.setdefault(row.code, []).append(row)

        return render(
            request,
            self.template_name,
            {
                "rows": rows,
                "optional_fields": optional_fields,
                "visible_fields": visible_fields,
                "hidden_fields": hidden,
                "total": len(rows),
                "duplicates": duplicates,
                "duplicate_groups": len(duplicate_keys),
            },
        )
