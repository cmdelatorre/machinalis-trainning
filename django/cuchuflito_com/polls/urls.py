from django.conf.urls import patterns, url

from polls import views

urlpatterns = patterns('',
    url(r'^$', views.PollsIndex.as_view(), name='index'),
    url(r'^archive/$', views.PollsArchiveView.as_view(), name='archive'),
    url(r'^archive_year/$', views.PollsYearArchiveView.as_view(), name='archive_year'),
    url(r'^(?P<poll_id>\d+)/$', views.PollDetail.as_view(), name='detail'),
    url(r'^(?P<poll_id>\d+)/results/$', views.PollResults.as_view(), name='results'),
    url(r'^(?P<poll_id>\d+)/vote/$', views.PollVote.as_view(), name='vote'),
    url(r'^new_poll/$', views.new_poll, name='new_poll'),
    url(r'^(?P<poll_id>\d+)/add_choice/$', views.ChoiceAdd.as_view(), name='add_choice'),
)