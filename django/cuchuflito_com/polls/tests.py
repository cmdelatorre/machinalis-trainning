# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from django.http import HttpResponseNotAllowed, Http404, QueryDict
from django.contrib.auth.models import AnonymousUser


from polls.models import Poll, Choice
from polls import views, forms
from fixtures.polls_factory import UserFactory, PollFactory, ChoiceFactory, DEFAULT_PASSWORD


request_factory = RequestFactory()

class PollsModelTesting(TestCase):
    def setUp(self):
        self.poll = PollFactory()

    def tearDown(self):
        self.poll.delete()

    def test_get_max_votes_no_voted(self):
        """A poll with no votes, get_max_votes returns 0."""
        self.assertEqual(self.poll.get_max_votes(), 0)

    def test_get_max_votes_nominal(self):
        """get_max_votes returns the number of votes of the most voted choice."""
        c_max = ChoiceFactory(poll = self.poll, choice = "A winner choice")
        c_max.vote_me()
        c_max.vote_me()
        c_max.vote_me()

        c_med = ChoiceFactory(poll = self.poll, choice = "A choice")
        c_med.vote_me()
        c_med.vote_me()

        c_min = ChoiceFactory(poll = self.poll, choice = "A looser choice")
        c_min.vote_me()

        self.assertEqual(self.poll.get_max_votes(), 3)

    def test_has_winners_returns_none_if_no_choice(self):
        """If the poll has not choices, has_winners resturns []."""
        self.assertItemsEqual(self.poll.has_winners(), [])

    def test_has_winners_only_one_winning_choice(self):
        """If the poll has a single winner, has_winners returns it."""
        c_max = ChoiceFactory(poll = self.poll, choice = "A winner choice")
        c_max.vote_me()
        c_max.vote_me()
        c_med = ChoiceFactory(poll = self.poll, choice = "A choice")
        c_med.vote_me()
        self.assertItemsEqual(self.poll.has_winners(), [c_max])

    def test_has_winners_multiple_winning_choices(self):
        """If the poll has many winners, has_winners returns all of them."""
        winner_1 = ChoiceFactory(poll = self.poll)
        winner_1.vote_me()
        winner_1.vote_me()
        winner_2 = ChoiceFactory(poll = self.poll)
        winner_2.vote_me()
        winner_2.vote_me()
        looser = ChoiceFactory(poll = self.poll)
        looser.vote_me()
        self.assertItemsEqual(self.poll.has_winners(), [winner_2, winner_1])

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


class NewPollTesting(TestCase):
    def setUp(self):
        self.poll = PollFactory()
        self.usr = "usr"
        self.passwd = "pass"
        self.a_user = UserFactory(username=self.usr, password=DEFAULT_PASSWORD)

    def tearDown(self):
        """Delete the created Poll instance."""
        self.poll.delete()

    def test_not_authenticated_user_cant_create_polls(self):
        """Not authenticated users accesing edit_poll, receive 403."""
        original = reverse('polls:new_poll')
        # si llamo directamente la vista, en vez de client.get, 
        # sale error AttributeError: 'HttpResponseRedirect' object has no attribute 'client'
        response = self.client.get(original)
        destiny = "%s?next=%s"%(reverse('polls:login'), original)
        self.assertRedirects(response, destiny)

    def test_every_authenticated_user_can_create_polls(self):
        """Authenticated users accesing (GET) edit_poll, receive 200."""
        request = request_factory.get(reverse('polls:new_poll'))
        request.user = UserFactory()
        response = views.edit_poll(request)
        self.assertEqual(response.status_code, 200)

    def test_new_poll_view_unbound_forms(self):
        """When requiring new_poll, the involved forms are not bound to any poll instance."""
        self.client.login(username=self.usr, password=DEFAULT_PASSWORD)
        request = request_factory.get(reverse('polls:new_poll'))
        request.user = UserFactory()
        response = views.edit_poll(request)
        response.render()
        self.assertFalse(response.context['voting_form'].is_bound())

    # def test_new_poll_empty_question_render_error(self):
    #     """Sending an empty question renders the same edit_poll page"""
    #     request = request_factory.post(
    #             reverse('polls:new_poll'), 
    #             kwargs={'poll_id':self.poll.id},
    #             data = {
    #                 "choice_set-TOTAL_FORMS" : 1,
    #                 "choice_set-INITIAL_FORMS" : 0,
    #                 "choice_set-MAX_NUM_FORMS" : '',
    #         })
    #     request.user = UserFactory()
    #     response = views.edit_poll(request)
    #     self.assertEqual(response.status_code, 200)


class PollsDetailViewTestCase(TestCase):
    def setUp(self):
        self.poll = PollFactory()

    def tearDown(self):
        """Delete the created Poll instance."""
        self.poll.delete()

    def test_voting_form_has_good_choices(self):
        """The choices in the VotingForm object are correct."""
        # Create a couple of Choices to check if they are in the form's queryset.
        c1 = ChoiceFactory(poll=self.poll)
        c2 = ChoiceFactory(poll=self.poll)
        form = forms.VoteForm(poll=self.poll)
        self.assertQuerysetEqual(
                form.fields['choice'].queryset, 
                [c1.id, c2.id],
                transform=lambda c:c.id
            )


class PollsVoteTestCase(TestCase):
    def setUp(self):
        self.poll = PollFactory()
        self.c1 = ChoiceFactory(poll=self.poll)
        self.c2 = ChoiceFactory(poll=self.poll)

    def tearDown(self):
        """Delete the created Poll instance."""
        self.poll.delete()

    def test_vote_ok(self):
        """Voting an existing choice adds 1 to its votes."""
        original_n_votes = self.c1.votes
        data = {'choice':self.c1.id}
        request = request_factory.post(
                reverse('polls:vote', kwargs={'poll_id':self.poll.id}),
                data = data
            )
        response = views.PollVote.as_view()(request, poll_id = self.poll.id)
        modified_n_votes = Choice.objects.get(pk=self.c1.pk).votes
        self.assertEqual(modified_n_votes, original_n_votes + 1)

    def test_vote_redirects_ok(self):
        """Succesful voting redirects to results page."""
        data = {'choice':self.c1.id}
        response = self.client.post(
                reverse('polls:vote', kwargs={'poll_id':self.poll.id}),
                data = data
            )
        self.assertRedirects(
                response, 
                reverse('polls:results', kwargs={'poll_id':self.poll.id}),
            )

    def test_vote_nonExistant(self):
        """Voting for a non-existing poll responds a 404."""
        inexisten_id = 10000
        data = {'choice':self.c1.id}
        request = request_factory.post(
                reverse('polls:vote', kwargs={'poll_id':inexisten_id}),
                data = data,
            )
        with self.assertRaises(Http404):
            response = views.PollVote.as_view()(request, poll_id = inexisten_id)
            self.assertEqual(response.status_code, 404)

    def test_vote_without_data(self):
        """Voting with empty form-data responds a form with errors."""
        data = {}
        request = request_factory.post(
                reverse('polls:vote', kwargs={'poll_id':self.poll.id}),
                data = data,
            )
        response = views.PollVote.as_view()(request, poll_id = self.poll.id)
        self.assertContains(response, u"You must select a choice to vote.")

    def test_vote_invalid_choice(self):
        """Voting for a wrong choice responds a form with errors."""
        wrong_choice = 505050
        data = {'choice':wrong_choice}
        request = request_factory.post(
                reverse('polls:vote', kwargs={'poll_id':self.poll.id}),
                data = data,
            )
        response = views.PollVote.as_view()(request, poll_id = self.poll.id)
        self.assertContains(response, u"Seleccione una opción válida.")

