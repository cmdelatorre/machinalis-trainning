# -*- coding: utf-8 -*-
from datetime import datetime

from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseNotAllowed

from django.views.generic import ListView, DetailView, FormView, CreateView
from django.views.generic.dates import ArchiveIndexView, YearArchiveView

from polls.models import Poll, Choice
from polls.forms import VoteForm, NewChoiceForm

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


class ChoiceAdd(CreateView):
    form_class = NewChoiceForm
    model = Choice
    template_name = 'polls:detail'
    pk_url_kwarg = 'poll_id'

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


class PollsYearArchiveView(YearArchiveView):
    queryset = Poll.objects.all()
    date_field = "pub_date"
    make_object_list = True
    allow_future = True
    allow_empty = True
    paginate_by = 10


class PollsArchiveView(ArchiveIndexView):
    queryset = Poll.objects.all()
    date_field = "pub_date"
    allow_future = True
    allow_empty = True
    paginate_by = 10

