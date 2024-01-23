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
  res.status(503)
}