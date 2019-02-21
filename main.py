import datetime
import json
import sys
import traceback
from html.parser import HTMLParser

GBOOKMARK_XML = 'GoogleBookmarks.html'
INTERMEDIATE_JSON = 'intermediate.json'
RAINDROP_XML = 'Raindrop-out.html'
RAINDROP_COLLECTION_NAME = 'main'

class LinkItem(object):
    def __init__(self):
        self.title = None
        self.href = None
        self.createDate = None
        self.tags = []

    def addTag(self, tag):
        if self.tags is None:
            self.tags = [tag]
        elif tag not in self.tags:
            self.tags.append(tag)

    def __str__(self):
        return ('LinkItem(title={t}, href={h}, date={d}, tags={ts})'
                .format(t=self.title, h=self.href,
                        d=self.createDate, ts=self.tags))

    def toJSON(self):
        return {
            'title': self.title,
            'href': self.href,
            'createDate': self.createDate,
            'tags': self.tags
        }

def tagIs(name1, name2):
    return name1.lower() == name2.lower()

def getAttribute(attrs, name):
    for k, v in attrs:
        if k == name:
            return v
    return None


class GBookmarkParser(HTMLParser):
    STATE_INIT = 0
    STATE_START = 1
    STATE_LABELS = 2
    STATE_READ_LABEL = 3
    STATE_READ_ITEMS = 4
    STATE_READ_ITEM = 5

    def __init__(self, labelsIgnore=[]):
        super().__init__()
        self.count = 0
        self.state = GBookmarkParser.STATE_INIT
        self.currentLabel = None
        self.currentItem = None
        self.items = {}
        self.labelsIgnore = labelsIgnore

    def handle_starttag(self, name, attrs):
        print('start {s} | {n} {a}'.format(s=self.state, n=name, a=attrs))
        if self.state == GBookmarkParser.STATE_INIT:
            if tagIs(name, 'dl'):
                self.state = GBookmarkParser.STATE_START
        elif self.state == GBookmarkParser.STATE_START:
            if tagIs(name, 'dt'):
                self.state = GBookmarkParser.STATE_LABELS
        elif self.state == GBookmarkParser.STATE_LABELS:
            if tagIs(name, 'h3'):
                self.state = GBookmarkParser.STATE_READ_LABEL
                self.currentLabel = name
            elif tagIs(name, 'dl'):
                self.state = GBookmarkParser.STATE_READ_ITEMS
                if self.currentLabel is None:
                    raise Exception('no label')
        elif self.state == GBookmarkParser.STATE_READ_ITEMS:
            if tagIs(name, 'dt'):
                self.state = GBookmarkParser.STATE_READ_ITEM
                self.currentItem = LinkItem()
        elif self.state == GBookmarkParser.STATE_READ_ITEM:
            if tagIs(name, 'a'):
                add_date = getAttribute(attrs, 'add_date')
                if add_date is None:
                    raise Exception('Non date found')
                self.currentItem.href = getAttribute(attrs, 'href')
                self.currentItem.createDate = int(int(add_date) * 1e-6)
                if self.currentLabel not in self.labelsIgnore:
                    self.currentItem.addTag(self.currentLabel)
        print(name)

    def handle_endtag(self, name):
        print('end   {s} | {n}'.format(s=self.state, n=name))
        if self.state == GBookmarkParser.STATE_READ_LABEL:
            if tagIs(name, 'h3'):
                self.state = GBookmarkParser.STATE_LABELS
        elif self.state == GBookmarkParser.STATE_LABELS:
            if tagIs(name, 'dt'):
                self.state = GBookmarkParser.STATE_START
        elif self.state == GBookmarkParser.STATE_READ_ITEMS:
            if tagIs(name, 'dl'):
                self.state = GBookmarkParser.STATE_LABELS
        elif self.state == GBookmarkParser.STATE_READ_ITEM:
            if tagIs(name, 'a'):
                print(self.currentItem)
                self.addItem(self.currentItem)
                self.state = GBookmarkParser.STATE_READ_ITEMS

    def handle_data(self, data):
        print('char  {d}'.format(d=data))
        if self.state == GBookmarkParser.STATE_READ_LABEL:
            self.currentLabel = data.strip()
        elif self.state == GBookmarkParser.STATE_READ_ITEM:
            self.currentItem.title = data

    def addItem(self, linkItem):
        href = linkItem.href
        if href in self.items:
            for tag in linkItem.tags:
                self.items[href].addTag(tag)
        else:
            self.items[href] = linkItem

class RaindropXMLBuilder(object):
    def __init__(self):
        self.collections = {}

    def addLinkItem(self, collectionName, item):
        if collectionName not in self.collections:
            self.collections[collectionName] = []
        self.collections[collectionName].append(item)


    def buildXml(self):
        header = '''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Raindrop.io Bookmarks</TITLE>
<H1>Raindrop.io Bookmarks</H1>
<DL><p>
'''
        lines = [header]
        for collectionName in self.collections:
            now = int(datetime.datetime.now().timestamp())
            lines.append('<DT><H3 ADD_DATE="{d1}" LAST_MODIFIED="{d2}">{c}</H3>'
                         .format(d1=now, d2=now, c=collectionName))
            lines.append('<DL><p>')
            for item in self.collections[collectionName]:
                lines.append(('<DT><A HREF="{h}" ADD_DATE="{d1}"' +
                              ' LAST_MODIFIED="{d2}" TAGS="{ts}">{t}</A>')
                              .format(t=item.title, h=item.href,
                                      d1=item.createDate, d2=item.createDate,
                                      ts=','.join(item.tags)))
            lines.append('</DL><p>')
        lines.append('</DL><p>')
        return '\n'.join(lines)

def main():
    inFileXml = GBOOKMARK_XML
    intFileJson = INTERMEDIATE_JSON
    outFileXml = RAINDROP_XML
    collectionName = RAINDROP_COLLECTION_NAME
    labelsIgnore = ['ラベルなし']
    parser = GBookmarkParser(labelsIgnore=labelsIgnore)
    with open(inFileXml, 'r') as f:
        xmlText = f.read()
        parser.feed(xmlText)
        parser.close()
    items = parser.items
    objs = [items[key].toJSON() for key in items.keys()]
    with open(intFileJson, 'w') as f:
        f.write(json.dumps(objs, indent=2, ensure_ascii=False))
    builder = RaindropXMLBuilder()
    for k in items.keys():
        builder.addLinkItem(collectionName, items[k])
    with open(outFileXml, 'w') as f:
        outXml = builder.buildXml()
        f.write(outXml)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
