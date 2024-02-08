//function to count the number of times the add Supplier button is clicked
var count = 1;
var item_count = 1;
item_count_element = document.getElementById("item_count");
item_count_element.value = item_count

function countClicks() {
  count = parseInt(count) + 1;
  return count;
}
//function to reduce the value of count each time a row is deleted
function countDeleteClicks() {
  count = parseInt(count) - 1;
}
//function to delete a table row
function deleteRow() {
  var containerDiv = document.getElementById("bid_container");
  var numRows = containerDiv.children.length;
  if (numRows <= 2) {
    alert("Maximum number of rows already deleted.");
  } else {
    var row = containerDiv.children[containerDiv.children.length-1].remove();
    item_count = item_count -1;
    item_count_element = document.getElementById("item_count");
    item_count_element.value = item_count
  }
}
//function to calculate total price.Pass table row id to the function
function totalPrice(i) {
  // let quantity = document.getElementById("supplier[quantity][" + i + "]");
  let qty = document.getElementById("supplier[quantity][" + i + "]").value;
  let uprice = document.getElementById("supplier[unit_price][" + i + "]").value;
  let total = document.getElementById("supplier[total_price][" + i + "]");
  let final = (qty * uprice).toFixed(2);
  parseFloat(Math.round(final * 100) / 100).toFixed(2);
  total.value = final;
}

//function to count the number of times the add suppier button is clicked
var sup_count = 1;
function supClicks() {
  sup_count = parseInt(sup_count) + 1;
}
//function to reduce the value of count each add supplier row is deleted
function supDelete() {
  sup_count = parseInt(sup_count) - 1;
}

