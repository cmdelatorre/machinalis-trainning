from django.conf.urls import patterns, url

from polls import views

urlpatterns = patterns('',
    url(r'^$', views.PollsIndex.as_view(), name='index'),
    url(r'^archive/$', views.PollsArchiveView.as_view(), name='archive'),
    url(r'^archive_year/$', views.PollsYearArchiveView.as_view(), name='archive_year'),
    url(r'^new_poll/$', views.new_poll, name='new_poll'),
    url(r'^(?P<poll_id>\d+)/$', views.edit_poll, name='edit_poll'),
    url(r'^(?P<poll_id>\d+)/voting/$', views.PollVoting.as_view(), name='voting'),
    url(r'^(?P<poll_id>\d+)/emit_vote/$', views.PollVote.as_view(), name='emit_vote'),
    url(r'^(?P<poll_id>\d+)/results/$', views.PollResults.as_view(), name='results'),
    url(r'^facts/$', views.facts, name='facts'),
)