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

"""
Script to be run daily for data input (scraping, preprocessing etc.
"""

from datetime import date, timedelta

import logging;
from amcat.scraping.controller import RobustController

log = logging.getLogger(__name__)

from django import forms

from amcat.scripts.script import Script

from amcat.scraping.controller import scrape_logged
from amcat.models.scraper import get_scrapers
from amcat.models.project import Project    
from amcat.models.articleset import ArticleSet

from amcat.tools import toolkit, sendmail

from amcat.tools.table import table3
from amcat.tools.table.tableoutput import table2html

MAIL_HTML = """<h3>Report for daily scraping on {datestr}</h3>

<p>The following scrapers were run:</p>
{table}

<p>For log details, ssh to amcat-dev.labs.vu.nl, then open /home/amcat/log/daily_{date.year:04d}-{date.month:02d}-{date.day:02d}.txt</p>

<p>For a complete overview of last week's results, navigate to http://www.amcat-production.labs.vu.nl/navigator/scrapers</p>

"""


MAIL_ASCII = MAIL_HTML
for tag in ["h3", "p", "pre"]:
    MAIL_ASCII = MAIL_ASCII.replace("<%s>"%tag, "").replace("</%s>"%tag, "")
    MAIL_ASCII = unicode(MAIL_ASCII)

EMAIL = "amcat-scraping@googlegroups.com"

from amcat.tools.sendmail import sendmail

def make_table(count):
    from amcat.tools.table.table3 import DictTable
    
    table = DictTable()

    for (scraper, n) in count.items():
        try:
            table.addValue(
                row = scraper.__class__.__name__,
                col = scraper.options['date'],
                value = n
                )
        except KeyError:
            pass

    return table


def send_email(count, messages, date):
    
    table = make_table(count).output(rownames = True)

    n = sum(count.values())
    succesful = len([1 for (s,n2) in count.items() if n2>0])
    total = len(count.items())

    datestr = toolkit.writeDate(date.today())

    subject = "Daily scraping for {datestr}: {n} articles, {succesful} out of {total} scrapers succesful".format(**locals())
    
    content = MAIL_ASCII.format(**locals())

    sendmail("toon.alfrink@gmail.com", EMAIL, subject, None, content)


class DailyForm(forms.Form):
    date = forms.DateField()
    deduplicate = forms.BooleanField(required = False)

class DailyScript(Script):
    options_form = DailyForm

    def run(self, _input):
        date = self.options['date']

        scrapers = list(get_scrapers(date = date, ignore_errors = True))
        log.info("Starting scraping with {n} scrapers: {classnames}".format(
                n = len(scrapers),
                classnames = [s.__class__.__name__ for s in scrapers]))



        kwargs = {}
        if self.options['deduplicate']:
            kwargs['deduplicate'] = True

        count, messages, result =  scrape_logged(
            RobustController(), 
            scrapers, 
            **kwargs)


        general_index_articleset = ArticleSet.objects.get(pk = 2)
        #CAUTION: destination articleset is hardcoded

        for (scraper, articles) in result.items():
            if scraper.module().split(".")[-2].lower().strip() == "newspapers":
                log.info("Adding result to general index set ({general_index_articleset})".format(**locals()))
                general_index_articleset.add_articles(articles)

        log.info("Sending email...")
        
        send_email(count, messages, date)

        log.info("Done")

        
def setup_logging():
    from amcat.tools.amcatlogging import AmcatFormatter
    loggers = (logging.getLogger("amcat.scraping"), logging.getLogger("amcat.scripts.maintenance.daily"), logging.getLogger("scraping"))
    d = date.today()
    handlers = (logging.FileHandler("/home/amcat/log/daily_{d.year:04d}-{d.month:02d}-{d.day:02d}.txt".format(**locals())), logging.StreamHandler())
    formatter = AmcatFormatter(date = True)

    for handler in handlers:
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)

    for logger in loggers:
        logger.setLevel(logging.INFO)
        for handler in handlers:        
            logger.addHandler(handler)

if __name__ == '__main__':
    from amcat.scripts.tools import cli
    setup_logging()
    cli.run_cli(DailyScript)
