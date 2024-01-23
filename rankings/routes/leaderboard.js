var express = require('express');
const leaderboardController = require("../controllers/leaderboardController");
var router = express.Router();

// Here we can show an alltime leaderboard (global rankings)
router.get('/', leaderboardController.index);

router.get('/:competition/:season', leaderboardController.index);
    
module.exports = router;