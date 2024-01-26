var db  = require("../database.js")

exports.index = (req, res, next) => {
    db.all(
        "SELECT * FROM player_table;",
        (err, rows) => {
            if (err) {
              res.status(400);
              return;
            }
            console.log(rows[0])
            res.render("player_list", { title: "Player List", player_list: rows});
    });
    
  };

exports.single = (req, res, next) => {
  const player_id = req.params.player_id
  // select past matches
  // select past rankings in all competitions
  // select past teams / clubs played in 
  db.prepare()
  // SELECT * FROM singlesmatch_table AS match JOIN human_table 
  // WHERE match.home_player = 
}