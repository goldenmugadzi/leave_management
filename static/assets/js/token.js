$(document).on('change', '#id_type', function() {
  var selectedValue = $(this).val();
  if (selectedValue === 'CLEAR CREDIT') {
    $('#clear_credit_form').show();
    $('#tamper_token_form').hide();
    $('#reimbursement_form').hide();
  }
  else if (selectedValue === 'REIMBURSEMENT') {
    $('#reimbursement_form').show();
    $('#clear_credit_form').hide();
    $('#tamper_token_form').hide();
  }
  else if (selectedValue ==='TEMPER TOKEN') {
    $('#tamper_token_form').show();
    $('#clear_credit_form').hide();
    $('#reimbursement_form').hide();
    // $('#id_pernalty').hide();
  }
});
$(document).on('change', '#id_is_for', function() {
  var selectedValue = $(this).val();
  if (selectedValue === 'Fauty Maintanance') {
    $('#fault_maintanance_form').show();
    $('#recovered_meter_form').hide();
    $('reconnection_form').hide();
  }
  else if (selectedValue === 'Recovered Meter') {
    $('#fault_maintanance_form').hide();
    $('#recovered_meter_form').show();
    $('reconnection_form').hide();
  }
  else if (selectedValue === 'Reconnection') {
    $('#fault_maintanance_form').hide();
    $('#recovered_meter_form').hide();
    $('reconnection_form').show();
  }
});
