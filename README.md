erd-server
==========

A ERD server for [2014 Entity Recognition and Disambiguation Challenge](http://web-ngram.research.microsoft.com/erd2014).

This package contains the source code for the Long Track as described in:

Yen-Pin Chiu, Yong-Siang Shih, Yang-Yin Lee, Chih-Chieh Shao, Ming-Lun Cai, Sheng-Lun Wei and Hsin-Hsi Chen. *NTUNLP Approaches to Recognizing and Disambiguating Entities in Long and Short Text in the 2014 ERD Challenge*

The program itself is developed by Yong-Siang Shih. I intend to continue to maintain and develop the package as the current codebase is a bit ugly. The orginal version is available on the `original` branch.


## Installation

### Process Data

Firstly, download the [ERD2014 Datasets](http://web-ngram.research.microsoft.com/erd2014/Datasets.aspx): `entity.tsv`, which contains the entities to be reconginzed in this task.

#### Extract Freebase Alias

Download [Freebase Data Dumps](https://developers.google.com/freebase/data), and extract alias for all entities in the `entity.tsv` dataset.

```sh
# extract all alias
zgrep 'common\.topic\.alias' freebase-rdf-2014-03-23-00-00.gz | gzip > freebase-filtered.gz

# strip unwanted texts
zcat freebase-filtered.gz | sed -e 's/<http:\/\/rdf.freebase.com\/ns\///g' -e 's/^m\./\/m\//' -e 's/>\s*common\.topic\.alias>//' -e 's/\s*\.$//' | gzip > freebase-stripped.gz

# get all entity mids
cut -d $'\t' -f1 entity.tsv | sort -k 1b,1  > sort_mid.tsv

# get entity alias from entity.tsv
cut -d $'\t' -f1,2 entity.tsv > freebase.tsv

# get entity alias from freebase-stripped.gz
zgrep '^/m/' freebase-stripped.gz >> freebase.tsv

# sort the alias
sort freebase.tsv | uniq | sort -k 1b,1 > sort_freebase.tsv

# produce join result
join -t $'\t' sort_mid.tsv sort_freebase.tsv > join_freebase.tsv

# filter out non-en entries
grep '@en' join_freebase.tsv | sort | uniq | sort -k 1b,1 > join_freebase_en.tsv
```

#### Extract Wikipedia Redirects

To extract Wikipedia Redirects, download the [Wikipedia Data Dump](http://dumps.wikimedia.org/enwiki/20140304/): `enwiki-20140304-pages-articles.xml.bz2`. Use the following two Python 2 scripts, and [Wikipedia Redirect](https://code.google.com/p/wikipedia-redirect/) package to process the data.

```python
## -- html.py -- ##
import fileinput
for line in fileinput.input():
  print HTMLParser.HTMLParser().unescape(line.decode('utf8')).encode('utf8 '),
## -- ##
```

```python
## -- convert.py -- ##
import re
import fileinput

def rep(s):
return unichr(int(s.group(1), 16))

for line in fileinput.input():
  content = re.sub(r'\$([0-9A-Fa-f]{4})', rep, line.decode('utf8'))
  print content.encode('utf8'),
## -- ##
```

```sh

# decompress dump
bunzip2 enwiki-20140304-pages-articles.xml.bz2

# decompress extractor
unzip wikipedia_redirect-1.0.0.zip

# extract it
java -cp wikipedia_redirect/wikipedia_redirect.jar edu.cmu.lti.wikipedia_redirect.WikipediaRedirectExtractor enwiki-20140304-pages-articles.xml

# convert syntax
cat target/wikipedia_redirect.txt | python html.py | awk -F'\t' -v OFS='\t' '{ print $2, $1 }'| sort -t$'\t' -k 1,1 > sort_redirect.tsv

# produce wikipedia title -> freebase id mapping
cut -d $'\t' -f1,3 entity.tsv | sed -e 's/"\/wikipedia\/en_title\///g' -e 's/"\r$//' | awk -F'\t' -v OFS='\t' '{ gsub(/_/, " ", $2); print $2, $1 }' | python convert.py | sort -t$'\t' -k 1,1 > sort_m_wiki.tsv

# produce join file
join -t $'\t' sort_redirect.tsv sort_m_wiki.tsv | cut -d $'\t' -f2,3 |  awk -F'\t' -v OFS='\t' '{ print $2, "\"" $1 "\"@en" }' > join_redirect.tsv

# merge result with previous work
cat join_redirect.tsv join_freebase_en.tsv | sort | uniq | sort -k 1b,1 > join_2nd.tsv
```

#### Construct SQLite Database


```sh
# construct initial database
python3 tools/db.py entity.tsv erd2014.db

# insert dictionary
python3 tools/jdict.py join_2nd.tsv erd2014.db

```

#### Construct Mapping between Freebase IDs and Wikipedia/Dbpedia IDs

Both [TAGME API](http://tagme.di.unipi.it/) and [DBPedia Spotlight API](http://spotlight.dbpedia.org) use different IDs to identiy the entities. Therefore, we need to create a mapping between these IDs to the Freebase IDs. As we are using live APIs, it's best to download the current data dumps to create the maping.

1. [Wikipedia Data Dump](http://dumps.wikimedia.org/enwiki/latest/): `enwiki-latest-page.sql.gz`
2. [DBPedia Data Dump](http://downloads.dbpedia.org/current/en/): `freebase_links_en.nt.bz2`

```sh
# decompress dumps
bunzip2 freebase_links_en.nt.bz2
gzip -d enwiki-latest-page.sql.gz

# create wikipedia -> freebase mapping
python3 tools/page-id.py entity.tsv enwiki-latest-page.sql page_id_map

# create dbpedia -> freebase mapping
python3 tools/dbpedia-id.py entity.tsv freebase_links_en.nt dbp_id_map
```

#### Construct the Stop List

Create an `stop_list` file. Each line is a stop word.

### Obtain and Set the API Keys

Create an `api_key.py` file with the following content to use Freebase/TAGME API:

```python
API_KEY = '{your Freebase API key here}'
TAGME_API_KEY = '{your TAGME API key here}'
```

You can obtain the keys by following the instructions on [Freebase](https://developers.google.com/freebase/) and [TAGME](http://tagme.di.unipi.it/) websites.


### Install Requirements

- Python 2 for tools
- Python 3.4 for tools and the server
- Flask for Python3
- SQLite for Python 3
- Requests for Python 3

## Execute the Server

`python3 server.py -l erd2014.db -t page_id_map -d dbp_id_map`

Notice that the server may take as much as 6GB of memory to run.

## License

Released under the GPLv3 License.  See the [LICENSE][license] file for further details.

[license]: https://github.com/shaform/erd-server/blob/master/LICENSE
