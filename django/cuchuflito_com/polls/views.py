from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render, redirect

from polls.models import Poll, Choice
from polls.forms import VoteForm, NewChoiceForm

def index(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'], "perro")

    latest_polls = Poll.objects.order_by('-pub_date')[:5]
    context = {'latest_poll_list': latest_polls}
    return render(request, 'polls/index.html', context)


def detail(request, poll_id):
    voting_form = None
    poll = get_object_or_404(Poll, pk=poll_id)
    context = {
        'poll': poll, 
        'voting_form': VoteForm(request.POST, poll=poll), 
        'new_choice_form': NewChoiceForm()
        }
    return render(request, 'polls/detail.html', context)


def vote(request, poll_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    poll = get_object_or_404(Poll, pk=poll_id)
    form = VoteForm(request.POST, poll=poll)
    if form.is_valid():
        choice = form.cleaned_data['choice']
        choice.votes += 1
        choice.save()
        return redirect('polls:results', poll_id=poll.id)
    else:
        print "Falla", form
        return render(request, 'polls/detail.html', {'poll': poll, 'voting_form': form})


def results(request, poll_id):
    response = None
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    poll = get_object_or_404(Poll, pk=poll_id)
    choices = poll.choice_set.all()
    context = {'poll':poll, 'choices':choices}
    return render(request, 'polls/results.html', context)


def add_choice(request, poll_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    poll = get_object_or_404(Poll, pk=poll_id)
    new_choice_form = NewChoiceForm(request.POST)
    if new_choice_form.is_valid():
        new_choice = new_choice_form.cleaned_data['choice']
        poll.choice_set.create(choice=new_choice, votes=0)
        return redirect('polls:detail', poll_id=poll.id)
    else:
        context = {
                'poll': poll, 
                'voting_form': VoteForm(request.POST, poll=poll), 
                'new_choice_form': new_choice_form
                }
        return render(request, 'polls/detail.html', context)
