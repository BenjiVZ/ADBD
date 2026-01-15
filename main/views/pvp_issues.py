from django.db.models import Count, Q
from django.shortcuts import render
from django.views import View

from ..models import Pvp


class PvpIssuesView(View):
    template_name = "pvp_issues.html"

    def get(self, request, *args, **kwargs):
        optional_fields = ["description", "price", "product"]
        hidden = set(request.GET.getlist("hide"))
        visible_fields = [f for f in optional_fields if f not in hidden]

        # Missing data: description empty, price <= 0, or product nulo
        missing_qs = (
            Pvp.objects.select_related("product")
            .filter(Q(description__exact="") | Q(price__lte=0) | Q(product__isnull=True))
            .order_by("sku")
        )
        missing_rows = []
        for item in missing_qs:
            missing_visible = []
            if "description" in visible_fields and not item.description:
                missing_visible.append("description")
            if "price" in visible_fields and (item.price is None or item.price <= 0):
                missing_visible.append("price")
            if "product" in visible_fields and item.product is None:
                missing_visible.append("product")
            if not missing_visible:
                continue
            missing_rows.append((item, missing_visible))

        # Duplicates by SKU
        duplicate_keys = (
            Pvp.objects.values("sku")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
            .order_by("-count", "sku")
        )
        duplicate_skus = [d["sku"] for d in duplicate_keys]
        duplicates = {}
        if duplicate_skus:
            for row in Pvp.objects.filter(sku__in=duplicate_skus).select_related("product").order_by("sku", "id"):
                duplicates.setdefault(row.sku, []).append(row)

        return render(
            request,
            self.template_name,
            {
                "missing_rows": missing_rows,
                "missing_total": len(missing_rows),
                "duplicates": duplicates,
                "duplicate_groups": len(duplicate_keys),
                "optional_fields": optional_fields,
                "visible_fields": visible_fields,
                "hidden_fields": hidden,
            },
        )
