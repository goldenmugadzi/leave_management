$(document).ready(function() {
    // Open modal on button click
    $("#open-modal").click(function() {
        $("#modal").show();
    });

    // Close modal on close button click
    $("#close-modal").click(function() {
        $("#modal").hide();
    });

    // Submit form data via AJAX
    $("#upload-form").submit(function(e) {
        e.preventDefault();

        var formData = new FormData(this);

        $.ajax({
            url: "/pettycash/receipt", // Replace with your actual URL
            type: "POST",
            data: formData,
            contentType: false,
            processData: false,
            success: function(response) {
                // Handle successful response
                console.log("Success:", response);
                $("#upload-form").trigger("reset"); // Reset form after submission
                $("#modal").hide();
            },
            error: function(error) {
                // Handle error response
                console.error("Error:", error);
            }
        });
    });
});