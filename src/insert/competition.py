import logging
from datetime import datetime

from sqlalchemy import Engine, and_
from sqlalchemy.orm import Session

from ..schema import Competition


def populate_competitions(
    engine: Engine, associations_competitions: dict, season: datetime
):
    """Populate the database with associations and their respective competitions.

    Args:
        engine (Engine): Engine connected to the database.
        associations_competitions (dict): Dictionary with associations as keys and competitions as values.
    """
    with Session(engine) as session:
        session.begin()
        for assoc, comps in associations_competitions.items():
            for comp in comps:
                # TODO This would be also necessary everywhere we filter comp by name
                # if assoc in comp:
                #     comp.replace(assoc, "").strip()
                try:
                    comp_obj = (
                        session.query(Competition)
                        .where(
                            and_(
                                Competition.name == comp,
                                Competition.association == assoc,
                                Competition.year == season.isoformat(),
                            )
                        )
                        .first()
                    )
                    if not comp_obj:
                        comp_obj = Competition(
                            name=comp, association=assoc, year=season.isoformat()
                        )
                        session.add(comp_obj)
                        logging.info(f"Added {assoc} {comp}")
                except:
                    session.rollback()
                    raise
                else:
                    session.commit()
