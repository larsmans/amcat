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

from amcat.models.scraper import Scraper
from amcat.models.article import Article
from amcat.models.medium import Medium

from django.db.models import Count
from datetime import date, timedelta
import logging; log = logging.getLogger(__name__)
import json

def scraper_ranges(scraper):
    ranges = [(0,0) for x in range(7)]

    medium = Medium.get_or_create(scraper.get_scraper_class().medium_name)
    print("getting n_scraped...")
    n_scraped = scraper.n_scraped_articles(from_date = date.today() - timedelta(days = 365),
                                           to_date = date.today(),
                                           medium = medium)
    
    if len(n_scraped) < 21:
        raise ValueError("not enough data on the scraper")
    
    for wkday, numbers in enumerate(sort_weekdays(n_scraped)):
        med = median(numbers)
        ranges[wkday] = (med/1.5, med*1.5)
        
    #if a scraper isn't always guaranteed to return anything, the lower range is set to 0
    for r in ranges:
        if r[0] < 1:
            r = (0, r[1])

    return ranges

def sort_weekdays(rows):
    days = [[] for L in range(7)]
    for date, count in rows.items():
        wkday = date.weekday()
        days[wkday].append(count)        
    return days
        
def median(numbers):
    numbers = sorted(numbers)
    L = len(numbers)
    if L == 0:
        return 0
    elif L == 1:
        return numbers[0]
    else:
        pointer = int(L*(2.0/4.0))
        return numbers[pointer]

def set_scraper_stats():
    print("starting...")
    for scraper in Scraper.objects.filter(active = True):
        print(scraper.label)
        try:
            ranges = scraper_ranges(scraper)
        except ValueError:
            continue
        scraper.statistics = ranges
        log.info("{scraper}: {scraper.statistics}".format(**locals()))
        scraper.save()



if __name__ == '__main__':
    from amcat.tools import amcatlogging
    amcatlogging.info_module("amcat.scripts.maintenance.set_scraper_stats")
    set_scraper_stats()
        

    
        
        
