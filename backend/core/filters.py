"""
Reusable filter primitives for the OutreachOS API.

Keeping them in ``core`` lets every module (leads, contacts, companies, and the
campaign/import modules later) expose the same query semantics.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import django_filters as filters
from django import forms
from django.db.models import F
from rest_framework.filters import OrderingFilter


class CsvMultipleChoiceFilter(filters.MultipleChoiceFilter):
    """
    Multi-value choice filter that accepts **both** query styles:

    ``?lead_status=NEW&lead_status=QUALIFIED``   (repeated parameter)
    ``?lead_status=NEW,QUALIFIED``               (comma separated)

    The frontend uses the comma form for compact URLs, while repeated parameters
    stay available for API clients that prefer them. Invalid values raise a 400
    through DRF's exception handler.
    """

    def filter(self, qs, value):
        if not value:
            # Empty selection means "no filter", not "match nothing".
            return qs if self.is_noop_value(value) else qs.none()
        if self.conjoined:
            for item in value:
                qs = self.get_method(qs)(**{f"{self.field_name}__{self.lookup_expr}": item})
            return qs
        return self.get_method(qs)(**{f"{self.field_name}__in": value})

    @staticmethod
    def is_noop_value(value) -> bool:
        """``None``/empty → ignore the filter (do not filter anything out)."""
        if value is None:
            return True
        if isinstance(value, (list, tuple, set)):
            return len(value) == 0
        return value == ""


class CsvSelectMultiple(forms.SelectMultiple):
    """Widget that splits a comma separated value before the field validates."""

    def value_from_datadict(self, data, files, name):
        value = super().value_from_datadict(data, files, name)

        if value is None:
            # Not supplied as a repeated parameter — check for the CSV form.
            raw = data.get(name)
            if raw is None:
                return None
            if isinstance(raw, str):
                return [part.strip() for part in raw.split(",") if part.strip()]
            return raw

        if isinstance(value, (list, tuple)):
            # A single element such as "NEW,QUALIFIED" may arrive in the list.
            expanded: list[str] = []
            for item in value:
                if isinstance(item, str) and "," in item:
                    expanded.extend(part.strip() for part in item.split(",") if part.strip())
                else:
                    expanded.append(item)
            return expanded

        return value


def csv_multiple_choice_filter(**kwargs) -> CsvMultipleChoiceFilter:
    """Factory wiring :class:`CsvMultipleChoiceFilter` to :class:`CsvSelectMultiple`."""
    kwargs.setdefault("widget", CsvSelectMultiple)
    return CsvMultipleChoiceFilter(**kwargs)


class NullsLastOrderingFilter(OrderingFilter):
    """
    Ordering filter that pushes empty values to the end.

    PostgreSQL sorts NULLs first for ``DESC`` ordering, which would put records
    without an employee count (or any other optional field) at the top of a
    "largest companies first" list. Fields listed in ``nulls_last_fields`` are
    ordered with ``NULLS LAST`` in both directions.
    """

    nulls_last_fields: Iterable[str] = ()

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if ordering:
            expressions: list[Any] = []
            for term in ordering:
                field = term.lstrip("-")
                if field in set(self.nulls_last_fields):
                    # Locale-aware ordering is not needed for numeric columns.
                    expression = F(field)
                    descending = term.startswith("-")
                    expressions.append(
                        expression.desc(nulls_last=True)
                        if descending
                        else expression.asc(nulls_last=True)
                    )
                else:
                    expressions.append(term)
            return queryset.order_by(*expressions)
        return queryset
