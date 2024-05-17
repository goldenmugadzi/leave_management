
  $(document).ready(function() {
  $('#acceptButton').click(function() {
    $('#accepted').val("True");
    if ($('#acceptForm').is(':visible')) {
      
      if (confirm('Are you sure you want to submit the form?')) {
        $('#form').submit();
    }
  }
  else{
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
  }
  else{
    $('#rejectForm').show();
      $('#acceptForm').hide();
     
  }
  });
});