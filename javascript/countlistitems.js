function countItems(aList){
	var cntr = 0;
	items = aList.getElementsByTagName("li");
	cntr += items.length;
	subLists = document.getElementsByTagName("ul");
	var N = subLists.length;

	return cntr;
}

function renderResults(nItems){
	return "<span style='color:red'>["+nItems+"]</span>";
}

console.log("carga");
allTheLists = document.getElementsByTagName("ul");
console.log("Corre sobre:"+allTheLists.length);
for (j=0; j<allTheLists.length; j++){
	var current = allTheLists[j];
	console.log("Probando el nodo"+current)
	var nItems = countItems(current);
	console.log(nItems);
	for (k=0; j<current.childNodes.length; k++){
		textNode = current.childNodes[k];

		if (textNode.nodeType == 3 && textNode != ""){
			console.log(textNode + renderResults(nItems));
			textNode.innerHTML += renderResults(nItems);
			break;
		}
	}

/*


	elementHTML = current.innerHTML
	//console.log(current.innerHTML);
	newLineCharPosition = elementHTML.indexOf("\n");
	console.log(elementHTML);
	console.log(newLineCharPosition);
	if (newLineCharPosition != -1){
		prefix = elementHTML.substr(0,newLineCharPosition);
		suffix = elementHTML.substr(newLineCharPosition);
	}
	current.innerHTML = 
			prefix + renderResults(nItems) + suffix;*/
}
