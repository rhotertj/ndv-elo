# ndv-elo

TODOS:

- Proper process for updating db and ratings without going through complete season
- CLI args for scripts
- More common queries
- Title for plots
- Season plot, player performace per competition (make scatterplot, rating and teams as axis)
- Make inserting data and queries season sensitive!
- Investigate parsing issues for names and matches

Crawl data:
```sh
python src/crawler.py
```
Create database and populate it :
```sh
python src/data.py && python src/insert_data.py
```

