# NDV Trueskill

Crawl match results for all darts leagues in Lower-Saxony and rank players based on their "true skill".

A short summary of how TrueSkill works can be found [here](https://www.microsoft.com/en-us/research/project/trueskill-ranking-system).

The matches are crawled from the [2K App](https://ndv.2k-dart-software.de/index.php/de/component/dartliga/index.php?option=com_dartliga&controller=showligagameplan&layout=showdashboard&filVbKey=6&filCompKey=1&filSaiKey=112&filVbsubKey=1&filStaffKey=667&filStaffFsGrpdataKey=0#%22).

## Usage

Crawl data:
```sh
python src/crawler.py --path [PATH] --season 202X --date [YYYY-MM-DD] --associations DBH NDV
```
Create database and populate it :
```sh
python src/data.py --filename [DB_PATH] && \
python src/insert_data.py -db [DB_PATH] --data [DATA_PATH]
```

## TODO

- Rating that includes doubles
- A webservice to serve plots