//counts the number of cells in the last row
function cellCount() {
  var containerDiv = document.getElementById("bids_table");
  var numRows = containerDiv.children.length;
  var numCells = parseInt(containerDiv.children[numRows - 1].children.length);
  //alert('Number of cells in the last row is: '+ numCells);
  return numCells;
}
//function to add row when user clicks Add Row
function addRow() {
  
  var i = count - 1;

  var containerDiv = document.getElementById("bid_container");
 
  var divRow = document.createElement("div");
  divRow.classList.add("flex", "justify-evenly", "mt-5", "bg-nepal-500", "px-2", "py-2", "rounded-md", "border-t", "border-gray-100", "border-gray-900/10");
  containerDiv.insertBefore(divRow, containerDiv.children[containerDiv.childElementCount+1]);
  
  var itemDescrContainer = document.createElement("div");
  itemDescrContainer.classList.add("flex-1", "w-15", "ml-1")
  divRow.appendChild(itemDescrContainer)
  
  var itemDescrLabel = document.createElement("label");
  itemDescrLabel.classList.add("block", "text-sm", "font-medium", "leading-6", "text-gray-900")
  itemDescrLabel.for = "supplier[item_name][" + i + "]"
  itemDescrLabel.textContent = "Item Description"
  itemDescrContainer.appendChild(itemDescrLabel)

  var itemInputContainer = document.createElement("div");
  itemInputContainer.classList.add("mt-2")
  itemDescrContainer.appendChild(itemInputContainer)

  var itemInput = document.createElement("input");
  itemInput.classList.add("block", "w-full", "rounded-md", "border-0", "py-1.5", "text-gray-900", "shadow-sm", "ring-1", "ring-inset", "ring-gray-300", "placeholder:text-gray-400", "focus:ring-2", "focus:ring-inset", "focus:ring-indigo-600", "sm:text-sm", "sm:leading-6")
  itemInput.id = "supplier[item_name][" + i + "]"
  itemInput.name = "supplier[item_name][" + i + "]";
  itemInput.required = true
  itemInputContainer.appendChild(itemInput)

  // Quantity
  var itemQtyContainer = document.createElement("div");
  itemQtyContainer.classList.add("flex-1", "w-15", "ml-1")
  divRow.appendChild(itemQtyContainer)
  
  var itemQtyLabel = document.createElement("label");
  itemQtyLabel.classList.add("block", "text-sm", "font-medium", "leading-6", "text-gray-900")
  itemQtyLabel.for = "supplier[quantity][" + i + "]"
  itemQtyLabel.textContent = "Quantity"
  itemQtyContainer.appendChild(itemQtyLabel)

  var itemInputContainer = document.createElement("div");
  itemInputContainer.classList.add("mt-2")
  itemQtyContainer.appendChild(itemInputContainer)

  var itemInput = document.createElement("input");
  itemInput.classList.add("block", "w-full", "rounded-md", "border-0", "py-1.5", "text-gray-900", "shadow-sm", "ring-1", "ring-inset", "ring-gray-300", "placeholder:text-gray-400", "focus:ring-2", "focus:ring-inset", "focus:ring-indigo-600", "sm:text-sm", "sm:leading-6")
  itemInput.id = "supplier[quantity][" + i + "]"
  itemInput.name = "supplier[quantity][" + i + "]"
  itemInput.type = "number"
  itemInput.required = true
  itemInput.setAttribute("step", "any");
  itemInput.setAttribute("minimum","any");
  itemInput.setAttribute("oninput", "totalPrice(" + i + ")");
  itemInputContainer.appendChild(itemInput)

  // UOM
  var itemUomContainer = document.createElement("div");
  itemUomContainer.classList.add("flex-1", "w-15", "ml-1")
  divRow.appendChild(itemUomContainer)
  
  var itemUomLabel = document.createElement("label");
  itemUomLabel.classList.add("block", "text-sm", "font-medium", "leading-6", "text-gray-900")
  itemUomLabel.for = "supplier[unit_of_measurement][" + i + "]"
  itemUomLabel.textContent = "UOM"
  itemUomContainer.appendChild(itemUomLabel)

  var itemInputContainer = document.createElement("div");
  itemInputContainer.classList.add("mt-2")
  itemUomContainer.appendChild(itemInputContainer)

  var itemInput = document.createElement("select");
  itemInput.classList.add("block", "w-full", "rounded-md", "border-0", "py-1.5", "text-gray-900", "shadow-sm", "ring-1", "ring-inset", "ring-gray-300", "placeholder:text-gray-400", "focus:ring-2", "focus:ring-inset", "focus:ring-indigo-600", "sm:text-sm", "sm:leading-6")
  itemInput.id = "supplier[unit_of_measurement][" + i + "]"
  itemInput.name = "supplier[unit_of_measurement][" + i + "]"
  itemInput.appendChild(new Option("Each", "each"));
  itemInput.appendChild(new Option("Kgs", "kgs"));
  itemInput.appendChild(new Option("Grammes", "grammes"));
  itemInput.appendChild(new Option("Litres", "litres"));
  itemInput.appendChild(new Option("Metres", "metres"));
  itemInput.appendChild(new Option("Bags", "bags"));
  itemInput.appendChild(new Option("Packets", "packets"));
  itemInput.appendChild(new Option("Cartons", "cartons"));
  itemInputContainer.appendChild(itemInput)

  // VAT
  var itemVatContainer = document.createElement("div");
  itemVatContainer.classList.add("flex-1", "w-15", "ml-1")
  divRow.appendChild(itemVatContainer)
  
  var itemVatLabel = document.createElement("label");
  itemVatLabel.classList.add("block", "text-sm", "font-medium", "leading-6", "text-gray-900")
  itemVatLabel.for = "supplier[vat][" + i + "]"
  itemVatLabel.textContent = "VAT"
  itemVatContainer.appendChild(itemVatLabel)

  var itemInputContainer = document.createElement("div");
  itemInputContainer.classList.add("mt-2")
  itemVatContainer.appendChild(itemInputContainer)

  var itemInput = document.createElement("select");
  itemInput.classList.add("block", "w-full", "rounded-md", "border-0", "py-1.5", "text-gray-900", "shadow-sm", "ring-1", "ring-inset", "ring-gray-300", "placeholder:text-gray-400", "focus:ring-2", "focus:ring-inset", "focus:ring-indigo-600", "sm:text-sm", "sm:leading-6")
  itemInput.id = "supplier[vat][" + i + "]"
  itemInput.name = "supplier[vat][" + i + "]"
  itemInput.appendChild(new Option("Excl", "excl."));
  itemInput.appendChild(new Option("Incl", "incl."));
  itemInputContainer.appendChild(itemInput)

    // Unit Price
    var itemUnitPriceContainer = document.createElement("div");
    itemUnitPriceContainer.classList.add("flex-1", "w-15", "ml-1")
    divRow.appendChild(itemUnitPriceContainer)
    
    var itemUnitPriceLabel = document.createElement("label");
    itemUnitPriceLabel.classList.add("block", "text-sm", "font-medium", "leading-6", "text-gray-900")
    itemUnitPriceLabel.for = "supplier[unit_price][" + i + "]"
    itemUnitPriceLabel.textContent = "Unit Price"
    itemUnitPriceContainer.appendChild(itemUnitPriceLabel)
  
    var itemInputContainer = document.createElement("div");
    itemInputContainer.classList.add("mt-2")
    itemUnitPriceContainer.appendChild(itemInputContainer)
  
    var itemInput = document.createElement("input");
    itemInput.classList.add("block", "w-full", "rounded-md", "border-0", "py-1.5", "text-gray-900", "shadow-sm", "ring-1", "ring-inset", "ring-gray-300", "placeholder:text-gray-400", "focus:ring-2", "focus:ring-inset", "focus:ring-indigo-600", "sm:text-sm", "sm:leading-6")
    itemInput.id = "supplier[unit_price][" + i + "]"
    itemInput.name = "supplier[unit_price][" + i + "]"
    itemInput.type = "number"
    itemInput.required = true
    itemInput.setAttribute("step", "any");
    itemInput.setAttribute("minimum","any");
    itemInput.setAttribute("oninput", "totalPrice(" + i + ")");
    itemInputContainer.appendChild(itemInput)

  // Total Price
  var itemTotalPriceContainer = document.createElement("div");
  itemTotalPriceContainer.classList.add("flex-1", "w-15", "ml-1")
  divRow.appendChild(itemTotalPriceContainer)
  
  var itemTotalPriceLabel = document.createElement("label");
  itemTotalPriceLabel.classList.add("block", "text-sm", "font-medium", "leading-6", "text-gray-900")
  itemTotalPriceLabel.for = "supplier[total_price][" + i + "]"
  itemTotalPriceLabel.textContent = "Total Price"
  itemTotalPriceContainer.appendChild(itemTotalPriceLabel)

  var itemInputContainer = document.createElement("div");
  itemInputContainer.classList.add("mt-2")
  itemTotalPriceContainer.appendChild(itemInputContainer)

  var itemInput = document.createElement("input");
  itemInput.classList.add("block", "w-full", "rounded-md", "border-0", "py-1.5", "text-gray-900", "shadow-sm", "ring-1", "ring-inset", "ring-gray-300", "placeholder:text-gray-400", "focus:ring-2", "focus:ring-inset", "focus:ring-indigo-600", "sm:text-sm", "sm:leading-6")
  itemInput.id = "supplier[total_price][" + i + "]"
  itemInput.name = "supplier[total_price][" + i + "]"
  itemInput.type = "number"
  itemInput.required = true
  itemInputContainer.appendChild(itemInput)

  item_count = item_count + 1;
  item_count_element = document.getElementById("item_count");
  item_count_element.value = item_count

  }
