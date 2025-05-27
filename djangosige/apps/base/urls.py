# -*- coding: utf-8 -*-

from django.urls import path, include, re_path
from . import views

from djangosige.configs import DEBUG

app_name = 'base'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
]

if DEBUG:
    urlpatterns += [
        path('404/', views.handler404),
        path('500/', views.handler500),
    ]
