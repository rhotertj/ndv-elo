window.onload = function() {
    const searchWrapper = document.querySelector(".search-input")
    const inputBox = searchWrapper.querySelector("input")
    const suggBox = searchWrapper.querySelector(".suggestion-box")
    inputBox.onkeyup = (e) => {
        let q = e.target.value;
        if (q.length < 2) {
            return
        }
        console.log(`Query value ${q}`)
        let recommendations = [];
        axios.get('/recommend', {params: {'q': q} })
        .then((response) => {
            console.log(response.data)
            // Create list elements from data
            recommendations = response.data.map( (data) => {
                return `<li>${data["player_name"]} (${data["association_id"]}) | ${data["club_name"]}</li>`;
            })
            console.log(recommendations)
            // If there are none, we suggest current input
            if (!recommendations.length) {
                recommendations = `<li>Nichts und niemanden gefunden.</li>`;
            } else {
                recommendations = recommendations.join("")
            }
            searchWrapper.classList.add("active")
            suggBox.innerHTML = recommendations
            let recommElements = suggBox.querySelectorAll("li")
            recommElements.forEach( (elem) => {
                elem.setAttribute("onclick", "selectRecommendation(this)");
            })


            }).catch( (e) => {
                console.log(`Error fetching recommendations ${e}`)
            }
                
            );
    }
    window.addEventListener('click', function (e){
        console.log("click")
        if (!document.getElementsByClassName('search-wrapper')[0].contains(e.target)) {
            searchWrapper.classList.remove("active")
        }
    })
}

function selectRecommendation(queryElement) {
    let q = queryElement.textContent;
    const inputBox = document.getElementById("query-input")
    inputBox.value = q;

    let queryType; 
    // that may change, functionality needed in any case
    if (q.includes("|")){
        queryType = "player"
    }
    axios.get(`/query_${queryType}`, {params : {'q' : q} }).then((response) => {
        removeError()
        hideLoader()
        if (queryType == "player") {
            renderPlayerResults(response.data)
        }
        console.log(`Received ${response.data}`)
    }).catch((e) => {
        console.log(`Error: ${e}`)
        hideLoader();
        showError(`Die Anfrage konnte nicht bearbeitet werden. \n ${e}`)
    })
    showLoader()
    hideResults()
    const searchWrapper = document.querySelector(".search-input")
    searchWrapper.classList.remove("active")
}
// 
function renderPlayerResults(data) {
    const results = document.getElementById("results")
    lastMatches = fillResultBoxMatches("Letzte Spiele", data["last_matches"])
    results.innerHTML = lastMatches

    showResults()
} 

function fillResultBoxRanking(heading, data) {

    resultBox = `
    <div class="result-container">
        <h1>${heading}</h1>
        <div class="result-info">
            <p>Skill Rating</p>
            <div>${25.88}</div>
            <div>${25/344}</div>
            <p>Winrate</p>


        </div>
    </div>
    `
    return resultBox
}

function fillResultBoxMatches(heading, data) {
    matches = data.map(
        (m) => {
            return "<tr><td>" + m + "</td></tr>"
        })
    resultBox = `
    <div class="result-container">
        <h1>${heading}</h1>
        <div class="result-list">
            <table>
                ${matches}
            </table>
        </div>
    </div>
    `
    console.log(resultBox)
    return resultBox
}

function showResults() {
    const resultWrapper = document.getElementById("results");
    resultWrapper.classList.add("active");
}

function hideResults() {
    const resultWrapper = document.getElementById("results");
    resultWrapper.classList.remove("active");
}

function showLoader() {
    const loader = document.getElementById("loader");
    loader.classList.add("active");
}

function hideLoader() {
    const loader = document.getElementById("loader");
    loader.classList.remove("active");
}


function showError(error) {
    const errorDiv = document.getElementById("error-div");
    errorDiv.innerHTML = error;
    errorDiv.classList.add("active");
}

function removeError() {
    const errorDiv = document.getElementById("error-div");
    errorDiv.classList.remove("active")
    errorDiv.innerHTML = ""
}