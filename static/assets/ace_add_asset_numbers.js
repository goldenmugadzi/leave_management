$(document).ready(function() {
    // Open modal on button click
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
            url: "/ace/add_asset_number", // Replace with your actual URL
            type: "POST",
            data: formData,
            contentType: false,
            processData: false,
            success: function(response) {
                // Handle successful response
                console.log("Success:", response);
                $("#upload-form").trigger("reset"); // Reset form after submission
                $("#modal").hide();
                location.reload();
            },
            error: function(error) {
                // Handle error response
                console.error("Error:", error);
            }
        });
    });
});