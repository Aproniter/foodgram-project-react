from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'
    
    # def get_paginated_response(self, data):
    #     print(data)
    #     return Response({
    #         'next': self.get_next_link(),
    #         'previous': self.get_previous_link(),
    #         'count': self.page.paginator.count,
    #         'results': data,
    #     })
