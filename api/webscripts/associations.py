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

from webscript import WebScript

from amcat.scripts.searchscripts.articlelist import ArticleListScript
from amcat.scripts.processors.associations import AssociationsScript
from django import forms
from amcat.tools.table import table3
from amcat.tools import dot, keywordsearch, amcates
import re
import logging
log = logging.getLogger(__name__)

FORMATS = [
    ("0.12", False, "%1.2f"),
    ("0.123", False, "%1.3f"),
    ("12%", True, "%1.0f%%"),
    ("12.3%", True, "%1.1f%%"),
    ]

class AssociationsForm(forms.Form):
    network_output = forms.ChoiceField(choices=[('oo', 'Table'),
                                        ('ool', 'List'),
                                        ('oon', 'Network graph'),
                                        ])

    association_format = forms.ChoiceField(label="Number Format", choices = ((i, x[0]) for (i,x) in enumerate(FORMATS)), initial=0)
    
    graph_threshold = forms.DecimalField(label="Graph: threshold", required=False)
    graph_label = forms.BooleanField(label="Graph: include association in label", required=False)

    
    
class ShowAssociations(WebScript):
    name = "Associations"
    form_template = None
    form = AssociationsForm
    output_template = None
    solrOnly = True
    displayLocation = ('ShowSummary','ShowArticleList')


    def format(self, a):
        name, perc, formatstr = FORMATS[int(self.options["association_format"])]
        if a:
            if perc: a*=100
            return formatstr % (a,)
    
    def run(self):
        es = amcates.ES()
        filters = dict(keywordsearch.filters_from_form(self.data))
        queries = list(keywordsearch.queries_from_form(self.data))
        qargs = dict(filters=filters, score=True, fields=[])
        probs = {}
        
        p = lambda f: 1 - (.5 ** f)
        probs = {q.label : {r.id : p(r.score) for r in
                            es.query_all(query=q.query, **qargs)}
                 for q in queries}
            
        assocTable = table3.ListTable(colnames=["From", "To", "Association"])
        for q in probs:
            sumprob1 = float(sum(probs[q].values()))
            if sumprob1 == 0: continue
            for q2 in probs:
                if q == q2: continue
                sumproduct = 0
                for id, p1 in probs[q].iteritems():
                    p2 = probs[q2].get(id)
                    if not p2: continue
                    sumproduct += p1*p2
                p = sumproduct / sumprob1
                assocTable.addRow(q, q2, p)

        if self.options['network_output'] == 'ool':
            self.output = 'json-html'
            assocTable = table3.WrappedTable(assocTable, cellfunc = lambda a: self.format(a) if isinstance(a, float) else a)
            
            return self.outputResponse(assocTable, AssociationsScript.output_type)
        elif self.options['network_output'] == 'oo':
            # convert list to dict and make into dict table
            result = table3.DictTable()
            result.rowNamesRequired=True
            for x,y,a in assocTable:
                result.addValue(x,y,self.format(a))
            self.output = 'json-html'
            return self.outputResponse(result, AssociationsScript.output_type)
        elif self.options['network_output'] == 'oon':
            g = dot.Graph()
            threshold = self.options.get('graph_threshold')
            if not threshold: threshold = 0
            nodes = {}
            def getnode(x):
                if not x in nodes: 
                    id = "node_%i_%s" % (len(nodes), re.sub("\W","",x))
                    nodes[x] = dot.Node(id, x)
                return nodes[x]
                
            for x,y,a in assocTable:
                if threshold and a < threshold:
                    continue

                opts = {}
                if self.options['graph_label']: opts['label'] = self.format(a)
                w = 1 + 10 * a

                g.addEdge(getnode(x),getnode(y), weight=w, **opts)
            html = g.getHTMLObject()
            self.output = 'json-html'
            return self.outputResponse(html, unicode)
            
            
