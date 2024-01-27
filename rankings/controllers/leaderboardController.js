var db = require("../database.js");

exports.index = (req, res, next) => {
  // TODO: sanitize input
  const competition_name = req.params.competition.replace(/-/g, " ");
  const season = req.params.season;

  let stmt = db.prepare(
    `SELECT h.name, cl.name AS club_name, (s.rating_mu - 3 * s.rating_sigma) AS rating
         FROM player_table AS p
         JOIN human_table AS h ON p.human = h.id
         JOIN skillrating_table AS s ON s.player = p.id
         JOIN club_table AS cl ON p.club = cl.id
         JOIN competition_table as c ON c.id = s.competition
         WHERE lower(c.name) = lower(?) AND date(c.year) = date(? || '-08-01')
         ORDER BY rating DESC;
         `,
  );
  stmt.all([competition_name, season], (err, rows) => {
    if (err) {
      console.log(err);
      res.status(404);
      return;
    }
    console.log(rows);
    if (rows === undefined) {
      rows = [];
    }
    res.render("leaderboard", {
      title: `Leaderboard - ${competition_name.toUpperCase()} (${season})`,
      player_list: rows,
    });
  });
};
