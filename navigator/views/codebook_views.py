###########################################################################
#          (C) Vrije Universiteit, Amsterdam (the Netherlands)            #
#                                                                         #
# This file is part of AmCAT - The Amsterdam Content Analysis Toolkit     #
#                                                                         #
# AmCAT is free software: you can redistribute it and/or modify it under  #
# the terms of the GNU Affero General Public License as published by the  #
# Free Software Foundation, either version 3 of the License, or (at your  #
# option) any later version.                                              #
#                                                                         #
# AmCAT is distributed in the hope that it will be useful, but WITHOUT    #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or   #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public     #
# License for more details.                                               #
#                                                                         #
# You should have received a copy of the GNU Affero General Public        #
# License along with AmCAT.  If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

from django.core.urlresolvers import reverse
from django.http import HttpResponse

from api.rest.datatable import Datatable
from amcat.scripts.actions.import_codebook import ImportCodebook
from amcat.scripts.actions.export_codebook import ExportCodebook
from amcat.scripts.actions.export_codebook_as_xml import ExportCodebookAsXML
from navigator.views.projectview import ProjectScriptView
from navigator.views.scriptview import TableExportMixin
from api.rest.resources import  CodebookResource 
from navigator.views.datatableview import DatatableMixin
from navigator.views.projectview import ProjectViewMixin, HierarchicalViewMixin, BreadCrumbMixin, ProjectScriptView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView

from amcat.models import Codebook

class ImportCodebook(ProjectScriptView):
    script = ImportCodebook
    def get_success_url(self):
        return reverse("project-codebooks", kwargs=dict(id=self.project.id))

    
class ExportCodebook(TableExportMixin, ProjectScriptView):
    script = ExportCodebook

    def export_filename(self, form):
        c = form.cleaned_data["codebook"]
        return "Codebook {c.id} {c}".format(**locals())
    
    def get_initial(self):
        return dict(codebook=self.url_data["codebookid"])

    def get_form_class(self):
        # Modify form class to also contain XML output
        form_class = super(ExportCodebook, self).get_form_class()
        form_class.base_fields['format'].choices.append(("xml", "XML"))
        return form_class

    def form_valid(self, form):
        if form.cleaned_data['format'] == 'xml':
            return ExportCodebookXML.as_view()(self.request, **self.kwargs)

        return super(ExportCodebook, self).form_valid(form)

class ExportCodebookXML(ProjectScriptView):
    script = ExportCodebookAsXML

    def export_filename(self, form):
        c = form.cleaned_data["codebook"]
        return "Codebook {c.id} {c}.xml".format(**locals())

    def get_initial(self):
        return dict(codebook=self.url_data["codebookid"])

    def form_valid(self, form):
        super(ExportCodebookXML, self).form_valid(form)

        filename = self.export_filename(form)
        response = HttpResponse(self.result, content_type='text/xml', status=200)
        response['Content-Disposition'] = 'attachment; filename="{filename}"'.format(**locals())
        return response




class CodebookListView(HierarchicalViewMixin,ProjectViewMixin, BreadCrumbMixin, ListView):
    model = Codebook
    parent = None
    base_url = "projects/(?P<project_id>[0-9]+)"
    context_category = 'Coding'

    def get_context_data(self, **kwargs):
        ctx = super(CodebookListView, self).get_context_data(**kwargs)
        owned_codebooks = Datatable(CodebookResource, rowlink='./{id}').filter(project=self.project)
        linked_codebooks = (Datatable(CodebookResource, rowlink='./{id}')
                        .filter(projects_set=self.project))
        
        ctx.update(locals())
        return ctx

class CodebookDetailsView(HierarchicalViewMixin,ProjectViewMixin, BreadCrumbMixin, DetailView):
    model = Codebook
    parent = CodebookListView
    context_category='Coding'
    
        
