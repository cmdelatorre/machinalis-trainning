import datetime

from django import forms

from polls.models import Poll, Choice

class VoteForm(forms.Form):
    choice = forms.ModelChoiceField(
            queryset=Choice.objects.all(),
            widget=forms.RadioSelect,
            empty_label=None,
            )

    def __init__(self, *args, **kwargs):
        poll = kwargs.pop('poll')
        super(VoteForm, self).__init__(*args, **kwargs)
        self.fields['choice'].queryset = poll.choice_set.all()


class NewPollForm(forms.Form):
    question = forms.CharField(max_length=200)
    pub_date = forms.DateTimeField(label='date published', initial=datetime.datetime.now())
    new_choice = forms.CharField(max_length=200, required=False, help_text='A new choice for this poll. 200 characters max.')
    choices = []


class NewChoiceForm(forms.ModelForm):
    choice = forms.CharField(label="new choice", max_length=200)

    class Meta:
        model = Choice
        fields = ('choice',)

