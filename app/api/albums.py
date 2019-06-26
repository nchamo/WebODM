from django.db import transaction
from django.http import FileResponse
from django.http import HttpResponse
from rest_framework import status, serializers, viewsets, filters, exceptions, permissions, parsers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

import requests

"""
Get available albums
"""
class AvailableAlbumsView(APIView):
    permission_classes = (permissions.AllowAny,)
    parser_classes = (parsers.MultiPartParser, parsers.JSONParser, parsers.FormParser,)

    def get(self, request):
        new_url = 'http://piwigo:9000/ws.php?format=json&method=pwg.categories.getList&recursive=true&tree_output=true'
        categories = requests.get(new_url).json()['result']
        result = flatten_list([build_category(cat) for cat in categories])
        return Response(result, status=status.HTTP_200_OK)
        
def build_category(category):
    name = category['name']
    images = category['nb_images']
    id = category['id']
    subcategories = flatten_list([build_category(subcat) for subcat in category['sub_categories']]) if category['nb_categories'] > 0 else []
    for subcategory in subcategories:
        subcategory['name'] = name + ' > ' + subcategory['name']
    categoryInfo = [{'name': name, 'images': images, 'album_id': id }] if images > 0 else []
    return categoryInfo + subcategories
    
def flatten_list(list_of_lists):
    return [item for sublist in list_of_lists for item in sublist]    