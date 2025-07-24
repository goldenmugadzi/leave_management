/**
 * Enhanced Asset Number Management
 * Provides a modern, user-friendly interface for managing asset numbers
 */

class AssetNumberManager {
    constructor() {
        this.assetCounter = 0;
        this.validAssets = new Set();
        this.invalidAssets = new Set();
        this.debounceTimer = null;
        this.currentAceId = null;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeTabs();
        this.updateCounter();
    }

    bindEvents() {
        // Tab switching
        $(document).on('click', '.tab-btn', (e) => {
            this.switchTab($(e.target).data('tab'));
        });

        // Dynamic field management
        $(document).on('click', '#add-asset-field', () => {
            this.addAssetField();
        });

        $(document).on('click', '.remove-asset-field', (e) => {
            this.removeAssetField($(e.target).closest('.asset-field-group'));
        });

        // Real-time validation
        $(document).on('input', '.asset-input-field', (e) => {
            this.handleAssetInput($(e.target));
        });

        $(document).on('focus', '.asset-input-field', (e) => {
            this.showSuggestions($(e.target));
        });

        $(document).on('blur', '.asset-input-field', (e) => {
            // Delay hiding to allow clicking on suggestions
            setTimeout(() => {
                $(e.target).siblings('.asset-suggestions').hide();
            }, 200);
        });

        // Suggestion clicking
        $(document).on('click', '.asset-suggestion', (e) => {
            this.selectSuggestion($(e.target));
        });

        // Form submission
        $(document).on('submit', '#enhanced-asset-form', (e) => {
            e.preventDefault();
            this.submitIndividualForm();
        });

        // Bulk operations
        $(document).on('click', '#process-bulk', () => {
            this.processBulkEntry();
        });

        $(document).on('click', '#clear-bulk', () => {
            $('#bulk-asset-input').val('');
        });

        // File import
        $(document).on('change', '#asset-file-input', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });

        $(document).on('click', '#process-file', () => {
            this.processFileImport();
        });

        // Utility buttons
        $(document).on('click', '#clear-all', () => {
            this.clearAllFields();
        });

        $(document).on('click', '#view-existing-btn', () => {
            this.toggleExistingAssets();
        });

