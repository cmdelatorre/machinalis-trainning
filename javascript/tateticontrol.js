currentPlayer = "A";

function play(event){
	console.log("start");
	targetToken = event.target
	//alert(targetToken.id);
	if (targetToken.value != ""){
		alert("Impossible");
	} else {
		markCurrent(targetToken);
		changePlayer();
	}
}

function markCurrent(token){
	player = "data-playerA";
	mark = "O"; //Player A
	if (currentPlayer == "B"){
		player = "data-playerB";
		mark = "X";
	}
	token.value = mark;
	token.setAttribute(player, true)
	return;
}

function changePlayer(){
	if (currentPlayer == "A"){
		currentPlayer == "B";
	} else {
		currentPlayer == "A";
	}
	return;
}