var db = require("../database.js");

exports.index = (req, res, next) => {
  db.all(
    "SELECT * FROM player_table AS p JOIN human_table AS h ON p.human = h.id;",
    (err, rows) => {
      if (err) {
        res.status(400);
        return;
      }
      console.log(rows[0]);
      res.render("player_list", { title: "Player List", player_list: rows });
    },
  );
};

exports.single = async (req, res, next) => {
  const human_id = req.params.human_id;

  const playerIdentities = await getPlayerIdentitiesForHuman(human_id);
  console.log(playerIdentities);

  const ratings = await getRatingsForPlayerIdentities(playerIdentities);
  console.log(ratings);

  const matches = await getMatchesForPlayerIdentities(playerIdentities);
  console.log(matches);

  res.render("player", {
    player: playerIdentities,
    matches: matches,
    ratings: ratings,
  });
};

function getPlayerIdentitiesForHuman(human_id) {
  return new Promise((resolve, reject) => {
    const stmt = db.prepare(
      `SELECT h.name, p.id, p.association_id, c.name AS clubname
      FROM player_table AS p
      JOIN human_table AS h ON p.human = h.id
      JOIN club_table AS c ON c.id = p.club
      WHERE p.human = ?;`,
      [human_id],
    );
    stmt.all((err, rows) => {
      if (err) {
        reject(err);
      } else {
        resolve(rows);
      }
    });
  });
}

function getRatingsForPlayerIdentities(identities) {
  const player_ids = identities.map((player) => player.id);
  const placeholders = player_ids.map(() => "?").join(", ");
  return new Promise((resolve, reject) => {
    const stmt = db.prepare(
      `SELECT sr.rating_mu, sr.rating_sigma, c.name AS competition_name
        FROM skillrating_table as sr
        JOIN competition_table AS c ON c.id = sr.competition
        WHERE sr.player IN (${placeholders});`,
      [...player_ids],
    );
    stmt.all((err, rows) => {
      if (err) {
        reject(err);
      } else {
        resolve(rows);
      }
    });
  });
}

function getMatchesForPlayerIdentities(identities, callback) {
  const player_ids = identities.map((player) => player.id);
  console.log("player_ids", player_ids);
  const placeholders = player_ids.map(() => "?").join(", ");

  return new Promise((resolve, reject) => {
    const stmt = db.prepare(
      `SELECT
        hh.name AS home_name,
        hh.id AS home_human,
        ah.id AS away_human,
        hc.name AS home_club,
        ah.name AS away_name,
        ac.name AS away_club,
        m.result,
        ht.rank AS home_team,
        at.rank AS away_team
      FROM
        singlesmatch_table AS m
      JOIN
        teammatch_table AS tm ON tm.id = m.team_match
      JOIN
        player_table AS hp ON m.home_player = hp.id
      JOIN
        player_table AS ap ON m.away_player = ap.id
      JOIN
        human_table AS hh ON hp.human = hh.id
      JOIN
        human_table AS ah ON ap.human = ah.id
      JOIN
        club_table AS hc ON hc.id = hp.club
      JOIN
        club_table AS ac ON ac.id = ap.club
      JOIN
        team_table AS ht ON ht.id = tm.home_team
      JOIN
        team_table AS at ON at.id = tm.away_team
      WHERE
          (m.home_player IN (${placeholders}))
          OR
          (m.away_player IN (${placeholders}));`,
      [...player_ids, ...player_ids],
    );
    stmt.all((err, rows) => {
      if (err) {
        reject(err);
      } else {
        resolve(rows);
      }
    });
  });
}
