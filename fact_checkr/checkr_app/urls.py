from django.conf.urls import url
from . import views

app_name = 'pathfinder_app'

urlpatterns = [
    url(r'^$', views.index, name='index'),
]