google.charts.load('current', {packages:["orgchart"]});
function getRoles(e) {
    const form = e.target.closest('form');
    const appId = form.querySelector('input[name="app_id"]').value;
    const userId = form.querySelector('input[name="user_id"]').value;
    $.ajax({
        type: "GET",
        url: `/users/getroles?app_id=${appId}&user_id=${userId}`,
        success: function(rdata) {
            // console.log(data);
            
            document.getElementById('rolesModalBody').innerHTML =rdata.form;
            $('#rolesModal').modal('show');
            
       data.addColumn('string', 'Name');
       data.addColumn('string', 'Manager');
       data.addColumn('string', 'ToolTip');
       response = rdata.regioncc_list;
       console.log(response);
            for (row in response){
                data.addRow([{'v':response[row].id, 'f':'<button type="button" onclick="assignCostCenter('+response[row].id+')">'+response[row].name+' <div style="color:red; font-style:italic">'+response[row].code+'</div></button>'}, response[row].parent, response[row].parent]);
   
            }
          var chartc = new google.visualization.OrgChart(document.getElementById('cc_chart_div'));
          chartc.draw(data, {'allowHtml': true});
         },
        error: function(xhr, status, error) {
            document.getElementById('rolesModalBody').innerHTML =xhr.responseText;
            console.error('Error:', error);
            console.log(xhr.responseText);
        }
    });
}