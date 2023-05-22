# ndv-elo

TODOS:
- Rating that includes doubles
- Plot that is aware of people available?

Crawl data:
```sh
python src/crawler.py --path [PATH] --season 202X --date [YYYY-MM-DD] --associations DBH NDV
```
Create database and populate it :
```sh
python src/data.py --filename [DB_PATH] && \
python src/insert_data.py -db [DB_PATH] --data [DATA_PATH]
```

