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
                if (response && response.success) {
                    if (response.redirect) {
                        window.location.href = response.redirect;
                    } else {
                        window.location.reload();
                    }
                } else {
                    alert((response && response.error) ? response.error : 'Unexpected response');
                }
            },
            error: function(xhr) {
                try {
                    const data = JSON.parse(xhr.responseText);
                    alert(data.error || 'Something went wrong');
                } catch(e) {
                    alert('Something went wrong');
                }
            }
        });
    });
});