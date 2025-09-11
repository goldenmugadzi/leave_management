// Wrap in a function to handle missing elements gracefully
document.addEventListener('DOMContentLoaded', function() {
    const classificationElement = document.getElementById('id_classification');
    if (!classificationElement) {
        // Element doesn't exist on this page, exit gracefully
        return;
    }
    
    classificationElement.addEventListener('change', function() {
        const selectedValue = this.value;
        // project fields
        const field1 = document.getElementById('id_present_tariff');
        const field2 = document.getElementById('id_present_fmc');
        const field3 = document.getElementById('id_capital_contribution');
        const field4 = document.getElementById('id_materials');
        const field5 = document.getElementById('id_connection_fee');
        const field6 = document.getElementById('id_labour');
        const field7 = document.getElementById('id_transport');

        // Only proceed if all required fields exist
        const fields = [field1, field2, field3, field4, field5, field6, field7];
        const missingFields = fields.filter(field => !field);
        if (missingFields.length > 0) {
            console.warn('Some fields are missing for classification functionality');
            return;
        }

        // hide these fields if the value Internal is selected
        if (selectedValue === 'Internal') {
            field1.style.display = 'none';
            field2.style.display = 'none';
            field3.style.display = 'none';
            field4.style.display = 'none';
            field5.style.display = 'none';
            field6.style.display = 'none';
            field7.style.display = 'none';
        } else {
            field1.style.display = 'block';
            field2.style.display = 'block';
            field3.style.display = 'block';
            field4.style.display = 'block';
            field5.style.display = 'block';
            field6.style.display = 'block';
            field7.style.display = 'block';
        }
    });
});
