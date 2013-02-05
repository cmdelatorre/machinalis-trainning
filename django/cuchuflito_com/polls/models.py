import datetime
from django.db import models
from django.utils import timezone
from django.core.urlresolvers import reverse

class Poll(models.Model):
	"""A poll about cuchuflitos."""
	question = models.CharField(max_length=200)
	pub_date = models.DateTimeField("date published", default=datetime.datetime.now())

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


class Choice(models.Model):
	poll = models.ForeignKey(Poll) 
	choice = models.CharField(max_length=200) 
	votes = models.PositiveIntegerField(default=0)

	def __unicode__(self):
		return self.choice