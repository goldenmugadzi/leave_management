$(document).ready(function () {
  $("#acceptButton").click(function () {
    $("#accepted").val("True");
    if ($("#acceptForm").is(":visible")) {
      if (confirm("Are you sure you want to submit the form?")) {
        $("#form").submit();
      }
    } else {
      $("#acceptForm").show();
      $("#rejectForm").hide();
    }
  });

  $("#rejectButton").click(function () {
    $("#accepted").val("False");
    if ($("#rejectForm").is(":visible")) {
      if (confirm("Are you sure you want to submit the form?")) {
        $("#form").submit();
      }
    } else {
      $("#rejectForm").show();
      $("#acceptForm").hide();
    }
  });

  $("#closeformcontainer").show();
  $("#editformcontainer").hide();

  $("#closeButton").click(function () {
    alert("Close button clicked!");
    // Add your logic here
  });
});
document.addEventListener("DOMContentLoaded", function () {
  var closeButton = document.getElementById("closeButton");
  closeButton.addEventListener("click", function () {
    alert("Close button clicked!");
    // Add your logic here
  });
});
