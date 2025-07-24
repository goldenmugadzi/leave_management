document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM ready, JS working");

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
});
