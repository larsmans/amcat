import dbtoolkit, sys, datetime
import batch, toolkit
import ticker

db = dbtoolkit.anokoDB()

arg = sys.argv[1]
if arg[0] == "s":
    srid = int(arg[1:])
    where = " articleid in (select articleid from storedresults_articles where storedresultid=%i)" % srid
    projectid = db.getValue("select projectid from storedresults where storedresultid=%i" % srid)
else:
    srid = None
    projectid = int(sys.argv[1])
    where = " batchid in (select batchid from batches where projectid=%i)" % projectid

ticker.warn("Querying for duplicate articles")

db.doQuery("create table #tempmax (n int not null, mx int not null)")

N=[3,4,5]

for i in N:
    SQL = """insert into #tempmax
    select %i,  max(articleid) from articles
    where %s
    and articleid not in (select mx from #tempmax)
    group by mediumid, date, section, headline, pagenr
    having count(*) > 2""" % (i, where)
    ticker.warn(SQL)
    db.doQuery(SQL)

cols = ", ".join('a%i' % i for i in N)
SQL = """select t1.a1, t1.a2, %s from (
  select min(articleid) as a1, max(articleid) as a2, count(*) as n from articles
  where %s
  group by mediumid, date, section, headline, pagenr
  having count(*) > 1
) t1""" % (cols, where)

for i in N:
    t = "t%i" % i
    a = "a%i" % i
    SQL += """  left join (
    select min(articleid) as a1, max(articleid) as %(a)s from articles
    where %(where)s
    and articleid not in (select mx from #tempmax where n <= %(i)s)
    group by mediumid, date, section, headline, pagenr
    having count(*) > 1
    ) %(t)s on t1.a1 = %(t)s.a1""" % locals()

ticker.warn("\n\n", SQL)
data = db.doQuery(SQL)

db.doQuery("drop table #tempmax")
db.conn.commit()

if not data:
    ticker.warn("No duplicates found")
    sys.exit()

ticker.warn("%i duplicates found" % len(data))

batchname = "Duplicate articles %s" % (datetime.datetime.now())
batchquery = "Duplicates from %s" % ("Stored Result %i" % srid if srid else "Project %s" % projectid)
b = batch.createBatch(projectid, batchname, batchquery, db)

ticker.warn("Created '%s' for duplicates in %s" % (b.clsidlabel(), b.project.clsidlabel()))

aids = set(toolkit.flatten(data))
aidselection = toolkit.intSelection(db, "articleid", aids)

ticker.warn("Determining use in codingjobs")
ticker.warn(aidselection)
coded = set(db.getColumn("select articleid from codingjobs_articles where %s" % aidselection))
ticker.warn("Determining parsed articles")
parsed = set(db.getColumn("select articleid from parses_words w inner join sentences s on w.sentenceid = s.sentenceid where %s" % aidselection))
ticker.warn("Determining use in stored results")
inset = set(db.getColumn("select articleid from storedresults_articles where %s" % aidselection))

sets = {"Already coded or assigned" : coded, "Parsed or lemmatized" :  parsed, "In a set / Stored Result" : inset}
delete = toolkit.Counter(keys=sets.keys())
prefs = coded, parsed, inset

tomove = set()
             
for articles in data:
    articles = set(articles)

    def preference(article):
        """Give high scores to articles we would like to delete"""
        for i, aset in enumerate(prefs):
            if article in aset:
                return -3+i
        return article
    
    articles = sorted(articles, key=preference)
    for article in articles[1:]:
        for name, sset in sets.items():
            if article in sset: delete.count(name)
        delete.count("Total")
        tomove.add(article)


ticker.warn("Deduplicating %i articles:" % (len(tomove)))
delete.prnt(outfunc=ticker.warn)

SQL = "update articles set batchid=%i where %s" % (b.id, toolkit.intSelection(db, "articleid", tomove))
print SQL

db.doQuery("update articles set batchid=%i where %s" % (b.id, toolkit.intSelection(db, "articleid", tomove)))

ticker.warn("Committing")
db.commit()
ticker.warn("Done!")
