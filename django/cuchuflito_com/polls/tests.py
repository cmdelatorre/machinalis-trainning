# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from django.utils import timezone

from polls.models import Poll, Choice


class PollsViewsTestCase(TestCase):
    fixtures = ['polls_views_testdata.json']

    def test_index(self):
        resp = self.client.get('/polls/')
        self.assertEqual(resp.status_code, 200)

    def test_archive_index(self):
        resp = self.client.get('/polls/archive/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('latest' in resp.context)
        # Only the correct poll is included in the context 
        self.assertEqual([poll.pk for poll in resp.context['latest']], [1])
        poll_1 = resp.context['latest'][0]
        self.assertEqual(poll_1.question, 'Are you learning about testing in Django?')
        self.assertEqual(poll_1.choice_set.count(), 2)
        choices = poll_1.choice_set.all()
        self.assertEqual(choices[0].choice, 'Yes')
        self.assertEqual(choices[0].votes, 1)
        self.assertEqual(choices[1].choice, 'No')
        self.assertEqual(choices[1].votes, 0)
        # The right set of dates is provided in the context
        self.assertTrue('date_list' in resp.context)
        self.assertEqual(len(resp.context['date_list']), 1)
        self.assertEqual(resp.context['date_list'][0].year, 2011)

    def test_archive_index_noPOST(self):
        resp = self.client.post('/polls/archive/')
        self.assertEqual(resp.status_code, 405)

    def test_archive_year(self):
        resp = self.client.get('/polls/archive_year/?year=2011')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('year' in resp.context)
        self.assertEqual(resp.context['year'], u'2011')
        self.assertTrue('object_list' in resp.context)
        # Only the correct poll is included in the context 
        self.assertEqual([poll.pk for poll in resp.context['object_list']], [1])
        poll_1 = resp.context['object_list'][0]
        self.assertEqual(poll_1.question, 'Are you learning about testing in Django?')
        self.assertEqual(poll_1.choice_set.count(), 2)
        choices = poll_1.choice_set.all()
        self.assertEqual(choices[0].choice, 'Yes')
        self.assertEqual(choices[0].votes, 1)
        self.assertEqual(choices[1].choice, 'No')
        self.assertEqual(choices[1].votes, 0)
        # Inexistent year works.
        resp = self.client.get('/polls/archive_year/?year=1982')
        self.assertEqual(resp.status_code, 200)
        # Future year works.
        resp = self.client.get('/polls/archive_year/?year=2082')
        self.assertEqual(resp.status_code, 200)

    def test_archive_year_bad_request(self):
        # No POST
        resp = self.client.post('/polls/archive_year/?year=2011')
        self.assertEqual(resp.status_code, 405)
        # Missing year parameter
        resp = self.client.get('/polls/archive_year/')
        self.assertEqual(resp.status_code, 404)
        resp = self.client.get('/polls/archive_year/?year=')
        self.assertEqual(resp.status_code, 404)
        # Wrong year.
        resp = self.client.get('/polls/archive_year/?year=perro')
        self.assertEqual(resp.status_code, 404)

    def test_detail(self):
        resp = self.client.get('/polls/1/')
        self.assertEqual(resp.status_code, 200)
        # Unbound forms: is_valid == False , errors = {}
        self.assertEqual(resp.context['voting_form'].errors, {})
        self.assertEqual(resp.context['poll'].pk, 1)
        self.assertEqual(resp.context['poll'].question, 'Are you learning about testing in Django?')
        # Ensure that non-existent polls throw a 404.
        resp = self.client.get('/polls/2/')
        self.assertEqual(resp.status_code, 404)

    def test_results(self):
        resp = self.client.get('/polls/1/results/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['poll'].pk, 1)
        self.assertEqual(resp.context['poll'].question, 'Are you learning about testing in Django?')
        # Ensure that non-existent polls throw a 404.
        resp = self.client.get('/polls/2/results/')
        self.assertEqual(resp.status_code, 404)
        
    def test_good_vote(self):
        poll_1 = Poll.objects.get(pk=1)
        self.assertEqual(poll_1.choice_set.get(pk=1).votes, 1)

        resp = self.client.post('/polls/1/vote/', {'choice': 1})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], 'http://testserver/polls/1/results/')

        self.assertEqual(poll_1.choice_set.get(pk=1).votes, 2)

    def test_bad_votes(self):
        def assertBadResponse(resp, expected_msg = u"Este campo es obligatorio."):
            self.assertFalse(resp.context['voting_form'].is_valid())
            the_error = resp.context['voting_form'].errors["choice"]
            self.assertEqual(
                    the_error.as_text().count(expected_msg), 1
                    )

        # Ensure a non-existant PK throws a Not Found.
        resp = self.client.post('/polls/1000000/vote/')
        self.assertEqual(resp.status_code, 404)

        # Sanity check.
        poll_1 = Poll.objects.get(pk=1)
        self.assertEqual(poll_1.choice_set.get(pk=1).votes, 1)

        # Send no POST data.
        resp = self.client.post('/polls/1/vote/')
        self.assertEqual(resp.status_code, 200)
        assertBadResponse(resp)

        # Send junk POST data.
        resp = self.client.post('/polls/1/vote/', {'foo': 'bar'})
        self.assertEqual(resp.status_code, 200)
        assertBadResponse(resp)

        # Send a non-existant Choice PK.
        resp = self.client.post('/polls/1/vote/', {'choice': 300})
        self.assertEqual(resp.status_code, 200)
        assertBadResponse(resp, expected_msg = u"Seleccione una opción válida.")

    def test_add_new_choice(self):
        new_choice_text = "Maybe"
        poll_1 = Poll.objects.get(pk=1)
        self.assertEqual(poll_1.choice_set.count(), 2)
        self.assertEqual(
                poll_1.choice_set.filter(choice__startswith=new_choice_text[0]).count(),
                0
                )
        resp = self.client.post('/polls/1/add_choice/', {'choice': new_choice_text})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], 'http://testserver/polls/1/')
        new_choice = poll_1.choice_set.get(pk=3)
        self.assertEqual(new_choice.choice, new_choice_text)
        self.assertEqual(new_choice.votes, 0)

    def test_bad_new_choice(self):
        def auxAssertBadResponse(resp, expected_msg = u"Este campo es obligatorio."):
            self.assertFalse(resp.context['new_choice_form'].is_valid())
            the_error = resp.context['new_choice_form'].errors["choice"]
            self.assertEqual(
                    the_error.as_text().count(expected_msg), 1
                    )
        # Only POST is accepted
        resp = self.client.get('/polls/1000000/add_choice/')
        self.assertEqual(resp.status_code, 405)
        # Ensure a non-existant PK throws a Not Found.
        resp = self.client.post('/polls/1000000/add_choice/')
        self.assertEqual(resp.status_code, 404)
        # Sanity check: no choices added yet
        poll_1 = Poll.objects.get(pk=1)
        self.assertEqual(poll_1.choice_set.count(), 2)
        # Send no POST data.
        resp = self.client.post('/polls/1/add_choice/')
        self.assertEqual(resp.status_code, 200)
        auxAssertBadResponse(resp)
        # Send junk POST data.
        resp = self.client.post('/polls/1/add_choice/', {'foo': 'bar'})
        self.assertEqual(resp.status_code, 200)
        auxAssertBadResponse(resp)
        # Send an empty choice
        resp = self.client.post('/polls/1/add_choice/', {'choice': ''})
        self.assertEqual(resp.status_code, 200)
        auxAssertBadResponse(resp)
        # Sanity check: no choices added
        poll_1 = Poll.objects.get(pk=1)
        self.assertEqual(poll_1.choice_set.count(), 2)

        