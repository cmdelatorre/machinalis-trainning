# -*- coding: utf-8 -*-
from datetime import datetime

from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseNotAllowed, Http404

from django.views.generic import ListView, DetailView, FormView, CreateView
from django.views.generic.dates import ArchiveIndexView, YearArchiveView

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


def new_poll(request):
    the_choices = []
    if request.method == 'POST':
        form = NewPollForm(request.POST)
        print request.POST.items()
        if request.POST["save"] == 'Add choice':
            data = {}
            for f in ['question', 'pub_date']:
                data[f] = request.POST.get(f, '')
            the_choices = request.POST.getlist('a_choice', [])
            if request.POST['new_choice']:
                the_choices.append(request.POST['new_choice'])
            data['choices'] = the_choices
            data['new_choice'] = ''
            form = NewPollForm(data)
        elif request.POST["save"] == 'Save poll':
            if form.is_valid():
                poll = Poll(
                        question=form.cleaned_data['question'],
                        pub_date=form.cleaned_data['pub_date']
                        )
                poll.save()
                for c in request.POST.getlist('a_choice', []):
                    poll.choice_set.create(choice=c)
                form.choices = []
                return redirect('polls:detail', poll.id)
            else:
                print "Dice que no vale"
        else:
            return Http404()
    else:
        form = NewPollForm()
        form.choices = []
    context = {'form': form, 'the_choices':the_choices}
    return render(request, 'polls/poll_form.html', context)

# class NewPoll(CreateView):
#     form_class = NewPollForm
#     model = Poll
#     http_method_names = ['post', 'get']

#     def get_form(self, form_class):
#         return NewPollForm(self.request.POST)

#     def form_valid(self, form):
#         return Http404()

#     def form_invalid(self, form):
#         return Http404


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