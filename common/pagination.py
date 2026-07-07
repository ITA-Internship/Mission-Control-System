from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        max_offset = getattr(settings, "MAX_PAGINATION_OFFSET", 10000)

        page_size = self.get_page_size(request)
        page_number = request.query_params.get(self.page_query_param, 1)

        if not page_number:
            page_number = 1

        try:
            page_number = int(page_number)

            offset = (page_number - 1) * page_size

            if offset > max_offset:
                raise ValidationError(
                    {
                        "page": f"Max pagination depth exceeded. "
                        f"Cannot skip more than {max_offset} records."
                    }
                )
        except (ValueError, TypeError):
            pass

        return super().paginate_queryset(queryset, request, view)
