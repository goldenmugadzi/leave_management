document.getElementById('add-form-button').addEventListener('click', () => {
    const container = document.getElementById('formset-container');
    const totalForms = document.getElementById('id_entries-TOTAL_FORMS');

    const nextIndex = parseInt(totalForms.value);
    const newFormDiv = document.createElement('div');
    newFormDiv.className = 'rounded row border padding-3 bg-gulf-blue-200';
     newFormDiv.innerHTML = `
                                <span class="font-bold">${nextIndex + 1}.</span>
                                <label for="id_entries-${nextIndex}-instruction">Instruction:</label>
                                <input type="text" name="entries-${nextIndex}-instruction" maxlength="500"
                                class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                                aria-describedby="id_entries-${nextIndex}-instruction_helptext"
                                id="id_entries-${nextIndex}-instruction">
                                <div class="text-red-500"></div>
                            `;
    container.appendChild(newFormDiv);
    totalForms.value = nextIndex + 1;
});

$(document).ready(function() {
});

