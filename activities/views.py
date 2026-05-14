from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse

class ActivitySearchView(TemplateView):
    template_name = 'activities/search.html'

class ActivityDetailView(TemplateView):
    template_name = 'activities/detail.html'

class ActivitySearchAPIView(TemplateView):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'message': 'Activities API endpoint'})
