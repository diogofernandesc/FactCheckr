from django.conf.urls import url
from . import views

app_name = 'checkr_app'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^mps/$', views.view_mps, name='view_mps'),
    url(r'^mps/(?P<mp_id>[0-9]+)/$', views.view_mp, name='view_mp'),
