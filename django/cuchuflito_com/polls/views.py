# -*- coding: utf-8 -*-
import datetime

from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseNotAllowed, Http404

from django.views.generic import ListView, DetailView, FormView, CreateView
from django.views.generic.dates import ArchiveIndexView, YearArchiveView
from django.db.models import Avg, Max, Count, Sum, Q

from polls.models import Poll, Choice
from polls.forms import VoteForm, NewPollForm, NewChoiceForm

NPOLLSININDEX = 4

class PollsIndex(ListView):
    model = Poll
    #queryset = Poll.objects.order_by('-pub_date')[:NPOLLSININDEX]
    #context_object_name = "latest_poll_list"
    template_name = "polls/index.html"


class PollDetail(DetailView):
    context_object_name = 'poll'
    pk_url_kwarg = 'poll_id'
    #queryset = Poll.objects.all()
    model = Poll
    template_name = "polls/detail.html"

    def get_context_data(self, **kwargs):
        context = super(PollDetail, self).get_context_data(**kwargs)
        context['voting_form'] = VoteForm(poll=self.get_object())
        context['new_choice_form'] = NewChoiceForm()
        return context


class PollVote(FormView):
    template_name = 'polls/detail.html'

    def get_form(self, form_class):
        self.poll = get_object_or_404(Poll, pk=self.kwargs['poll_id'])
        print self.request.POST
        return VoteForm(self.request.POST, poll=self.poll)

    def form_valid(self, form):
        choice = form.cleaned_data['choice']
        choice.votes += 1
        choice.save()
        return redirect('polls:results', poll_id=self.poll.pk)

    def form_invalid(self, form):
        context = {'poll': self.poll, 'voting_form': form, 'new_choice_form': NewChoiceForm()}
        return render(self.request, 'polls/detail.html', context)


class PollResults(DetailView):
    context_object_name = 'poll'
    pk_url_kwarg = 'poll_id'
    model = Poll
    template_name = "polls/results.html"


def _aux_add_choice(request):
    data = {'pub_date':datetime.datetime.now()}
    data['question'] = request.POST.get('question', '')
    the_choices = request.POST.getlist('a_choice', [])
    if request.POST['new_choice']:
        the_choices.append(request.POST['new_choice'])
    data['choices'] = the_choices
    data['new_choice'] = ''
    context = {'form': NewPollForm(data), 'the_choices':the_choices}
    return render(request, 'polls/poll_form.html', context)

def _aux_save_poll(request):
    modified_post = request.POST.copy()
    modified_post['pub_date'] = datetime.datetime.now()
    form = NewPollForm(modified_post)
    the_choices = request.POST.getlist('a_choice', [])
    if form.is_valid():
        poll = Poll(
                question=form.cleaned_data['question'],
                pub_date=form.cleaned_data['pub_date']
                )
        poll.save()
        for c in the_choices:
            poll.choice_set.create(choice=c)
        response = redirect('polls:detail', poll.id)
    else:
        context = {'form': form, 'the_choices':the_choices}
        response =  render(request, 'polls/poll_form.html', context)
    return response

def new_poll(request):
    if request.method == 'POST':
        #form = NewPollForm(request.POST)
        #print request.POST.items()
        if request.POST["save"] == 'Add choice':
            response = _aux_add_choice(request)
        elif request.POST["save"] == 'Save poll':
            response = _aux_save_poll(request)
        else:
            raise Http404("Invalid action.")
    else:
        context = {'form': NewPollForm(), 'the_choices':[]}
        response = render(request, 'polls/poll_form.html', context)

    return response


class ChoiceAdd(CreateView):
    form_class = NewChoiceForm
    model = Choice
    template_name = 'polls:detail'
    pk_url_kwarg = 'poll_id'
    http_method_names = ['post']

    def get_form(self, form_class):
        self.poll = get_object_or_404(Poll, pk=self.kwargs['poll_id'])
        return NewChoiceForm(self.request.POST)

    def form_valid(self, form):
        new_choice = form.cleaned_data['choice']
        self.poll.choice_set.create(choice=new_choice, votes=0)
        return redirect('polls:detail', poll_id=self.poll.id)

    def form_invalid(self, form):
        context = {
                'poll': self.poll, 
                'voting_form': VoteForm(self.request.POST, poll=self.poll), 
                'new_choice_form': NewChoiceForm(self.request.POST)
                }
        return render(self.request, 'polls/detail.html', context)


class PollsArchiveView(ArchiveIndexView):
    queryset = Poll.objects.all()
    date_field = "pub_date"
    allow_future = True
    allow_empty = True
    paginate_by = 10


class PollsYearArchiveView(YearArchiveView):
    queryset = Poll.objects.all()
    date_field = "pub_date"
    make_object_list = True
    allow_future = True
    allow_empty = True
    paginate_by = 10

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
        voted = filter(
                lambda poll: poll.choice_set.aggregate(s=Sum('votes'))['s'] != 0,
                Poll.objects.all()
            )
        return ("Polls with votes", voted)

    def poll_with_no_votes(self):
        no_votes = filter(
                lambda poll: poll.choice_set.aggregate(s=Sum('votes'))['s'] == 0,
                Poll.objects.all()
            )
        return ("Polls with no votes", no_votes)

    def most_voted_choice(self):
        max_votes = Choice.objects.aggregate(m=Max('votes'))['m']
        the_choice = Choice.objects.filter(votes = max_votes)[0]
        return ("Poll with the most voted choice <small>(%s - %i votes)</small>"%(the_choice.choice, max_votes), 
                [the_choice.poll]
            )

    def poll_with_more_votes(self, poll_set=Poll.objects.all()):
        max_votes, poll = max(map(
                lambda poll: (poll.choice_set.aggregate(s=Sum('votes'))['s'], poll),
                    poll_set
            ))
        return ("Poll with more votes <small>(%i votes total)</small>"%max_votes, [poll])

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
                #self.poll_with_no_votes(),
            ]
        

facts = FactsView.as_view()