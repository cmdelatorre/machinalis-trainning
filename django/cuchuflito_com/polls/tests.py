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
        self.usr = "usr"
        self.a_user = UserFactory(username=self.usr)
        self.a_user.set_password(DEFAULT_PASSWORD)
        self.a_user.save()

    def tearDown(self):
        """Delete the created Poll instance."""
        self.client.logout()

    def test_new_poll_not_authenticated_redirects_to_login(self):
        """Not authenticated users accesing new_poll, must be redirected to login page."""
        self.client.logout() # Make sure it's not logged-in
        original = reverse('polls:new_poll')
        response = self.client.get(original)
        destiny = "%s?next=%s"%(reverse('polls:login'), original)
        self.assertRedirects(response, destiny)

    def test_any_authenticated_user_can_create_polls(self):
        """Authenticated users accesing (GET) new_poll, receive 200."""
        request = request_factory.get(reverse('polls:new_poll'))
        request.user = UserFactory()
        response = views.edit_poll(request)
        self.assertEqual(response.status_code, 200)

    def test_new_poll_form_is_unbound(self):
        """When requiring new_poll, the poll_form is not bound to any poll instance."""
        self.client.login(username=self.usr, password=DEFAULT_PASSWORD)
        response = self.client.get(reverse('polls:new_poll'))
        self.assertFalse(response.context['poll_form'].is_bound)

    def __get_new_poll_choices_forms(self):
        self.client.login(username=self.usr, password=DEFAULT_PASSWORD)
        response = self.client.get(reverse('polls:new_poll'))
        return response.context['choices_formset'].forms

    def test_new_poll_choices_formset_has_only_one_form(self):
        """When requiring new_poll, the involved choices_formset has only one InlineChoiceForm."""
        choice_forms = self.__get_new_poll_choices_forms()
        self.assertEqual(len(choice_forms), 1)
        self.assertIsInstance(choice_forms[0], forms.InlineChoiceForm)

    def test_new_poll_choice_form_is_unbound(self):
        """When requiring new_poll, the InlineChoiceForm is unbound."""
        the_choice_form = self.__get_new_poll_choices_forms()[0]
        self.assertFalse(the_choice_form.is_bound)

    def test_new_poll_empty_question_shows_form_error(self):
        """When posting edit_poll, the InlineChoiceForm is unbound."""
        the_choice_form = self.__get_new_poll_choices_forms()[0]
        self.assertFalse(the_choice_form.is_bound)


class EditPollTesting(TestCase):
    def setUp(self):
        self.usr = "usr"
        self.a_user = UserFactory(username=self.usr)
        self.a_user.set_password(DEFAULT_PASSWORD)
        self.a_user.save()
        self.client.login(username=self.usr, password=DEFAULT_PASSWORD)
        self.a_question = 'a question?'
        self.a_choice = 'a choice'


    def tearDown(self):
        """Delete the created Poll instance."""
        self.client.logout()

    def __initial_management_form(self, total_forms=1, extra=None):
        ret_val = {
                "choice_set-0-ORDER" : 1,
                "choice_set-0-choice" : '',
                "choice_set-0-id" : '',
                "choice_set-TOTAL_FORMS" : total_forms,
                "choice_set-INITIAL_FORMS" : 0,
                "choice_set-MAX_NUM_FORMS" : '',
            }
        if extra:
            ret_val = dict(ret_val, **extra)
        return ret_val

    def test_valid_new_poll_inserts_one(self):
        """POST to edit_poll with valid data creates ONE new Poll."""
        assert(len(Poll.objects.all()) == 0)
        valid_data = self.__initial_management_form(extra={
                'question': self.a_question,
            })
        request = request_factory.post(
                reverse('polls:new_poll'),
                data = valid_data
            )
        request.user = self.a_user
        response = views.edit_poll(request)
        self.assertEqual(len(Poll.objects.all()), 1)

    def test_valid_new_poll_redirects_to_voting(self):
        """POST to edit_poll with valid data. redirects to polls:voting."""
        assert(len(Poll.objects.all()) == 0)
        valid_data = self.__initial_management_form(extra={'question': self.a_question})
        response = self.client.post(reverse('polls:new_poll'), data = valid_data)
        self.assertRedirects(
                response, 
                reverse('polls:voting', kwargs={'poll_id':Poll.objects.get(pk=1).pk})
            )

    def test_valid_new_poll_inserts_correct_question(self):
        """POST to edit_poll with valid data creates the correct Poll."""
        valid_data = self.__initial_management_form(extra={
                'question': self.a_question,
            })
        request = request_factory.post(
                reverse('polls:new_poll'),
                data = valid_data
            )
        request.user = self.a_user
        response = views.edit_poll(request)
        self.assertEqual(Poll.objects.get(pk=1).question, self.a_question)

    def test_valid_new_poll_inserts_correct_choices(self):
        """POST to edit_poll with valid data creates the correct Choices."""
        choices_values = ['a', 'b', 'c', 'd']
        valid_data = self.__initial_management_form(total_forms=4, extra={
                'question': self.a_question,
                "choice_set-0-ORDER" :  1,
                "choice_set-0-choice" : choices_values[0],
                "choice_set-1-ORDER" :  2,
                "choice_set-1-choice" : choices_values[1],
                "choice_set-2-ORDER" :  3,
                "choice_set-2-choice" : choices_values[2],
                "choice_set-3-ORDER" :  4,
                "choice_set-3-choice" : choices_values[3],
            })
        request = request_factory.post(
                reverse('polls:new_poll'),
                data = valid_data,
            )
        request.user = self.a_user
        response = views.edit_poll(request)
        db_values = [d.choice for d in Choice.objects.all()]
        self.assertItemsEqual(choices_values, db_values)





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
                reverse('polls:emit_vote', kwargs={'poll_id':self.poll.id}),
                data = data
            )
        response = views.PollVote.as_view()(request, poll_id = self.poll.id)
        modified_n_votes = Choice.objects.get(pk=self.c1.pk).votes
        self.assertEqual(modified_n_votes, original_n_votes + 1)

    def test_vote_redirects_ok(self):
        """Succesful voting redirects to results page."""
        data = {'choice':self.c1.id}
        response = self.client.post(
                reverse('polls:emit_vote', kwargs={'poll_id':self.poll.id}),
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
                reverse('polls:emit_vote', kwargs={'poll_id':inexisten_id}),
                data = data,
            )
        with self.assertRaises(Http404):
            response = views.PollVote.as_view()(request, poll_id = inexisten_id)
            self.assertEqual(response.status_code, 404)

    def test_vote_without_data(self):
        """Voting with empty form-data responds a form with errors."""
        data = {}
        request = request_factory.post(
                reverse('polls:emit_vote', kwargs={'poll_id':self.poll.id}),
                data = data,
            )
        response = views.PollVote.as_view()(request, poll_id = self.poll.id)
        self.assertContains(response, u"You must select a choice to vote.")

    def test_vote_invalid_choice(self):
        """Voting for a wrong choice responds a form with errors."""
        wrong_choice = 505050
        data = {'choice':wrong_choice}
        request = request_factory.post(
                reverse('polls:emit_vote', kwargs={'poll_id':self.poll.id}),
                data = data,
            )
        response = views.PollVote.as_view()(request, poll_id = self.poll.id)
        print response
        self.assertContains(response, u"Select a valid choice.")

