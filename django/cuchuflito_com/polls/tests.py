# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from django.test.html import parse_html
from django.utils import timezone, html
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotAllowed, Http404, QueryDict
from django.contrib.auth.models import AnonymousUser, User
from django.test.client import RequestFactory
from django.db import IntegrityError
from mock import patch

from polls.models import Poll, Choice
from polls import views, forms
from fixtures.polls_factory import UserFactory, PollFactory, ChoiceFactory, DEFAULT_PASSWORD


request_factory = RequestFactory()

# Auxiliar method
def aux_initial_management_form(total_forms=1, extra=None):
    """Creates the formset's management form items."""
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

def formset_management_form(items, extra=None):
    """Creates the formset's management form items."""
    n = len(items)
    form_items = {
            "choice_set-TOTAL_FORMS" : n,
            "choice_set-MAX_NUM_FORMS" : '',
        }
    initial = 0 #counts the choices with id, meaning they already existed (are not new)
    for ctr, (choice_id, choice) in enumerate(items):
        form_items["choice_set-%i-ORDER"%ctr] = ctr
        form_items["choice_set-%i-choice"%ctr] = choice
        if choice_id:
            form_items["choice_set-%i-id"%ctr] = choice_id
            initial += 1
    form_items["choice_set-INITIAL_FORMS"] = initial

    ret_val = form_items
    if extra:
        ret_val = dict(form_items, **extra)
    return ret_val


class AuxMethodTesting(TestCase):
    def test_formset_management_form_empty(self):
        f = formset_management_form([])
        expected = {
            'choice_set-INITIAL_FORMS': 0,
            'choice_set-MAX_NUM_FORMS': '',
            'choice_set-TOTAL_FORMS': 0
        }
        self.assertDictEqual(expected, f)

    def test_formset_management_form_one_with_id(self):
        f1 = formset_management_form([(9,"A")])
        expected = {
            'choice_set-INITIAL_FORMS': 1,
            'choice_set-MAX_NUM_FORMS': '',
            'choice_set-TOTAL_FORMS': 1,
            'choice_set-0-ORDER': 0,
            'choice_set-0-choice': 'A',
            'choice_set-0-id': 9,
        }
        self.assertDictEqual(expected, f1)

    def test_formset_management_form_id_and_not(self):
        f2 = formset_management_form([(9,"A"), (None, "B")])
        expected = {
            'choice_set-INITIAL_FORMS': 1,
            'choice_set-MAX_NUM_FORMS': '',
            'choice_set-TOTAL_FORMS': 2,
            'choice_set-0-ORDER': 0,
            'choice_set-0-choice': 'A',
            'choice_set-0-id': 9,
            'choice_set-1-ORDER': 1,
            'choice_set-1-choice': 'B',
        }
        self.assertDictEqual(expected, f2)

    def test_formset_management_form_not_ids(self):
        f2 = formset_management_form([(None,"A"), (None, "B")])
        expected = {
            'choice_set-INITIAL_FORMS': 0,
            'choice_set-MAX_NUM_FORMS': '',
            'choice_set-TOTAL_FORMS': 2,
            'choice_set-0-ORDER': 0,
            'choice_set-0-choice': 'A',
            'choice_set-1-ORDER': 1,
            'choice_set-1-choice': 'B',
        }
        self.assertDictEqual(expected, f2)

    def test_formset_management_extra_fields(self):
        f2 = formset_management_form([], extra={'foo':'bar'})
        expected = {
            'choice_set-INITIAL_FORMS': 0,
            'choice_set-MAX_NUM_FORMS': '',
            'choice_set-TOTAL_FORMS': 0,
            'foo' : 'bar',
        }
        self.assertDictEqual(expected, f2)

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


class ChoiceModelTesting(TestCase):
    def setUp(self):
        self.choice = ChoiceFactory()

    def test_vote_me_adds_1_vote(self):
        """The Choice.vote_me method adds exactly 1 to the votes of the instance."""
        assert(self.choice.votes == 0)
        self.choice.vote_me()
        self.assertEqual(self.choice.votes, 1)
        self.choice.delete()

    def test_vote_me_saves_results(self):
        """The Choice.vote_me method updates the DB (not only the object instance)"""
        assert(self.choice.votes == 0)
        self.choice.vote_me()
        pk = self.choice.pk
        del(self.choice) # Obj removed just to be extreme and show the votes value comes from the DB.
        self.assertEqual(Choice.objects.get(pk=pk).votes, 1)

    def test_vote_me_work_only_on_DB_saved_instances(self):
        """The Choice.vote_me method works only on saved objects."""
        c = Choice()
        self.assertRaises(IntegrityError, c.vote_me)
        


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


