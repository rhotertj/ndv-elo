import concurrent.futures
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(r"S:\Dokumente\Code\ndv-elo\src")
# trunk-ignore(ruff/E402)
from crawler import Crawler2K


def crawl_competition(season, results, association, competition, from_date):
    """Function that can crawls data for one competition. Should be used concurrently.
    Depends on a selenium docker instance.

    Args:
        season (int): Season to crawl. Determines crawler URL.
        results (dict): Results in standard format.
        association (str): Name of the association.
        competition (str): Name of the competition within the association.
        from_date (datetime): Matches before this date will be ignored in crawling.

    Returns:
        dict: Results in standard format.
    """
    logging.info(f"Start {association}: {competition}")
    # Prepare empty result dict for each thread
    with Crawler2K(season) as crawler:
        results["crawled_competitions"][association] = [competition]
        results[association] = {}
        results[association][competition] = {}
        clubs_teams, players = crawler.get_clubs_and_teams([association], [competition])
        matchdays, matches = crawler.get_matches(
            [association], [competition], from_date=from_date
        )
        results[association][competition]["clubs_teams"] = {
            club: list(teams) for club, teams in clubs_teams.items()
        }
        results[association][competition]["matches"] = matches
        results[association][competition]["players"] = players
        for match in matchdays:
            match["date"] = match["date"].isoformat()
        results[association][competition]["team_matches"] = matchdays

    return results


if "__main__" == __name__:
    import argparse

    parser = argparse.ArgumentParser(description="Crawl data from 2k app.")

    parser.add_argument(
        "--date",
        help="Matches before this date are ignored. Expects YYYY-MM-DD.",
        required=False,
    )
    parser.add_argument(
        "--path", help="Destination for the crawled data.", required=True
    )
    parser.add_argument(
        "--season",
        help="What season we crawl. Expects YYYY (will be set to first of august that year.)",
        required=True,
        type=int,
    )
    parser.add_argument(
        "--associations",
        help="Limit associations to be crawled.",
        nargs="*",
        default=["DBH", "NDV"],
    )
    parser.add_argument(
        "--max-retries",
        help="Maximum number of retries per competition.",
        required=False,
        default=5,
        type=int,
    )
    args = parser.parse_args()

    logging.basicConfig(encoding="utf-8", level=logging.INFO)

    data_path = Path(args.path)
    # os.makedirs(data_path, exist_ok=True)
    season = datetime(args.season, 8, 1)
    if not args.date:
        from_date = season
    else:
        from_date = datetime.fromisoformat(args.date)
    logging.info(f"Only checking matches past {from_date}")

    jobs = []
    with Crawler2K(args.season) as crawler:
        if args.associations[0] == "all":
            assocs = crawler.get_associations()
        else:
            assocs = args.associations
        for a in assocs:
            comps = crawler.get_competitions(a)
            for c in comps:
                results = {}
                results["from_date"] = from_date.isoformat()
                results["crawled_date"] = datetime.now().isoformat()
                results["season"] = season.isoformat()
                results["crawled_competitions"] = {}
                jobs.append((args.season, results, a, c, from_date))

    while len(jobs) > 0:
        logging.info(f"Running for {len(jobs)} jobs")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_job = {
                executor.submit(crawl_competition, *job): job for job in jobs
            }
            for future in concurrent.futures.as_completed(future_to_job):
                job = future_to_job[future]
                season, _, a, c, from_date = job
                logging.info(f"Finished job for {a,c}")
                try:
                    data = future.result()
                    time_str = datetime.fromisoformat(data["crawled_date"]).strftime(
                        "%Y-%m-%d-T%H+%M+%S"
                    )
                    with open(
                        data_path / f"{season}" / f"{a}_{c}_{time_str}.json",
                        "w+",
                    ) as f:
                        json.dump(data, f)
                    jobs.remove(job)
                except Exception:
                    logging.error(f"{c} crashed, up for retry")
