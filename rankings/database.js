var sqlite3 = require('sqlite3');

const db = new sqlite3.Database('../new.db', sqlite3.OPEN_READONLY);
// db.all("select * from player_table;", (err, rows) => {
//   rows.forEach(row => {
//       console.log(row);
//   });
// });

module.exports = db;