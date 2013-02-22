import datetime
from django.db import models
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.db.models import Max, F
from django.contrib.auth.models import User


class Poll(models.Model):
    """A poll about cuchuflitos."""
    question = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published", default=timezone.now)
    created_by = models.ForeignKey(User)

    class Meta:
        ordering = ['-pub_date']
        #order_with_respect_to = 'created_by'
        permissions = (('can_view_stats', 'Can view the statistics?'),)

    def was_published_recently(self):
        """Return true if the poll was created from yesterday, afterwards."""
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)
    was_published_recently.admin_order_field = 'pub_date'
    was_published_recently.boolean = True
    was_published_recently.short_description = 'Is it recent?'

    def __unicode__(self):
        return self.question

    def get_absolute_url(self):
        return reverse('polls:detail', kwargs={'poll_id': self.id})

    def get_max_votes(self):
        """Return the number of votes of the most voted choice."""
        return self.choice_set.aggregate(max=Max('votes'))['max'] or 0

    def has_winners(self):
        """Return the choices with more votes than the rest."""
        voted_choices = self.choice_set.filter(votes__gt=0).order_by('-votes')
        M = voted_choices.aggregate(max=Max('votes'))['max']
        return voted_choices.filter(votes=M)

    def get_ordered_choices(self):
        """Most voted choices, first."""
        return self.choice_set.order_by('-votes')

class Choice(models.Model):
    poll = models.ForeignKey(Poll) 
    choice = models.CharField(max_length=200) 
    votes = models.PositiveIntegerField(default=0)

    class Meta:
        order_with_respect_to = 'poll'
        unique_together = [("poll", "choice")]
        ordering = ['order',]

    def __unicode__(self):
        return self.choice

    def vote_me(self):
        """Increment in 1 the votes for this choice, and save."""
        self.votes += 1
        self.save()

