from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse

class PackageSearchView(TemplateView):
    template_name = 'packages/search.html'

class PackageDetailView(TemplateView):
    template_name = 'packages/detail.html'

class PackageSearchAPIView(TemplateView):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'message': 'Packages API endpoint'})
