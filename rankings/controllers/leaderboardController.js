var db  = require("../database.js");

exports.index = (req, res, next) => {
    const competition_name = req.params.competition.replace(/-/g, " ")
    const season = req.params.season

    let stmt = db.prepare(
        `SELECT p.name, cl.name AS club_name, s.rating_mu, s.rating_sigma
         FROM player_table AS p
         JOIN skillrating_table AS s ON s.player = p.id
         JOIN club_table AS cl ON p.club = cl.id
         JOIN competition_table as c ON c.id = s.competition
         WHERE lower(c.name) = lower(?) AND date(c.year) = date(? || '-08-01')
         ORDER BY s.rating_mu DESC;
         `);
    stmt.all(
          [competition_name, season]
         ,
        (err, rows) => {
            if (err) {
              console.log(err)
              res.status(404);
              return;
            }
            console.log(rows)
            if (rows === undefined){
              rows = []
            }
            res.render("leaderboard", { title: `Leaderboard - ${competition_name} (${season})`, player_list: rows });
    });
  };