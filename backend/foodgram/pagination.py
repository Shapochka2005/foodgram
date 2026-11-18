from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """Пагинация с управляемой длиной страницы через параметр limit."""

    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 100
