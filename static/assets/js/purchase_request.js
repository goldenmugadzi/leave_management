$(document).ready(function () {
  $("#add-item-button").click(function () {
    var formIdx = $("#id_pritem_set-TOTAL_FORMS").val();
    var num = parseInt(formIdx) + 1;
    alert(num);
   var clonedElement = $("#formset-container").children().eq(-2).clone();
   
    $("#formset-container").children().eq(-2).after(clonedElement);

    var newElement = $("#formset-container").children().eq(-2).next();

    const regex = new RegExp('__prefix__', 'g')
    newElement.innerHTML = newElement.innerHTML.replace(regex, num)
        
    $("#id_pritem_set-TOTAL_FORMS").val(parseInt(formIdx) + 1);
  });
});