class NewPollGETTesting(TestCase):
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



class NewPollPOSTTesting(TestCase):
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
        self.a_user.delete()

    def test_valid_new_poll_inserts_only_one(self):
        """POST to edit_poll with valid data creates ONE new Poll."""
        assert(len(Poll.objects.all()) == 0)
        valid_data = aux_initial_management_form(extra={
                'question': self.a_question,
            })
        request = request_factory.post(
                reverse('polls:new_poll'),
                data = valid_data
            )
        request.user = self.a_user
        response = views.edit_poll(request)
        self.assertEqual(Poll.objects.all().count(), 1)

    def test_valid_new_poll_redirects_to_voting(self):
        """POST to edit_poll with valid data. redirects to polls:voting."""
        assert(len(Poll.objects.all()) == 0)
        valid_data = aux_initial_management_form(extra={'question': self.a_question})
        response = self.client.post(reverse('polls:new_poll'), data = valid_data)
        self.assertRedirects(
                response, 
                reverse('polls:voting', kwargs={'poll_id':Poll.objects.get(pk=1).pk})
            )

    def test_valid_new_poll_inserts_correct_question(self):
        """POST to edit_poll with valid data creates the correct Poll."""
        valid_data = aux_initial_management_form(extra={
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
        valid_data = aux_initial_management_form(total_forms=4, extra={
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

    def test_new_poll_empty_question_fails(self):
        """POST to edit_poll with an empty question, results in an invalid form."""
        assert(Poll.objects.all().count() == 0)
        # No extra data (such as the 'question' value)
        invalid_data = aux_initial_management_form()
        response = self.client.post(reverse('polls:new_poll'), data = invalid_data)
        self.assertFalse(response.context['poll_form'].is_valid())

    def test_new_poll_empty_question_shows_specific_message(self):
        """POST to edit_poll with an empty question, renders a specific msg"""
        # No extra data (such as the 'question' value)
        invalid_data = aux_initial_management_form()
        request = request_factory.post(
                reverse('polls:new_poll'),
                data = invalid_data,
            )
        request.user = self.a_user
        response = views.edit_poll(request)
        response.render()
        self.assertContains(response, html.escape(forms.EMPTY_QUESTION_MSG))

    def test_new_poll_empty_question_dont_inserts_in_DB(self):
        """POST to edit_poll with an empty question, does not insert a new poll in the DB."""
        assert(len(Poll.objects.all()) == 0)
        # No extra data (such as the 'question' value)
        invalid_data = aux_initial_management_form()
        response = self.client.post(reverse('polls:new_poll'), data = invalid_data)
        self.assertEqual(Poll.objects.all().count(), 0)
        

    def test_new_poll_duplicated_choices_fail(self):
        """POST to edit_poll with an empty question, renders a specific msg"""
        # No extra data (such as the 'question' value)
        choices_values = ['a', 'a']
        invalid_data = aux_initial_management_form(total_forms=2, extra={
                'question': self.a_question,
                "choice_set-0-ORDER" :  1,
                "choice_set-0-choice" : choices_values[0],
                "choice_set-1-ORDER" :  2,
                "choice_set-1-choice" : choices_values[1],
            })
        response = self.client.post(reverse('polls:new_poll'), data = invalid_data)
        self.assertFalse(response.context['choices_formset'].is_valid())



class EditPollTesting(TestCase):
    def setUp(self):
        self.usr = "usr"
        self.a_user = UserFactory(username=self.usr)
        self.a_user.set_password(DEFAULT_PASSWORD)
        self.a_user.save()
        self.client.login(username=self.usr, password=DEFAULT_PASSWORD)
        self.a_question = 'a question?'
        self.poll = self.a_user.poll_set.create(question=self.a_question)
        self.a_choice = 'a choice'
        self.choice = self.poll.choice_set.create(choice=self.a_choice)

    def tearDown(self):
        """Delete the created Poll instance."""
        self.client.logout()
        User.objects.all().delete() # Borra su poll y la choice

    def test_edit_poll_not_authenticated_redirects_to_login(self):
        """Not authenticated users trying edit_poll, must be redirected to login page."""
        self.client.logout() # Make sure it's not logged-in
        original = reverse('polls:edit_poll', kwargs={'poll_id':self.poll.id})
        response = self.client.post(original)
        destiny = "%s?next=%s"%(reverse('polls:login'), original)
        self.assertRedirects(response, destiny)

    def test_edit_not_owned_poll_fails(self):
        """An authenticated user cannot edit polls owned by someone else."""
        assert(self.a_user.is_authenticated())
        another_user = UserFactory(username="someone else")
        another_user.set_password(DEFAULT_PASSWORD)
        another_user.save()
        alien_poll = another_user.poll_set.create(question="whatever")
        # The logged in user tries to edit the alien_poll
        request = request_factory.post(
                reverse('polls:edit_poll', kwargs={'poll_id':alien_poll.id}),
            )
        request.user = self.a_user
        with self.assertRaises(PermissionDenied):
            response = views.edit_poll(request, poll_id=alien_poll.id)

    def test_edit_poll_empty_question_shows_specific_message(self):
        """Try to edit_poll with an empty question, renders a specific msg"""
        # No extra data (such as the 'question' value)
        invalid_data = aux_initial_management_form()
        request = request_factory.post(
                reverse('polls:edit_poll', kwargs={'poll_id':self.poll.id}),
                data = invalid_data,
            )
        request.user = self.a_user
        response = views.edit_poll(request)
        response.render()
        self.assertContains(response, html.escape(forms.EMPTY_QUESTION_MSG))

    def test_edit_poll_with_duplicated_choices_fail(self):
        """POST to /<id>/edit_poll with duplicated choices, invalids formset."""
        # No extra data (such as the 'question' value)
        choices_values = ['a', 'a']
        invalid_data = aux_initial_management_form(total_forms=2, extra={
                'question': self.a_question,
                "choice_set-0-ORDER" :  1,
                "choice_set-0-choice" : choices_values[0],
                "choice_set-1-ORDER" :  2,
                "choice_set-1-choice" : choices_values[1],
            })
        response = self.client.post(
                reverse('polls:edit_poll', kwargs={'poll_id':self.poll.id}),
                data = invalid_data
            )
        self.assertFalse(response.context['choices_formset'].is_valid())

    def test_edit_poll_choices_strip(self):
        """Choices value is stripped (no starting spaces)."""
        # No extra data (such as the 'question' value)
        extra = {'question': self.a_question}
        choices_values =  [ 
                #(choice id, user given value)
                (1   , u'   a   '), 
                (None, u'\t b \t'), 
                (None, u'\n c \n')
            ]
        desired_values = map(unicode.strip, [c for (i,c) in choices_values])
        valid_data = formset_management_form(choices_values, extra=extra)
        #print valid_data
        request = request_factory.post(
                reverse('polls:edit_poll', kwargs={'poll_id':self.poll.id}),
                data = valid_data,
            )
        request.user = self.a_user
        response = views.edit_poll(request, poll_id=self.poll.id)
        for i, db_choice in enumerate(Choice.objects.all()):
            self.assertEqual(db_choice.choice, desired_values[i])



class VotingFormTesting(TestCase):
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


class PollVoteTesting(TestCase):
    def setUp(self):
        self.poll = PollFactory()
        self.c1 = ChoiceFactory(poll=self.poll)
        self.c2 = ChoiceFactory(poll=self.poll)

    def tearDown(self):
        """Delete the created Poll instance."""
        self.poll.delete()

    def test_vote_calls_choice_vote_me(self):
        """polls:emit_vote calls the right Choice vote_me method."""
        request = request_factory.post(
                reverse('polls:emit_vote', kwargs={'poll_id':self.poll.id}),
                data = {'choice':self.c1.id}
            )
        with patch.object(Choice, 'vote_me', autospec=True) as mock_vote_me:
            mock_vote_me.return_value = None
            response = views.PollVote.as_view()(request, poll_id = self.poll.id)
            args, kwargs = mock_vote_me.call_args_list[0]
            target_choice = args[0]
            self.assertEqual(target_choice.id, self.c1.id)

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

