$(document).on('change', '#id_type', function() {
  var selectedValue = $(this).val();
  $('#clear_credit_form').hide();
  $('#tamper_token_form').hide();
  $('#reimbursement_form').hide();
 $('#fault_maintanance_form').hide();
  $('#reconnection_form').hide();
  $('#faulty_meter_form').hide();
  $('#recovered_meter_form').hide();
  $('#old_token_form').hide();
  switch (selectedValue) {
    case 'CLEAR CREDIT':
      $('#clear_credit_form').show();
      break;
    case 'REIMBURSEMENT':
      $('#reimbursement_form').show();
      break;
    case 'TEMPER':
      $('#tamper_token_form').show();
      break;
  }
});

$(document).on('change', '#id_is_for', function() {
  var selectedValue = $(this).val();
  $('#fault_maintanance_form').hide();
  $('#reconnection_form').hide();
  $('#faulty_meter_form').hide();
  $('#recovered_meter_form').hide();
  $('#old_token_form').hide();
  switch (selectedValue) {
    case 'Fauty Maintanance':
      $('#fault_maintanance_form').show();
      break;
    case 'Recovered Meter':
      $('#recovered_meter_form').show();
      break;
    case 'Reconnection':
      $('#reconnection_form').show();
      break;
  }
});$(document).on('change', '#id_purpose', function() {
  var selectedValue = $(this).val();
  $('#fault_maintanance_form').hide();
  $('#reconnection_form').hide();
  $('#faulty_meter_form').hide();
  $('#recovered_meter_form').hide();
  $('#old_token_form').hide();
  switch (selectedValue) {
    case 'Faulty Meter':
      $('#faulty_meter_form').show();
      break;
    case 'Recovered Meter':
      $('#recovered_meter_form').show();
      break;
    case 'Old Token':
      $('#old_token_form').show();
      break;
  }
});