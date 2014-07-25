erd-server
==========

A ERD server for [2014 Entity Recognition and Disambiguation Challenge](http://web-ngram.research.microsoft.com/erd2014).

This package contains the source code for the Long Track as described in:

Yen-Pin Chiu, Yong-Siang Shih, Yang-Yin Lee, Chih-Chieh Shao, Ming-Lun Cai, Sheng-Lun Wei and Hsin-Hsi Chen. *NTUNLP Approaches to Recognizing and Disambiguating Entities in Long and Short Text in the 2014 ERD Challenge*

The program itself is developed by Yong-Siang Shih.

## Installation

### Process Data

#### Extract Freebase Alias

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
# download redirect extractor
wget https://wikipedia-redirect.googlecode.com/files/wikipedia_redirect-1.0.0.zip

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

#### Construct Mapping between Freebase IDs and Wikipedia/Dbpedia IDs

#### Construct the Stop List

### Obtain and Set the API Keys

Create an `api_key.py` file with the following content to use Freebase/TAGME API:

```python
API_KEY = '{your Freebase API key here}'
TAGME_API_KEY = '{your TAGME API key here}'
```

## License

To be determined.
