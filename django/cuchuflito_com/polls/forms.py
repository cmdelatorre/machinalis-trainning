import datetime

from django import forms
from django.forms.extras.widgets import SelectDateWidget

from polls.models import Poll, Choice

class VoteForm(forms.Form):
    choice = forms.ModelChoiceField(
            queryset=Choice.objects.all(),
            widget=forms.RadioSelect,
            empty_label=None,
            error_messages={'required': u"You must select a choice to vote."}
            )

    def __init__(self, *args, **kwargs):
        poll = kwargs.pop('poll')
        super(VoteForm, self).__init__(*args, **kwargs)
        self.fields['choice'].queryset = poll.choice_set.all()


class NewPollForm(forms.Form):
    question = forms.CharField(
            max_length=200, 
            error_messages={'required': u"Question can't be empty."}
        )
    pub_date = forms.DateTimeField(
            label='date published', 
            initial=datetime.datetime.now,
            widget=forms.HiddenInput,
        )
    new_choice = forms.CharField(
            max_length=200, 
            required=False, 
            help_text='A new choice for this poll. 200 characters max.',
            error_messages={'required': u"New choice can't be empty."}
        )
    #initial={'pub_date': datetime.datetime.now}


class NewChoiceForm(forms.ModelForm):
    choice = forms.CharField(
            label="new choice", 
            max_length=200,
            widget=forms.TextInput(attrs={'class':'span4'}),
            error_messages={'required': u"New choice can't be empty."},
        )

    class Meta:
        model = Choice
        fields = ('choice',)

