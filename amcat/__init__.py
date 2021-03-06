"""AmCAT python libraries

Main organisation:
 - L{amcat.ml} contains Machine Learning tools
 - L{amcat.nlp} contains Natural Language Processing tools
 - L{amcat.bin} Executable scripts such as generating the api documentation. 
 - L{amcat.tools} contains a number of auxilliary modules, especially the L{toolkit<amcat.tools.toolkit>} and L{amcat.tools.table.table3}
 - L{amcat.db} contains helper classes for the database
 - L{amcat.models} contains the model layer
 - L{amcat.scripts} Interface and auxilliary modules for plugins. 
"""


# from http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html
from __future__ import absolute_import
from amcat.amcatcelery import app

