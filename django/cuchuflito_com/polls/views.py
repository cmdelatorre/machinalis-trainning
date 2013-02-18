# -*- coding: utf-8 -*-
import datetime

from django.shortcuts import get_object_or_404, render, redirect, render_to_response
from django.http import HttpResponseNotAllowed, Http404
from django.template import RequestContext
from django.views.generic import ListView, DetailView, FormView, CreateView
from django.views.generic.dates import ArchiveIndexView, YearArchiveView
from django.db.models import Avg, Max, Count, Sum, Q

from polls.models import Poll, Choice
from polls.forms import VoteForm, PollDetailForm, ChoiceFormSet

NPOLLSININDEX = 4
NPOLLSINPAGE = 10

def new_poll(request):
    if request.method == "GET":
        response = render_to_response(
                "polls/poll_detail.html", 
                {"poll_form":PollDetailForm(), "choices_formset":ChoiceFormSet()},
                RequestContext(request)
            )
    elif request.method == "POST":
        poll_form = PollDetailForm(request.POST)
        choices_formset = ChoiceFormSet(request.POST, request.FILES)
        if poll_form.is_valid() and choices_formset.is_valid():
            poll = poll_form.save()
            ChoiceFormSet(request.POST, request.FILES, instance=poll).save()
            response = redirect('polls:voting', poll_id=poll.pk)
        else:
            response = render_to_response(
                "polls/poll_detail.html", 
                {"poll_form":poll_form, "choices_formset":choices_formset},
                RequestContext(request)
                )
    return response

def edit_poll(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)

    if request.method == "POST":
        poll_form = PollDetailForm(request.POST, instance=poll)
        choices_formset = ChoiceFormSet(request.POST, request.FILES, instance=poll)

        if poll_form.is_valid() and choices_formset.is_valid():
            poll_form.save()
            choices_formset.save()
            return redirect('polls:voting', poll_id=poll.pk)
        else:
            context = {
                    "poll_form" : poll_form,
                    "choices_formset" : choices_formset,
                }
    else:
        context = {
                "poll_form" : PollDetailForm(instance=poll),
                "choices_formset" : ChoiceFormSet(instance=poll),
            }

    return render_to_response(
            "polls/poll_detail.html", 
            context, 
            RequestContext(request)
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
        choice.votes += 1
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
        a = Choice.objects.aggregate(a=Avg('votes'))['a']
        return ("Average number of votes <small>(all the choices)</small>: %f"%a, [])

    def avg_votes_no_zero(self):
        a = Choice.objects.filter(votes__gt=0).aggregate(a=Avg('votes'))['a']
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
        return [
                (t1, voted_polls),
                self.avg_votes(),
                self.avg_votes_no_zero(),
                self.most_voted_choice(),
                self.poll_with_more_votes(poll_set=voted_polls),
                self.useless(),
            ]
        

facts = FactsView.as_view()