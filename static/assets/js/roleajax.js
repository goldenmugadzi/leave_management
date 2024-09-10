google.charts.load("current", { packages: ["orgchart"] });

function setRoles(e) {
  const form = e.target.closest("form");
  const appId = form.querySelector('input[name="app_id"]').value;
  const userId = form.querySelector('input[name="user_id"]').value;
  $.ajax({
    type: "GET",
    url: `/users/setroles?app_id=${appId}&user_id=${userId}`,
    success: function (rdata) {
      document.getElementById("rolesModalform").innerHTML = rdata.form;
      let modal = document.getElementById("my_modal_2");
      let cc_chart = document.getElementById("cc_chart");
      const selectedAppIdElement = document.getElementById("selectedapp_id");
      if (selectedAppIdElement) {
        selectedAppIdElement.value = rdata.app.id;
      } else {
        console.error("Element with ID 'selectedapp_id' not found.");
      }
      document.getElementById("applbl").innerHTML = rdata.app.fullname;
      const idCostCenters = document.getElementById("id_cost_centers");
      let selectedItems = [];

      for (let i = 0; i < idCostCenters.options.length; i++) {
        if (idCostCenters.options[i].selected) {
          selectedItems.push(idCostCenters.options[i].value);
        }
      }
      modal.showModal();
      const chartc = new google.visualization.OrgChart(cc_chart);
      const data = new google.visualization.DataTable();
      data.addColumn("string", "Name");
      data.addColumn("string", "Manager");
      data.addColumn("string", "ToolTip");
      const response = rdata.regioncc;

      function resetData() {
        data.removeRows(0, data.getNumberOfRows());
        for (const row in response) {
          let bg_color = selectedItems.includes(response[row].id)
            ? "text-gulf-blue-700"
            : "text-gulf-blue-100";
          data.addRow([
            {
              v: response[row].id,
              f: `<div id="item-${response[row].id}" class="${bg_color} "><button type="button" onclick="assignCostCenter(${response[row].id})">${response[row].name} <div style="color:red; font-style:italic">${response[row].code}</div></button></div>`,
            },
            response[row].parent,
            response[row].parent,
          ]);
        }
        chartc.draw(data, { allowHtml: true });
      }

      function getDescendants(itemId) {
        let descendants = [];
        for (let i = 0; i < data.getNumberOfRows(); i++) {
          if (data.getValue(i, 1) === itemId) {
            descendants.push(data.getValue(i, 0));
            descendants = descendants.concat(
              getDescendants(data.getValue(i, 0))
            );
          }
        }
        return descendants;
      }
      google.visualization.events.addListener(chartc, "select", function () {
        const selection = chartc.getSelection();
        // const idCostCenters = document.getElementById("id_cost_centers");
        const options = idCostCenters.options;
        selection.forEach(function (item) {
          if (item.row != null) {
            const selectedRow = data.getValue(item.row, 0);
            if (!selectedItems.includes(selectedRow)) {
              selectedItems.push(selectedRow);
              const descendants = getDescendants(selectedRow);
              descendants.forEach(function (descendant) {
                if (!selectedItems.includes(descendant)) {
                  selectedItems.push(descendant);
                }
              });
            } else {
              selectedItems = selectedItems.filter((i) => i !== selectedRow);
              const descendants = getDescendants(selectedRow);
              descendants.forEach(function (descendant) {
                if (selectedItems.includes(descendant)) {
                  selectedItems = selectedItems.filter((i) => i !== descendant);
                }
              });
              descendants.forEach(function (descendant) {
                if (selectedItems.includes(descendant)) {
                  selectedItems = selectedItems.filter(
                    (i) => i !== selectedRow
                  );
                }
              });
            }
          }
        });
        for (let i = 0; i < options.length; i++) {
          options[i].selected = selectedItems.includes(options[i].value);
        }
        resetData();
      });
      resetData();
    },
    error: function (xhr, status, error) {
      alert(
        "error:" +
          error +
          "\n Please ensure that you gave the appropriate Cost Center to the user, and submit your changes before assigning responsibilities to the user."
      );
      document.getElementById("rolesModalform").innerHTML = xhr.responseText;
      console.error("Error:", xhr.responseText);
      // console.log(xhr.responseTex t);
    },
  });
}

document.querySelectorAll(".rolebtn").forEach(function (element) {
  element.addEventListener("click", setRoles);
});
document.getElementById("save_role").addEventListener("click", function (e) {
  e.preventDefault();
  const form = document.getElementById("Modalform");
  const formData = new FormData(form);
  $.ajax({
    type: "POST",
    url: "/users/setroles",
    data: formData,
    processData: false,
    contentType: false,
    success: function (rdata) {
      document.getElementById("my_modal_2").close();
      document.getElementById("rolesModalform").innerHTML = "";
      console.log(rdata.role);
      document.getElementById("app_" + rdata.appid).innerHTML = rdata.role;
    },
    error: function (xhr, status, error) {
      alert("Error:" + error);
      console.error("Error:", xhr.responseText);
      //  console.log(xhr);
    },
  });
});
document.getElementById("save_update").addEventListener("click", function (e) {
  e.preventDefault();
  let form = document.getElementById("user_form");
  form.submit();
});
