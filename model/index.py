from amcat.model.article import Article
from amcat.model.set import Set

from django.db import models

class Index(models.Model):
    id = models.IntegerField(db_column='indexid', primary_key=True)

    name = models.CharField(max_length=100)
    status = models.IntegerField()

    started = models.BooleanField(default=False)
    done = models.BooleanField(default=False)
    directory = models.CharField(max_length=500)
    options = models.CharField(max_length=50)

    set = models.ForeignKey(Set, db_column='storedresultid')

    def __unicode__(self):
        return self.name

    class Meta():
        db_table = 'indices'

    #def query(self, terms, **options):
    #    """Executes the query on the index and yields articles"""
    #    if type(terms) in (str, unicode): terms = [terms]
    #    aidsDict, time, hits = lucenelib.search(self.directory, list(enumerate(terms)), db=self.db, **options)
    #    for id, dict in aidsDict.iteritems():
    #        for aid in dict.keys():
    #            yield article.Article(self.db, aid)


        
        
