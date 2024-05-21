document.getElementById('add-form-button').addEventListener('click', () => {
    const container = document.getElementById('formset-container');
    const totalForms = document.getElementById('id_pritem_set-TOTAL_FORMS');
    const newFormHtml = document.getElementById('blankForm').innerHTML.replace(/__prefix__/g, container.children.length);

    const newFormDiv = document.createElement('div');
    newFormDiv.className = 'rounded row border bg-gulf-blue-200 px-2 my-3 gap-4 m-auto grid grid-cols-3';
    newFormDiv.innerHTML = newFormHtml;

    container.appendChild(newFormDiv);
    totalForms.value = parseInt(totalForms.value) + 1;
});
const fileInput = document.getElementById('upload');
const form = document.getElementById('purchase-request-form');

fileInput.addEventListener('change', () => {
  $('#saveRadio').checked = true;
  form.submit();
});