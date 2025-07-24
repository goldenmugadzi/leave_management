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

    // Initialize enhanced asset number functionality
    function initEnhancedAssets() {
        // Only run if enhanced modal exists
        if ($('#enhanced_asset_modal').length === 0) return;
        
        // Initialize Select2 for enhanced asset inputs
        $('.enhanced-asset-select').select2({
            placeholder: 'Search asset numbers...',
            allowClear: true,
            width: '100%',
            ajax: {
                url: '/ace/asset_autocomplete_api/',
                dataType: 'json',
                delay: 250,
                data: function (params) {
                    return { q: params.term };
                },
                processResults: function (data) {
                    return {
                        results: data.results || []
                    };
                },
                cache: true
            },
            templateResult: function(item) {
                if (!item.id) return item.text;
                
                var verified = item.verified ? 'verified' : 'unverified';
                var icon = item.verified ? '✓' : '⚠';
                
                return $(`
                    <div class="asset-option ${verified}">
                        <span class="asset-text">${item.text}</span>
                        <span class="asset-status">${icon}</span>
                    </div>
                `);
            }
        });
    }
    
    // Open enhanced modal
    $('#enhanced_asset_btn').click(function() {
        $('#enhanced_asset_modal').show();
        setTimeout(initEnhancedAssets, 100);
    });
    
    // Add more asset fields
    $('#add_enhanced_field').click(function() {
        var fieldCount = $('.enhanced-asset-field').length;
        var newField = `
            <div class="enhanced-asset-field mb-3">
                <label>Asset Number ${fieldCount + 1}:</label>
                <select class="enhanced-asset-select" name="asset_number[]" style="width: 100%;">
                    <option value=""></option>
                </select>
                <button type="button" class="btn btn-sm btn-danger remove-enhanced-field">Remove</button>
            </div>
        `;
        $('#enhanced_fields_container').append(newField);
        initEnhancedAssets();
    });
    
    // Remove field
    $(document).on('click', '.remove-enhanced-field', function() {
        $(this).closest('.enhanced-asset-field').remove();
    });
    
    // Submit enhanced form
    $('#enhanced_asset_form').submit(function(e) {
        e.preventDefault();
        
        var assetNumbers = [];
        $('.enhanced-asset-select').each(function() {
            var val = $(this).val();
            if (val && val.trim()) {
                assetNumbers.push(val.trim());
            }
        });
        
        if (assetNumbers.length === 0) {
            alert('Please add at least one asset number');
            return;
        }
        
        // Add hidden field to indicate enhanced system
        if ($('input[name="use_enhanced"]').length === 0) {
            $(this).append('<input type="hidden" name="use_enhanced" value="true">');
        }
        
        var formData = new FormData(this);
        
        $.ajax({
            url: '/ace/enhanced_add_asset_number/',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function() {
                $('#enhanced_asset_modal').hide();
                location.reload();
            },
            error: function(xhr) {
                alert('Error: ' + (xhr.responseText || 'Unknown error'));
            }
        });
    });
    
    // Close enhanced modal
    $('#close_enhanced_modal').click(function() {
        $('#enhanced_asset_modal').hide();
    });
    
    // Initialize on page load
    initEnhancedAssets();
});