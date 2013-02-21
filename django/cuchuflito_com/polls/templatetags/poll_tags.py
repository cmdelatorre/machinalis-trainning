from django import template

register = template.Library()

progress_bar = "<div class='progress %s'> <div class='bar' style='width: %i%%;'></div> </div>"

HIGH = "progress-danger"
MEDIUM = "progress-warning"
LOW = "progress-info"

@register.simple_tag
def barrita(choice, **kwargs):
    max_votes = choice.poll.get_max_votes()
    percent = 0.0
    importance = LOW
    if max_votes != 0:
        percent = choice.votes * 100.0 / max_votes

    if percent >= 66:
        importance = HIGH
    elif percent < 66 and percent >= 30:
        importance = MEDIUM

    return progress_bar%(importance, int(percent))




from django.core.urlresolvers import reverse

@register.simple_tag
def edit_link_if_autorized(user, poll, **kwargs):
    link_template = """<p>
        <a href="%(link)s" title="%(title)s"> 
            %(question)s
        </a><br/>
    </p>"""
    link = "#"
    title = ""
    if poll.created_by == user:
        link = reverse('polls:edit_poll', kwargs={'poll_id':poll.id}) #"{%% url 'polls:edit_poll' poll_id=%i %%}"%poll.id,
        title = "Click to edit the poll"

    return link_template%{
            'link':link, 
            'title':title, 
            'question':poll.question
        }
