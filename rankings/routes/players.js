var express = require('express');
const playerController = require("../controllers/playerController")
var router = express.Router();

router.get("/", playerController.index);

// todo go for human model that has player identities
// each human has a player identity token that is truly unique
// that way, we can map old 96 identities to dart akademie and so on.
router.get("/:token", playerController.single);
// we need: competitions leaderboard (via browser competitions), playerInfo, match info
// search bar to browser players / competitions
// use controller to forward search result to correct list
module.exports = router;
