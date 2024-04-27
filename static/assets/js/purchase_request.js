document.getElementById('add-form-button').addEventListener('click', function () {
    const container = document.getElementById('formset-container');
    const totalForms = document.getElementById('id_pritem_set-TOTAL_FORMS');
    const emptyFormHtml = document.getElementById('blankForm').innerHTML;
    const newFormHtml = emptyFormHtml.replace(/__prefix__/g, container.children.length);

    // Create a new div element to contain the form
    const newFormDiv = document.createElement('div');
    newFormDiv.classList.add('rounded', 'row', 'rounded', 'border', 'bg-gulf-blue-200', 'px-2', 'my-3', 'gap-4', 'm-auto', 'grid', 'grid-cols-3');
    newFormDiv.innerHTML = newFormHtml;

    // Append the new form to the formset-container
    container.appendChild(newFormDiv);

    // Update the TOTAL_FORMS field
    totalForms.value = parseInt(totalForms.value) + 1;
});