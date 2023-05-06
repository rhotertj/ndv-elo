# ndv-elo

TODOS:

- Check player belong to club when adding matches via teammatch object
- Create unknown players that appear in matches. Player gets temp (000000) assoc id and club and name 
    -> Done for singles, add checks and playr creation to doubles (lots of copying possible!)
- More common queries
- Title for plots
- Season plot, player performace per competition (make scatterplot, rating and teams as axis)
- Make inserting data and queries season sensitive!
- Investigate parsing issues for names and matches
- Rating that includes doubles

Crawl data:
```sh
python src/crawler.py
```
Create database and populate it :
```sh
python src/data.py && python src/insert_data.py
```

