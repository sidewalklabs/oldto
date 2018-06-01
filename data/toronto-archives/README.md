# Toronto Archives Data Collection

The Toronto Archives' web site has 100,000+ digitized photos. To collect data on all
the digitized photos, we use an empty search on their mobile web site and iterate
through the paginated results.

Here's the procedure:

1. Visit the [mobile archives site][m] and hit "Search". Copy the `ClientSession`
   URL parameter. This is a long hex string, e.g. `-a47dfc9:160e3d0b97e:-7f39`.
2. Open `data/search_urls.txt` and put your new `ClientSession` value in to all the URLs.
3. Run

        oldtoronto/fetcher.py data/search_urls.txt

   This will fetch all the results pages and store them in a cache for later
   use.
4. Read the results pages from the cache, parse them and produce the `data/images.ndjson` file.

   oldtoronto/parse-results.py

To fetch complete metadata for this sample of images, write out a new version
of `record-ids.txt` with the unique IDs of the random images (note that these URLs
don't have session IDs!). Then fetch and parse them:

    oldtoronto/write_records_txt.py data/images.random1000.ndjson > data/record_ids.txt
    oldtoronto/fetch_archive_records.py data/record_ids.txt
    oldtoronto/parse_records.py data/record_ids.txt data/images.ndjson

This produces `images.ndjson`, which has full metadata. The `data/images.ndjson` that is
committed on GitHub has full metadata for all images.

### Citation Hierarchy

Sometimes the file, series, subseries and fonds pages can have valuable data as well.
For example, [this image][image] lacks a date, but the date can be found in its [file][].

Unfortunately there's no way to list all the files, subseries, series and fonds in the way that you
can list all the digitized images. So to get IDs for these, we need to fetch full records for a
set of images that are part of each part of the hierarchy.

To download and attach this data, run:

    ./write_record_url_per_file.py > record-per-file.txt
    ./fetch_archive_records.py record-per-file.txt
    ./write_all_series.txt > series-ids.txt
    ./fetch_archive_records.py series-ids.txt
    ./parse_records.py series-ids.txt series.ndjson

The `series.ndjson` file now contains a record for each level of the hierarchy that contains a
digitized image.

[m]: https://gencat.eloquent-systems.com/city-of-toronto-archives-m-public.html
[image]: https://gencat.eloquent-systems.com/city-of-toronto-archives-m-permalink.html?key=571480
[file]: https://gencat.eloquent-systems.com/city-of-toronto-archives-m-permalink.html?key=348714
