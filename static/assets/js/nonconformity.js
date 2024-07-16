
  $(document).ready(function() {
      $('#acceptButton').click(function() {
          $('#accepted').val("True");
          if ($('#acceptForm').is(':visible')) {
              if (confirm('Are you sure you want to submit the form?')) {
                  $('#form').submit();
              }
          } else {
              $('#acceptForm').show();
              $('#rejectForm').hide();
          }
      });
  
      $('#rejectButton').click(function() {
          $('#accepted').val("False");
          if ($('#rejectForm').is(':visible')) {
              if (confirm('Are you sure you want to submit the form?')) {
                  $('#form').submit();
              }
          } else {
              $('#rejectForm').show();
              $('#acceptForm').hide();
          }
      });
  
  //     const closeButton = document.getElementById('closeButton');
  //     if (closeButton) {
  //         closeButton.addEventListener('click', function() {
  //             $('#id_closed').val("True");
  //             if ($('#closeformcontainer').is(':visible')) {
  //                 if (confirm('Are you sure you want to submit the form?')) {
  //                     $('#form').submit();
  //                 }
  //             } else {
                  $('#closeformcontainer').show();
                  $('#editformcontainer').hide();
  //             }
  //         });
  //     }
  // });
  // $(document).ready(function() {
    $('#closeButton').click(function() {
        alert('Close button clicked!');
        // Add your logic here
    });
});
document.addEventListener('DOMContentLoaded', function() {
  var closeButton = document.getElementById('closeButton');
  closeButton.addEventListener('click', function() {
      alert('Close button clicked!');
      // Add your logic here
  });
});