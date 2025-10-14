document.addEventListener("DOMContentLoaded", function () {

  const addFormButton = document.getElementById("add-form-button");
  if (!addFormButton) return;

  const formsetContainer = document.getElementById("formset-container");
  const totalFormsInput = document.querySelector("#id_cells-TOTAL_FORMS");
  const blankFormDiv = document.getElementById("blankForm");

  addFormButton.addEventListener("click", function () {
    const totalForms = parseInt(totalFormsInput.value);
    const newFormHtml = blankFormDiv.innerHTML.replace(
      /__prefix__/g,
      totalForms
    );

    const newFormWrapper = document.createElement("div");
    newFormWrapper.classList.add(
      "rounded",
      "row",
      "border",
      "bg-gulf-blue-200",
      "px-2",
      "my-3",
      "gap-4",
      "m-auto",
      "grid",
      "grid-cols-2"
    );
    // Create a temporary container and insert new form HTML
    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = newFormHtml;

    // Remove all empty divs with class 'text-red-500'
    tempDiv.querySelectorAll("div.text-red-500").forEach((div) => {
      if (div.innerHTML.trim() === "") {
        div.remove();
      }
    });

    // Now select each field div
    const fields = tempDiv.querySelectorAll("div"); // each field is wrapped in a div
    if (fields.length > 0) {
      const labelSpan = document.createElement("span");
      labelSpan.className = "font-bold";
      labelSpan.textContent = `${totalForms + 1}.`;

      fields[0].prepend(labelSpan); // Add the number to the first field
    }

    // Append all fields to the wrapper
    fields.forEach((field) => {
      newFormWrapper.appendChild(field);
    });

    // Append the wrapper to the container and increment total forms count
    formsetContainer.appendChild(newFormWrapper);
    totalFormsInput.value = totalForms + 1;
  });
   function toggleSubstationVisibility() {
    const newSubstationContainer = document.getElementById('new_substation_container');
    const existingSubstationContainer = document.getElementById('existing_substation_container');
    const substationChoice = document.querySelector('input[name="substation_choice"]:checked').value;

    if (substationChoice === 'new') {
      newSubstationContainer.classList.remove('hidden');
      // clear inputs in the new substation form
      for (const input of newSubstationContainer.querySelectorAll('input[type="text"], select')) {
        input.value = ''; // Clear the input value
      }
      existingSubstationContainer.classList.add('hidden');
      document.getElementById('id_new_substation').focus(); // Focus the new substation input
    } else {
      newSubstationContainer.classList.add('hidden');
      existingSubstationContainer.classList.remove('hidden');
      // clear substation input
      document.getElementById('id_substation').value = ''; // Clear the existing sub
      document.getElementById('id_substation').focus(); // Focus the existing substation input
    }
  }

  // Add event listeners to radio buttons to toggle visibility
  document.querySelectorAll('input[name="substation_choice"]').forEach((radio) => {
    radio.addEventListener('change', toggleSubstationVisibility);
  });

  // Initial call to set visibility based on the default selected option
  toggleSubstationVisibility();

});
