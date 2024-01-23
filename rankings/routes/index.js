var express = require('express');
var router = express.Router();

// db.all("select * from players;");
/* GET home page. */
router.get('/', function(req, res, next) {
      res.render('index', { title: 'Dart Rankings' });
    });

module.exports = router;
