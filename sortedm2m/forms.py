# -*- coding: utf-8 -*-
from django import VERSION as DJANGO_VERSION
from itertools import chain
from django.forms.util import flatatt
from django.utils.datastructures import MergeDict, MultiValueDict
from re import escape
from django import forms
from django.conf import settings
from django.db.models.query import QuerySet
from django.forms.models import ModelMultipleChoiceField
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


STATIC_URL = getattr(settings, 'STATIC_URL')
if not STATIC_URL:
    STATIC_URL = settings.MEDIA_URL


class SortedFilteredSelectMultiple(forms.SelectMultiple):
    """
    A SortableSelectMultiple with a JavaScript filter interface.
	
	Requires jQuery to be loaded.
	
    Note that the resulting JavaScript assumes that the jsi18n
    catalog has been loaded in the page
    """

    def __init__(self, is_stacked, attrs=None, choices=()):
        self.is_stacked = is_stacked
        super(SortedFilteredSelectMultiple, self).__init__(attrs, choices)

    class Media:
        css = {
            'screen': (STATIC_URL + 'sortedm2m/widget.css',)
        }
        if DJANGO_VERSION[:2] >= (1, 4):
            css['screen'] += (STATIC_URL + 'sortedm2m/widget_14.css',)

        js = (STATIC_URL + 'sortedm2m/OrderedSelectBox.js',
              STATIC_URL + 'admin/js/inlines.js')

        if DJANGO_VERSION[:2] < (1, 4):
            # requires jquery 1.6
            js += (STATIC_URL + 'sortedm2m/OrderedSelectFilter.js',)
        else:
            # requires jquery 1.9
            js += (STATIC_URL + 'sortedm2m/OrderedSelectFilter_14.js',)

    def build_attrs(self, attrs=None, **kwargs):
        attrs = super(SortedFilteredSelectMultiple, self).\
        build_attrs(attrs, **kwargs)
        classes = attrs.setdefault('class', '').split()
        classes.append('sortedm2m')
        if self.is_stacked: classes.append('stacked')
        attrs['class'] = u' '.join(classes)
        return attrs

    def render(self, name, value, attrs=None, choices=()):
        if attrs is None: attrs = {}
        if value is None: value = []
        admin_media_prefix = getattr(settings, 'ADMIN_MEDIA_PREFIX', STATIC_URL + 'admin/')
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<select multiple="multiple"%s>' % flatatt(final_attrs)]
        options = self.render_options(choices, value)
        if options:
            output.append(options)
        output.append(u'</select>')
        output.append(u'<script>addEvent(window, "load", function(e) {')
        output.append(u'OrderedSelectFilter.init("id_%s", "%s", %s, "%s") });</script>\n' %\
                      (name, name.split('-')[-1], int(self.is_stacked), admin_media_prefix))

        prefix_name = name.split('-')[0]
        output.append(u"""
        <script>
            (function($) {
            $(document).ready(function() {
                var rows = "#%s-group .inline-related";
                var updateOrderedSelectFilter = function() {
                    // If any SelectFilter widgets are a part of the new form,
                    // instantiate a new SelectFilter instance for it.
                    if (typeof OrderedSelectFilter != "undefined"){
                        $(".sortedm2m").each(function(index, value){
                            var namearr = value.name.split('-');
                            OrderedSelectFilter.init(value.id, namearr[namearr.length-1], false, "%s");
                        });
                        $(".sortedm2mstacked").each(function(index, value){
                            var namearr = value.name.split('-');
                            OrderedSelectFilter.init(value.id, namearr[namearr.length-1], true, "%s");
                        });
                    }
                }
                $(rows).formset({
                    prefix: "%s",
                    addText: "%s %s",
                    formCssClass: "dynamic-%s",
                    deleteCssClass: "inline-deletelink",
                    deleteText: "Remove",
                    emptyCssClass: "empty-form",
                    added: (function(row) {
                        updateOrderedSelectFilter();
                    })
                });
            });
        })(django.jQuery)
        </script>""" % (
        prefix_name, admin_media_prefix, admin_media_prefix, prefix_name, _('Add another'),
        name.split('-')[-1], prefix_name))

        return mark_safe(u'\n'.join(output))


    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_unicode(option_value)
        selected_html = (option_value in selected_choices) and u' selected="selected"' or ''
        try:
            index = list(selected_choices).index(escape(option_value))
            selected_html = u'%s %s' % (u' data-sort-value="%s"' % index, selected_html)
        except ValueError:
            pass

        return u'<option value="%s"%s>%s</option>' % (
            escape(option_value), selected_html,
            conditional_escape(force_unicode(option_label)))

    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = list(force_unicode(v) for v in selected_choices)
        output = []
        for option_value, option_label in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                output.append(u'<optgroup label="%s">' % escape(force_unicode(option_value)))
                for option in option_label:
                    output.append(self.render_option(selected_choices, *option))
                output.append(u'</optgroup>')
            else:
                output.append(self.render_option(selected_choices, option_value, option_label))
        return u'\n'.join(output)

    def _has_changed(self, initial, data):
        if initial is None:
            initial = []
        if data is None:
            data = []
        initial_list = [force_unicode(value) for value in initial]
        return data != initial_list

class SortedMultipleChoiceField(forms.ModelMultipleChoiceField):
    def __init__(self, queryset, cache_choices=False, required=True,
                 widget=None, label=None, initial=None,
                 help_text=None, *args, **kwargs):
        if not widget:
            widget = SortedFilteredSelectMultiple(
                is_stacked=kwargs.get('is_stacked', False)
            )
        super(ModelMultipleChoiceField, self).__init__(queryset, None,
            cache_choices, required, widget, label, initial, help_text,
            *args, **kwargs)

    def clean(self, value):
        queryset = super(SortedMultipleChoiceField, self).clean(value)
        if value is None or not isinstance(queryset, QuerySet):
            return queryset

        object_list = dict((
            (unicode(key), value)
            for key, value in queryset.in_bulk(value).iteritems()))

        return [object_list[unicode(pk)] for pk in value]