        $(document).on('click', '#migrate-legacy-btn', (e) => {
            this.migrateLegacyAssets($(e.target).data('ace-id'));
        });
    }

    initializeTabs() {
        $('.tab-content').hide();
        $('#individual-tab').show();
        $('.tab-btn').removeClass('active');
        $('[data-tab="individual"]').addClass('active');
    }

    switchTab(tabName) {
        $('.tab-content').hide();
        $('.tab-btn').removeClass('active');
        
        $(`#${tabName}-tab`).show();
        $(`[data-tab="${tabName}"]`).addClass('active');
    }

    addAssetField() {
        const fieldCount = $('.asset-field-group').length + 1;
        const fieldHtml = `
            <div class="asset-field-group mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">Asset Number ${fieldCount}:</label>
                <div class="relative">
                    <input type="text" class="asset-input-field" name="asset_number[]" 
                           placeholder="Enter or search for asset number..." 
                           autocomplete="off">
                    <button type="button" class="remove-asset-field absolute right-3 top-3 text-red-500 hover:text-red-700">
                        ✕
                    </button>
                    <div class="asset-suggestions" style="display: none;"></div>
                </div>
            </div>
        `;
        
        $('#asset-fields-container').append(fieldHtml);
        this.updateCounter();
    }

    removeAssetField($fieldGroup) {
        if ($('.asset-field-group').length > 1) {
            const assetValue = $fieldGroup.find('.asset-input-field').val();
            this.validAssets.delete(assetValue);
            this.invalidAssets.delete(assetValue);
            
            $fieldGroup.remove();
            this.updateCounter();
            this.updateValidationCounts();
        }
    }

    async handleAssetInput($input) {
        const value = $input.val().trim();
        const $container = $input.closest('.asset-field-group');
        
        // Clear previous validation
        $container.find('.validation-icon').remove();
        
        if (value.length < 2) {
            $input.siblings('.asset-suggestions').hide();
            return;
        }

        // Show loading state
        $input.after('<span class="validation-icon checking">?</span>');

        // Debounce the validation
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(async () => {
            await this.validateAssetNumber($input, value);
            await this.fetchSuggestions($input, value);
        }, 300);
    }

    async validateAssetNumber($input, value) {
        try {
            // Mock validation - replace with actual API call
            const isValid = await this.checkAssetExists(value);
            const $container = $input.closest('.asset-field-group');
            
            $container.find('.validation-icon').remove();
            
            if (isValid) {
                $input.after('<span class="validation-icon valid">✓</span>');
                this.validAssets.add(value);
                this.invalidAssets.delete(value);
            } else {
                $input.after('<span class="validation-icon invalid">!</span>');
                this.invalidAssets.add(value);
                this.validAssets.delete(value);
            }
            
            this.updateValidationCounts();
            
        } catch (error) {
            console.error('Validation error:', error);
        }
    }

    async checkAssetExists(assetNumber) {
        // This would call your actual validation API
        // For now, simulate random validation
        return new Promise(resolve => {
            setTimeout(() => {
                // Simple validation: check if it's a reasonable asset number format
                const isValidFormat = /^[A-Z0-9]{6,15}$/i.test(assetNumber);
                resolve(isValidFormat);
            }, 100);
        });
    }

    async fetchSuggestions($input, query) {
        try {
            const response = await $.ajax({
                url: '/ace/asset_autocomplete_api/',
                data: { q: query },
                method: 'GET'
            });

            this.displaySuggestions($input, response.results || []);
        } catch (error) {
            console.error('Error fetching suggestions:', error);
        }
    }

    displaySuggestions($input, suggestions) {
        const $suggestionsContainer = $input.siblings('.asset-suggestions');
        
        if (suggestions.length === 0) {
            $suggestionsContainer.hide();
            return;
        }

        const suggestionsHtml = suggestions.map(suggestion => `
            <div class="asset-suggestion ${suggestion.verified ? 'verified' : 'unverified'}" 
                 data-value="${suggestion.id}">
                <div class="flex items-center justify-between">
                    <span class="font-medium">${suggestion.text}</span>
                    <span class="text-xs px-2 py-1 rounded ${suggestion.verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                        ${suggestion.verified ? 'Verified' : 'Unverified'}
                    </span>
                </div>
                <div class="text-xs text-gray-500 mt-1">${suggestion.source}</div>
            </div>
        `).join('');

        $suggestionsContainer.html(suggestionsHtml).show();
    }

    selectSuggestion($suggestion) {
        const value = $suggestion.data('value');
        const $input = $suggestion.closest('.relative').find('.asset-input-field');
        
        $input.val(value);
        $suggestion.parent().hide();
        
        // Trigger validation
        this.handleAssetInput($input);
    }

    showSuggestions($input) {
        const value = $input.val().trim();
        if (value.length >= 2) {
            this.fetchSuggestions($input, value);
        }
    }

    async submitIndividualForm() {
        const $form = $('#enhanced-asset-form');
        const formData = new FormData($form[0]);
        
        // Show progress
        this.showProgress(0);
        
        try {
            const response = await $.ajax({
                url: '/ace/enhanced_add_asset_number/',
                method: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                xhr: () => {
                    const xhr = new window.XMLHttpRequest();
                    xhr.upload.addEventListener("progress", (evt) => {
                        if (evt.lengthComputable) {
                            const percentComplete = (evt.loaded / evt.total) * 100;
                            this.showProgress(percentComplete);
                        }
                    }, false);
                    return xhr;
                }
            });

            this.showToast('Asset numbers added successfully!', 'success');
            setTimeout(() => {
                location.reload();
            }, 1500);

        } catch (error) {
            this.showToast('Error adding asset numbers: ' + (error.responseText || 'Unknown error'), 'error');
        } finally {
            this.hideProgress();
        }
    }

    processBulkEntry() {
        const bulkText = $('#bulk-asset-input').val().trim();
        if (!bulkText) {
            this.showToast('Please enter some asset numbers', 'warning');
            return;
        }

        // Parse bulk input (support both line-separated and comma-separated)
        let assetNumbers = [];
        
        if (bulkText.includes('\n')) {
            assetNumbers = bulkText.split('\n').map(line => line.trim()).filter(line => line);
        } else if (bulkText.includes(',')) {
            assetNumbers = bulkText.split(',').map(item => item.trim()).filter(item => item);
        } else {
            assetNumbers = [bulkText];
        }

        // Clear existing fields and add new ones
        this.clearAllFields();
        
        assetNumbers.forEach((assetNumber, index) => {
            if (index > 0) {
                this.addAssetField();
            }
            $('.asset-input-field').eq(index).val(assetNumber);
            this.handleAssetInput($('.asset-input-field').eq(index));
        });

        // Switch to individual tab
        this.switchTab('individual');
        this.showToast(`Processed ${assetNumbers.length} asset numbers`, 'success');
    }

    handleFileSelect(file) {
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            const content = e.target.result;
            this.processFileContent(content, file.name);
        };

        if (file.name.endsWith('.csv') || file.name.endsWith('.txt')) {
            reader.readAsText(file);
        } else {
            this.showToast('File format not supported yet. Please use CSV or TXT files.', 'warning');
        }
    }

    processFileContent(content, filename) {
        // Simple CSV/TXT parsing
        const lines = content.split('\n').map(line => line.trim()).filter(line => line);
        const assetNumbers = [];

        lines.forEach(line => {
            if (line.includes(',')) {
                // CSV format
                const values = line.split(',').map(val => val.trim().replace(/"/g, ''));
                assetNumbers.push(...values.filter(val => val && val.length > 3));
            } else {
                // Simple text format
                if (line.length > 3) {
                    assetNumbers.push(line);
                }
            }
        });

        if (assetNumbers.length > 0) {
            $('#bulk-asset-input').val(assetNumbers.join('\n'));
            this.showToast(`Found ${assetNumbers.length} asset numbers in ${filename}`, 'success');
        } else {
            this.showToast('No valid asset numbers found in file', 'warning');
        }
    }

    processFileImport() {
        const content = $('#bulk-asset-input').val();
        if (content) {
            this.processBulkEntry();
        } else {
            this.showToast('Please select and process a file first', 'warning');
        }
    }

    clearAllFields() {
        $('#asset-fields-container').html(`
            <div class="asset-field-group mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">Asset Number 1:</label>
                <div class="relative">
                    <input type="text" class="asset-input-field" name="asset_number[]" 
                           placeholder="Enter or search for asset number..." 
                           autocomplete="off">
                    <div class="asset-suggestions" style="display: none;"></div>
                </div>
            </div>
        `);
        
        this.validAssets.clear();
        this.invalidAssets.clear();
        this.updateCounter();
        this.updateValidationCounts();
    }

    toggleExistingAssets() {
        $('#existing-assets').slideToggle();
    }

    async migrateLegacyAssets(aceId) {
        if (!confirm('This will migrate your existing asset numbers to the enhanced format. Continue?')) {
            return;
        }

        try {
            await $.ajax({
                url: `/ace/migrate_ace_assets/${aceId}/`,
                method: 'GET'
            });

            this.showToast('Legacy assets migrated successfully!', 'success');
            setTimeout(() => {
                location.reload();
            }, 1500);

        } catch (error) {
            this.showToast('Migration failed: ' + (error.responseText || 'Unknown error'), 'error');
        }
    }

    updateCounter() {
        const count = $('.asset-field-group').length;
        $('#asset-counter').text(`${count} asset${count !== 1 ? 's' : ''}`);
        this.assetCounter = count;
    }

    updateValidationCounts() {
        $('#valid-count').text(this.validAssets.size);
        $('#invalid-count').text(this.invalidAssets.size);
    }

    showProgress(percentage) {
        $('.progress-bar').show();
        $('.progress-fill').css('width', percentage + '%');
    }

    hideProgress() {
        $('.progress-bar').hide();
    }

    showToast(message, type = 'success') {
        const $toast = $(`<div class="toast ${type}">${message}</div>`);
        $('body').append($toast);

        setTimeout(() => {
            $toast.fadeOut(() => $toast.remove());
        }, 3000);
    }
}

// Initialize when document is ready
$(document).ready(() => {
    new AssetNumberManager();
});

// Legacy support for existing modals
$(document).ready(function() {
    // Keep existing modal functionality for backward compatibility
    $("#asset_number_btn").click(function() {
        $("#asset_number_modal").show();
    });

    $("#close-modal").click(function() {
        $("#asset_number_modal").hide();
        location.reload();
    });

    // Enhanced legacy form submission
    $("#asset_upload").submit(function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const $submitBtn = $(this).find('button[type="submit"]');
        const originalText = $submitBtn.text();
        
        $submitBtn.text('Adding...').prop('disabled', true);

        $.ajax({
            url: "/ace/add_asset_number/",
            type: "POST",
            data: formData,
            contentType: false,
            processData: false,
            success: function(response) {
                // Show success message
                const toast = new AssetNumberManager();
                toast.showToast('Asset numbers added successfully!', 'success');
                
                setTimeout(() => {
                    $("#asset_number_modal").hide();
                    location.reload();
                }, 1500);
            },
            error: function(xhr, status, error) {
                const toast = new AssetNumberManager();
                toast.showToast('Error: ' + (xhr.responseText || error), 'error');
            },
            complete: function() {
                $submitBtn.text(originalText).prop('disabled', false);
            }
        });
    });
});
