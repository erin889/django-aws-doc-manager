from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^document$', views.document, name='document'),
	url(r'^pull_file_metadata$', views.pull_file_metadata, name='pull_file_metadata'),
	url(r'^get_settings$', views.get_settings, name='get_settings'),
	url(r'^upload', views.upload, name='upload'),
	url(r'^detail$', views.detail, name='detail')
]