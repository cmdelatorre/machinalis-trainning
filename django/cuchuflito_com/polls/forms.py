import datetime

from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.forms.extras.widgets import SelectDateWidget
from django.forms.models import BaseInlineFormSet, inlineformset_factory

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


class PollDetailForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = ('question',)

    question = forms.CharField(
            max_length=200,
            error_messages={'required': u"Question can't be empty."}
        )


def validate_empty(value):
    if len(value) == 0 or len(value.strip()) == 0:
        raise ValidationError(u'Empty value')

class InlineChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ('choice',)

    choice = forms.CharField(
            validators = [validate_empty],
            error_messages = {
                    'invalid': u'Enter a non-empty choice.',
                    'required': u'This choice is required.',
                    '__all__': u"Repeated choice."},
            max_length = 200,
        )

    def clean_choice(self):
        return self.cleaned_data['choice'].strip()


class BaseChoiceFormSet(BaseInlineFormSet):
    def add_fields(self, form, index):
        """Add the ORDER field in a hidden widget."""
        super(BaseChoiceFormSet, self).add_fields(form, index)
        form.fields['ORDER'] = forms.IntegerField(label=(u'Order'), initial=index+1, required=False)
        form.fields['ORDER'].widget = forms.HiddenInput()

    def save(self, commit=True):
        super(BaseChoiceFormSet, self).save(commit=commit)
        for form in self.ordered_forms:
            choice = form.cleaned_data['id']
            if choice:
                choice._order = form.cleaned_data['ORDER']
                choice.save()


ChoiceFormSet = inlineformset_factory(
        Poll, 
        Choice,
        form=InlineChoiceForm,
        formset=BaseChoiceFormSet,
        extra=1,
        can_order=True, 
        can_delete=True,
        )
