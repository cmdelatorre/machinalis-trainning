# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from django.http import HttpResponseNotAllowed, Http404, QueryDict

from polls.models import Poll, Choice
from polls import views, forms
from fixtures.polls_factory import PollFactory, ChoiceFactory


request_factory = RequestFactory()


class PollsIndexViewsTestCase(TestCase):
    def setUp(self):
        self.poll = PollFactory()
        

    def tearDown(self):
        self.poll.delete()

    def test_index(self):
        request = request_factory.get(reverse('polls:index'))
        response = views.PollsIndex.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_archive_index(self):
        """The listchoices template is used in the archive view"""
        request = request_factory.get(reverse('polls:archive'))
        response = views.PollsArchiveView.as_view()(request)
        self.assertTemplateUsed(response, "polls/listchoices.html")

    def test_archive_index_noPOST(self):
        """The archive view doesn't accept POST method"""
        request = request_factory.post(reverse('polls:archive'))
        response = views.PollsArchiveView.as_view()(request)
        self.assertEqual(response.status_code, 405)


class YearArchiveViewTest(TestCase):
    def test_year_archive_bad_year_parameter(self):
        """Passing a year that's not a number, responds with 404"""
        url = reverse('polls:archive_year')
        request = request_factory.get(url, {'year':'perro'})
        with self.assertRaises(Http404):
            views.PollsYearArchiveView.as_view()(request)

    def test_year_archive_bad_without_year_parameter(self):
        """Not passing a year, responds with 404"""
        request = request_factory.get(reverse('polls:archive_year'))
        with self.assertRaises(Http404):
            views.PollsYearArchiveView.as_view()(request)
        
    def test_year_archive_noPOST(self):
        """The year archive doesn't accept POST method"""
        request = request_factory.post(reverse('polls:archive_year'))
        response = views.PollsYearArchiveView.as_view()(request)
        self.assertEqual(response.status_code, 405)

    # This test is to verufy that the view's configuration don't change
    def test_year_archive_accepts_future_dates(self):
        """Passing a future year, works ok (responds with 200)"""
        url = "%s?%s=%s;"%(reverse('polls:archive_year'), "year", "2050")
        request = request_factory.get(url)
        response = views.PollsYearArchiveView.as_view()(request)
        self.assertEqual(response.status_code, 200)

