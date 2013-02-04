from polls.models import Poll, Choice
from datetime import datetime, timedelta
import codecs
from django.utils import timezone


questions = codecs.open('polls/fixtures/questions.txt', "r", "utf-8").readlines()
YEARS = xrange(2009, 2014)
DAYS_SKIP = 1


for y in YEARS:
    a_date = datetime(y,06,01, 9, 45, 25, tzinfo=timezone.get_default_timezone()) #Ojo con el tz, not tested
    i = 0
    for q in questions:
        i += 1
        q = unicode(q)
        #p = Poll(question=u"%i_%03i_%s"%(y, i, q.strip()), pub_date=a_date+timedelta(i*DAYS_SKIP))
        print a_date+timedelta(i*DAYS_SKIP)
        p.save()
        p.choice_set.create(choice="Yes")
        p.choice_set.create(choice="No")
        p.choice_set.create(choice="WTF?")
    print "Inserted %i questions for year %i"%(i, y)

