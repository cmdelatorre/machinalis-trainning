# -*- coding: utf-8 -*-
from polls.models import Poll, Choice
from datetime import datetime, timedelta
import codecs
from django.utils import timezone


questions = codecs.open('polls/fixtures/questions.txt', "r", "utf-8").readlines()
YEARS = xrange(2011, 2013)
DAYS_SKIP = 1
STEP = 50 # Cada cuantas preguntas cambia el año.

timezone = timezone.get_default_timezone()

y = 2011
a_date = datetime(y,06,01, 9, 45, 25, tzinfo=timezone)
i = 0
for q in questions:
    q = unicode(q)
    p = Poll(
            question=u"%s_%03i_%i"%(q.strip(), y ,i), 
            pub_date=a_date+timedelta(i*DAYS_SKIP)
        )
    i += 1
    p.save()
    p.choice_set.create(choice="Yes")
    p.choice_set.create(choice="No")
    p.choice_set.create(choice="WTF?")
    if i%STEP == 0:
        print "Inserted %i questions for year %i"%(i, y)
        y += 1
        a_date = datetime(y,06,01, 9, 45, 25, tzinfo=timezone)
        i = 0
