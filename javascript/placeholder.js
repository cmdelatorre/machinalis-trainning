PLACEHOLDERATTRNAME = "myplaceholder"
CUSTOMATTR = "data-placeholdered"
/**
 * Auxiliar
 */
log = console.log

function implement_placeholder(inputElement){
	//console.log(inputElement + getElemPH(inputElement));
	applyMyPlaceholder(inputElement, getElemPH(inputElement));
	inputElement.onfocus = removeMyPlaceholder;
	inputElement.onblur = setPlaceholderIfEmpty;
	return;
}

function getElemPH(elem){
	var ph = ""; //PlaceHolder
	if (elem.hasAttribute(PLACEHOLDERATTRNAME)){
		ph = elem.getAttribute(PLACEHOLDERATTRNAME);
	}

	return ph;
}

function applyMyPlaceholder(elem, elemPH){
	if (elem.value == ""){
		elem.value = elemPH;
		elem.setAttribute(CUSTOMATTR, true)
	}
	return;
}

function removeMyPlaceholder(event){
	//log(event.target.value + "<- val . PH ->" + getElemPH(event.target));
	if (event.target.value == getElemPH(event.target)){
		event.target.value = "";
		if (event.target.hasAttribute(CUSTOMATTR)){
			event.target.removeAttribute(CUSTOMATTR);
		}
	}
	return;
}

function setPlaceholderIfEmpty(event){
	applyMyPlaceholder(event.target, getElemPH(event.target));
}


/**
 * Main
 */

var inputs = document.getElementsByTagName('input');
for(var i=0; i<inputs.length; i++) {
	var targetInput = inputs[i];
	implement_placeholder(targetInput);
}

