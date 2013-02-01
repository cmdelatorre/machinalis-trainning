from django.shortcuts import get_object_or_404, render, redirect

from django.views.generic import ListView, DetailView, FormView, CreateView

from polls.models import Poll, Choice
from polls.forms import VoteForm, NewChoiceForm

class PollsIndex(ListView):
    #model = Poll # Muestra TODAS las Polls
    queryset = Poll.objects.order_by('-pub_date')[:5]
    context_object_name = "latest_poll_list"
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
    form_class = VoteForm
    template_name = 'polls/detail.html'

    def post(self, request, *args, **kwargs):
        self.poll = get_object_or_404(Poll, pk=self.kwargs['poll_id'])
        form = VoteForm(request.POST, poll=self.poll)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        choice = form.cleaned_data['choice']
        choice.votes += 1
        choice.save()
        return redirect('polls:results', poll_id=self.poll.pk)

    def form_invalid(self, form):
        context = {'poll': self.poll, 'voting_form': form}
        return render(self.request, 'polls/detail.html', context)


class PollResults(DetailView):
    context_object_name = 'poll'
    pk_url_kwarg = 'poll_id'
    model = Poll
    template_name = "polls/results.html"


# def add_choice(request, poll_id):
#     if request.method != 'POST':
#         return HttpResponseNotAllowed(['POST'])
#     poll = get_object_or_404(Poll, pk=poll_id)
#     new_choice_form = NewChoiceForm(request.POST)
#     if new_choice_form.is_valid():
#         new_choice = new_choice_form.cleaned_data['choice']
#         poll.choice_set.create(choice=new_choice, votes=0)
#         return redirect('polls:detail', poll_id=poll.id)
#     else:
#         context = {
#                 'poll': poll, 
#                 'voting_form': VoteForm(request.POST, poll=poll), 
#                 'new_choice_form': new_choice_form
#                 }
#         return render(request, 'polls/detail.html', context)
class ChoiceAdd(CreateView):
    form_class = NewChoiceForm
    model = Choice
    template_name = 'polls:detail'
    pk_url_kwarg = 'poll_id'

    def form_valid(self, form):
        new_choice = form.cleaned_data['choice']
        poll = self.get_object().poll # Acá no anda... algo estoy haciendo mal...
        poll.choice_set.create(choice=new_choice, votes=0)
        print poll
        return redirect('polls:detail', poll_id=poll.pk)

    def form_invalid(self, form):
        poll = self.get_object().poll
        context = {
                'poll': poll, 
                'voting_form': VoteForm(self.request.POST, poll=poll), 
                'new_choice_form': NewChoiceForm(self.request.POST)
                }
        return render(self.request, 'polls/detail.html', context)