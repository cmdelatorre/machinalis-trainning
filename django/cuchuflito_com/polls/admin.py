from polls.models import Poll, Choice
from django.contrib import admin

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2

class PollAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['question','created_by']}),
        ('Date information', {'fields': ['pub_date'], 'classes': ['collapse']}),
    ]
    inlines = [ChoiceInline]
    list_display = ('question', 'pub_date', 'created_by', 'was_published_recently')
    list_filter = ['pub_date', 'created_by']
    search_fields = ['question']
    date_hierarchy = 'pub_date'
	# Default
	# actions_on_top= False
	# actions_on_bottom = False

admin.site.register(Poll, PollAdmin)