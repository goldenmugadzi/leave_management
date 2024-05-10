  $(document).on('change', '#id_status', function() {
    var selectedValue = $(this).val();
    if (selectedValue === 'False') {
      $('#AcceptedForm').hide();
    } else {
      $('#AcceptedForm').show();
    }
  }); 