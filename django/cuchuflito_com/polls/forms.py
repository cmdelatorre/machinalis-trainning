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


class NewPollForm(forms.ModelForm):
    class Meta:
        model = Poll


class NewChoiceForm(forms.ModelForm):
    choice = forms.CharField(label="new choice", max_length=200)

    class Meta:
        model = Choice
        fields = ('choice',)

