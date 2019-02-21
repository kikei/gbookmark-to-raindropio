# Google bookmarks to Raindrop.io

A tool for migration from google bookmarks to raindrop.io;
converter from GoogleBookmarks.html into Raindrop.io.html.

Both of Google bookmarks and Raindrop.io are online bookmarking service.
Google bookmarks has 'label' and Raindrop.io has similar function of 'tag'.

I have been using google bookmarks and its label for a long time.
So I hope labels can be migrated to raindrop.io in same structure.

We can export our bookmarks of google bookmarks as GoogleBookmarks.html,
but it will not be imported into raindrop.io well. Labels are migrated as
tags, but as collections, a huge number of collections!

Then, this script can convert 'labels' of google bookmarks into 'tags' of raindrop.io,
so that we can migrate to raindrop.io without loss of past labeling.

## Run

```
$ python3 main.py
```

Paths of source and output files are defined in top off main.py by hardcoding.

