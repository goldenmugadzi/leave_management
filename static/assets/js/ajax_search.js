<script>
  $(document).ready(function(){" "}
  {$("#search-input").on("keyup", function () {
    var query = $(this).val();
    $.ajax({
      url: '{% url "search_purchase_requests" %}',
      data: { query: query },
      dataType: "json",
      success: function (data) {
        // Clear previous results
        $("#search-results").empty();
        // Append new results
        alert("data received successfully");
        $.each(data, function (index, item) {
          var row =
            '<tr class="h-1">' +
            '<td><a class="text-blue-500" href="{% url \'purchase_request:purchase_request_detail\' item.id %}">' +
            item.id +
            "</a>" +
            '<a class="text-red-400" href="{% url \'purchase_request:purchase_request_update\' item.id %}"><i class="fas fa-edit mr-2"></i></a></td>' +
            "<td>" +
            item.created_at +
            "</td>" +
            "<td>" +
            item.scope_of_work +
            "</td>" +
            "<td>" +
            (item.requested_by == user
              ? "You"
              : item.requested_by.get_full_name) +
            "</td>" +
            "<td>" +
            item.section +
            "</td>" +
            "<td>" +
            item.cost_center.name +
            "</td>" +
            "<td>" +
            item.procurement_plan_reference +
            "</td>" +
            "<td>" +
            item.ace +
            "</td>" +
            "</tr>";
          $("#nonconformity tbody").append(row);
        });
      },
    });
  })}
  );
</script>;
