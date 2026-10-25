from django.urls import path
from . import views

app_name = 'editor'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/upload/', views.upload_image, name='upload_image'),
    path('api/apply-filters/', views.apply_filters, name='apply_filters'),
    path('api/remove-filter/', views.remove_filter, name='remove_filter'),
    path('api/reset-image/', views.reset_image, name='reset_image'),
    path('api/save-image/', views.save_image, name='save_image'),
]