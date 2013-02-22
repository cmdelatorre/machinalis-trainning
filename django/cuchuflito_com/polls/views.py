# -*- coding: utf-8 -*-
import datetime

from django.shortcuts import get_object_or_404, render, redirect, render_to_response
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.template import RequestContext
from django.template.response import TemplateResponse
from django.views.generic import ListView, DetailView, FormView
from django.views.generic.dates import ArchiveIndexView, YearArchiveView
from django.db.models import Avg, Max, Sum, Q, F
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User

from polls.models import Poll, Choice

from polls.forms import VoteForm, PollDetailForm, ChoiceFormSet


# Pagination for year-view: number of polls to show per page.
NPOLLSINPAGE = 10

@login_required
def edit_poll(request, poll_id=None):
    poll = None
    if poll_id:
        poll = get_object_or_404(Poll, pk=poll_id)
        if poll.created_by != request.user:
            raise PermissionDenied

    if request.method == "POST":
        poll_form = PollDetailForm(request.POST, instance=poll)
        choices_formset = ChoiceFormSet(request.POST, request.FILES, instance=poll)
        if poll_form.is_valid():
            poll = poll_form.save(commit=False)
            request.user.poll_set.add(poll)
            choices_formset = ChoiceFormSet(request.POST, request.FILES, instance=poll)
            if  choices_formset.is_valid():
                poll.save()
                choices_formset.save()
                return redirect('polls:voting', poll_id=poll.pk)
        # Some form is not valid.
    else:
        poll_form = PollDetailForm(instance=poll)
        choices_formset = ChoiceFormSet(instance=poll)
    #
    return TemplateResponse(
            request,
            "polls/poll_detail.html", 
            {"poll_form" : poll_form, "choices_formset" : choices_formset}
        )


class PollsIndex(ListView):
    model = Poll
    template_name = "polls/index.html"


class PollVoting(DetailView):
    context_object_name = 'poll'
    pk_url_kwarg = 'poll_id'
    model = Poll
    template_name = "polls/poll_voting.html"

    def get_context_data(self, **kwargs):
        context = super(PollVoting, self).get_context_data(**kwargs)
        context['voting_form'] = VoteForm(poll=self.get_object())
        return context


class PollVote(FormView):
    template_name = 'polls/poll_voting.html'

    def get_form(self, form_class):
        self.poll = get_object_or_404(Poll, pk=self.kwargs['poll_id'])
        return VoteForm(self.request.POST, poll=self.poll)

    def form_valid(self, form):
        choice = form.cleaned_data['choice']
        choice.vote_me()
        choice.save()
        return redirect('polls:results', poll_id=self.poll.pk)

    def form_invalid(self, form):
        context = {'poll': self.poll, 'voting_form': form}
        return render(self.request, 'polls/poll_voting.html', context)


class PollResults(DetailView):
    context_object_name = 'poll'
    pk_url_kwarg = 'poll_id'
    model = Poll
    template_name = "polls/poll_results.html"


class PollsArchiveView(ArchiveIndexView):
    queryset = Poll.objects.all()
    date_field = "pub_date"
    allow_future = True
    allow_empty = True
    paginate_by = NPOLLSINPAGE


class PollsYearArchiveView(YearArchiveView):
    queryset = Poll.objects.all()
    date_field = "pub_date"
    make_object_list = True
    allow_future = True
    allow_empty = True
    paginate_by = NPOLLSINPAGE

    def get_year(self):
        "Overwrite to check the case the 'year' parameter is not an integer."
        year = super(YearArchiveView, self).get_year()
        try:
            int(year)
        except ValueError:
            raise Http404(u"Year badly specified: not a number.")
        return year


class FactsView(ListView):
    template_name = "polls/facts.html"
    context_object_name = "facts_list"

    @method_decorator(permission_required('polls.can_view_stats', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(FactsView, self).dispatch(*args, **kwargs)

    def poll_with_votes(self):
        voted = Poll.objects.annotate(s=Sum('choice__votes')).filter(s__gt=0)
        return ("Polls with votes", voted)

    def poll_with_no_votes(self):
        no_votes = Poll.objects.annotate(s=Sum('choice__votes')).filter(s=0)
        return ("Polls with no votes", no_votes)

    def most_voted_choice(self):
        the_choice = Choice.objects.order_by('-votes')[0]
        return ("Poll with the most voted choice <small>(%s - %i votes)</small>"%(the_choice.choice, the_choice.votes), 
                [the_choice.poll]
            )

    def poll_with_more_votes(self, poll_set=Poll.objects.all()):
        poll = Poll.objects.annotate(s=Sum('choice__votes')).order_by('-s')[0]
        return ("Poll with more votes <small>(%i votes total)</small>"%poll.s, [poll])

    def avg_votes(self):
        a = Choice.objects.aggregate(a=Avg('votes'))['a'] or 0.0
        return ("Average number of votes <small>(all the choices)</small>: %f"%a, [])

    def avg_votes_no_zero(self):
        a = Choice.objects.filter(votes__gt=0).aggregate(a=Avg('votes'))['a'] or 0.0
        return ("Average number of votes <small>(only voted choices)</small>: %f"%a, [])

    def useless(self):
        return ("Polls whose ID is greater (or equal) to the max number of votes in any choice, whose question starts with A and was published since 2012 ", 
                Poll.objects.filter(
                        pk__gte=Choice.objects.aggregate(m=Max('votes'))['m'], 
                        question__startswith='A', 
                        pub_date__gte="2012-01-01"
                    )
            )

    def get_queryset(self):
        t1, voted_polls = self.poll_with_votes()
        qs = []
        if voted_polls:
            qs = [
                    (t1, voted_polls),
                    self.avg_votes(),
                    self.avg_votes_no_zero(),
                    self.most_voted_choice(),
                    self.poll_with_more_votes(poll_set=voted_polls),
                    self.useless(),
                ]
        return qs
        