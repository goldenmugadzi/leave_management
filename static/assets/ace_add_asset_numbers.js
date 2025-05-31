$(document).ready(function() {
    // Open modal on button click
    console.log("Document is ready");
    $("#asset_number_btn").click(function() {
        $("#asset_number_modal").show();
    });

    // Close modal on close button click
    $("#close-modal").click(function() {
        $("#asset_number_modal").hide();
        // reload page after closing modal
        location.reload();
    });

    // Submit form data via AJAX
    $("#asset_upload").submit(function(e) {
        e.preventDefault();

        var formData = new FormData(this);

        $.ajax({
            url: "/ace/add_asset_number/", // Make sure this is the correct URL and view
            type: "POST",
            data: formData,
            contentType: false,
            processData: false,
            headers: {'X-CSRFToken': $("input[name=csrfmiddlewaretoken]").val()},
            success: function(response) {
                // Handle successful response
                console.log("Success:", response);
                $("#asset_upload").trigger("reset"); // Reset the correct form
                alert("Asset numbers added successfully!");
                $("#asset_number_modal").hide();      // Hide the correct modal
                location.reload();
            },
            error: function(error) {
                // Handle error response
                console.error("Error:", error);
                alert("Failed to add asset numbers. Please try again.");
            }
        });
    });
});