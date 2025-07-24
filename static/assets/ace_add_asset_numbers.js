$(document).ready(function() {
    console.log("ACE Asset Numbers JS loaded");
    
    // Check if elements exist
    console.log("Button exists:", $("#asset_number_btn").length > 0);
    console.log("Modal exists:", $("#asset_number_modal").length > 0);
    console.log("Form exists:", $("#asset_upload").length > 0);
    console.log("Close button exists:", $("#close-modal").length > 0);
    
    // Open modal on button click
    $("#asset_number_btn").click(function(e) {
        e.preventDefault();
        console.log("Button clicked!");
        $("#asset_number_modal").show();
        return false;
    });

    // Close modal on close button click
    $("#close-modal").click(function() {
        console.log("Close button clicked");
        $("#asset_number_modal").hide();
    });

    // Submit form data via AJAX
    $("#asset_upload").submit(function(e) {
        e.preventDefault();
        console.log("Form submitted");

        var formData = new FormData(this);

        $.ajax({
            url: "/ace/add_asset_number/", // Correct URL path
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                alert("Asset numbers added successfully!");
                $("#asset_number_modal").hide();
                location.reload();
            },
            error: function(xhr, status, error) {
                alert("Error adding asset numbers: " + error);
                console.log("AJAX error:", xhr.responseText);
            }
        });
    });
});