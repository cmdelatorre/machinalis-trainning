/*
 * Make the list of choices, sortable (by drag-and-drop).
 */
function sort_choices(event, ui){
    var choices = $(".choice-item");
    var pos = 1;
    for(i=0; i<choices.length; i++){
        choice = $(choices[i]);
        choice_value = $(choice.children('[id$="-choice"]'));
        if ($(choice_value).val() != ""){
            order = choice.children('[id$="ORDER"]');
            order.val(pos);
            pos += 1;
        }
    }
}
$( "#sortable-choices" ).sortable({placeholder: "ui-state-highlight", axis:"y"});
$( "#sortable-choices" ).on( "sortstop", sort_choices);
    
/*
 * Add a new, empty choice, to the list of choices.
 */
function add_empty_choice(event){
    event.preventDefault();
    var count = $('.choice-item').length;
    var tmplMarkup = $('#new-choice-template').html();
    var compiledTmpl = _.template(tmplMarkup, { id : count });
    $('#sortable-choices').append(compiledTmpl);
    // update form count
    $('#id_choice_set-TOTAL_FORMS').attr('value', count+1);
};
$("#add-choice").on("click",add_empty_choice);