function countItems(aList){
	var cntr = 0;
	items = aList.getElementsByTagName("li");
	cntr += items.length;
	subLists = document.getElementsByTagName("ul");
	var N = subLists.length;

	return cntr;
}

function appendResults(targetElem, nItems){
	var results = document.createElement('span');
	results.setAttribute("style", "color:red");
	results.appendChild(document.createTextNode(nItems));
	targetElem.insertBefore(results, targetElem.firstChild);
}


/**
 * Main
 */
allTheLists = document.getElementsByTagName("ul");
for (j=0; j<allTheLists.length; j++){
		currentList = allTheLists[j];
		nItems = countItems(currentList);
		appendResults(currentList, nItems);  
	}
