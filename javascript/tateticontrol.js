playerACustomAttr = "data-playerA";
playerBCustomAttr = "data-playerB";
winnerCustomAttr = "data-winner";
currentPlayer = playerACustomAttr;
displayCurrentPlayer();

successCases = [
		["pos_1_1",
		"pos_1_2",
		"pos_1_3"],
		["pos_2_1",
		"pos_2_2",
		"pos_2_3"],
		["pos_3_1",
		"pos_3_2",
		"pos_3_3"],
		["pos_1_1",
		"pos_2_1",
		"pos_3_1"],
		["pos_1_2",
		"pos_2_2",
		"pos_3_2"],
		["pos_1_3",
		"pos_2_3",
		"pos_3_3"],
		["pos_1_1",
		"pos_2_2",
		"pos_3_3"],
		["pos_1_3",
		"pos_2_2",
		"pos_3_1"]
		];

function play(event){
	targetToken = event.target;
	if (isTaken(targetToken)){
		alert("Token already taken. Choose another.");
	} else {
		markCurrent(targetToken);
		if (checkWinner()){
			displayWinner();
		} else {
			changePlayer();
		}
	}
}

/**
 * Return true if the token is already taken by any player. 
 */
function isTaken(token) {
	return (token.innerHTML != "");
}

/**
 * Mark the given token (a button element) as taken by the current player.
 */
function markCurrent(token){
	player = playerACustomAttr;
	mark = "O"; //Player A
	if (currentPlayer == playerBCustomAttr){
		player = playerBCustomAttr;
		mark = "X";
	}
	token.innerHTML = mark;
	token.setAttribute(player, true);
}

/**
 * Verify if the current player is the winner.
 * Return true if positive, false otherwise.
 */
function checkWinner(){
	is_winner = false;
	for(i=0; i<successCases.length;i++){
		is_winner = true;
		for(j=0; j<3 && is_winner;j++){
			token = document.getElementById(successCases[i][j]);
			is_winner = is_winner &&  token.hasAttribute(currentPlayer);
		}
		if (is_winner) {
			// Mark the winning tokens and return true.
			for(j=0; j<3 && is_winner;j++){
				token = document.getElementById(successCases[i][j]);
				token.setAttribute(winnerCustomAttr, true);
			}
			break;
		}
	}

	return is_winner;
}

/**
 * Change the current player.
 */
function changePlayer(){
	if (currentPlayer == playerACustomAttr){
		currentPlayer = playerBCustomAttr;
	} else {
		currentPlayer = playerACustomAttr;
	}
	displayCurrentPlayer();

	return;
}

/**
 * Identify the current player, and its token, in the document's given area.
 */
function displayCurrentPlayer(){
	document.getElementById("current_player").innerHTML = 
			getCurrentPlayerName() + " ("+getCurrentPlayerDisplayToken()+")";
}

/**
 * Raise a dialog box with the winner's identifier.
 */
function displayWinner(){
	playerName = getCurrentPlayerName();
	alert("Winner!\nPlayer "+playerName);
	document.getElementById("player_info").innerHTML = 
			"Winner! Player "+playerName + " ("+getCurrentPlayerDisplayToken()+")";
}

function getCurrentPlayerName(){
	playerName = "A";
	if (currentPlayer == playerBCustomAttr){
		playerName = "B";
	}
	return playerName;
}

function getCurrentPlayerDisplayToken(){
	playerToken = "<span data-playerA='true'>O</span>"
	if (currentPlayer == playerBCustomAttr){
		playerToken = "<span data-playerB='true'>X</span>"
	}
	return playerToken;
}