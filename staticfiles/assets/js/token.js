
document.getElementById('id_type').addEventListener('change', () => {

  var selectedValue = document.getElementById('id_type').value;
  console.log(selectedValue);
  document.getElementById('clear_credit_form').style.display = 'none';
  document.getElementById('tamper_token_form').style.display = 'none';
  document.getElementById('reimbursement_form').style.display = 'none';
  document.getElementById('fault_maintanance_form').style.display = 'none';
  document.getElementById('reconnection_form').style.display = 'none';
  document.getElementById('faulty_meter_form').style.display = 'none';
  document.getElementById('recovered_meter_form').style.display = 'none';
  document.getElementById('old_token_form').style.display = 'none';
  switch (selectedValue) {
    case 'CLEAR CREDIT':
      document.getElementById('clear_credit_form').style.display = 'block';
      break;
    case 'REIMBURSEMENT':
      document.getElementById('reimbursement_form').style.display = 'block';
      break;
    case 'TEMPER':
      document.getElementById('tamper_token_form').style.display = 'block';
      break;
  }
}
);
document.getElementById('id_purpose').addEventListener('change', () => {

  var selectedValue = document.getElementById('id_purpose').value;
  console.log(selectedValue);
  document.getElementById('clear_credit_form').style.display = 'none';
  document.getElementById('tamper_token_form').style.display = 'none';
  document.getElementById('fault_maintanance_form').style.display = 'none';
  document.getElementById('reconnection_form').style.display = 'none';
  document.getElementById('faulty_meter_form').style.display = 'none';
  document.getElementById('recovered_meter_form').style.display = 'none';
  document.getElementById('old_token_form').style.display = 'none';
  switch (selectedValue) {
    case 'Faulty Meter':
      document.getElementById('faulty_meter_form').style.display = 'block';
      break;
    case 'Recovered Meter':
      document.getElementById('recovered_meter_form').style.display = 'block';
      break;
    case 'Old Token':
      document.getElementById('old_token_form').style.display = 'block';
      break;
  }
}
);

document.getElementById('id_is_for').addEventListener('change', () => {

  var selectedValue = document.getElementById('id_is_for').value;
  console.log(selectedValue);
  document.getElementById('clear_credit_form').style.display = 'none';
  document.getElementById('reimbursement_form').style.display = 'none';
  document.getElementById('fault_maintanance_form').style.display = 'none';
  document.getElementById('reconnection_form').style.display = 'none';
  document.getElementById('faulty_meter_form').style.display = 'none';
  document.getElementById('recovered_meter_form').style.display = 'none';
  document.getElementById('old_token_form').style.display = 'none';
  switch (selectedValue) {
    case 'Fault Maintenance':
      document.getElementById('fault_maintanance_form').style.display = 'block';
      break;
    case 'Recovered Meter':
      document.getElementById('recovered_meter_form').style.display = 'block';
      break;
    case 'Reconnection':
      document.getElementById('reconnection_form').style.display = 'block';
      break;
  }
}
);

