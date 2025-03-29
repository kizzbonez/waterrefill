document.addEventListener("DOMContentLoaded", function () {
    // Ensure this script runs after Select2 is initialized
    jQuery(document).ready(function ($) {

        document.getElementById('order_form').addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent default submit first
        
            let quantities = $('.field-quantity');
            let hasZero = false;
            let allProductsValid = true;
               // Loop through all product selects
                // $('[name^="order_details-"][name$="-product"]').each(function(index, element) {
                //     const val = $(element).val();
                //     if (!val || val === "") {
                //         alert(`Please select a product in row ${index + 1}`);
                //         allProductsValid = false;
                //         return false; // Break loop early
                //     }
                // });
                // if (!allProductsValid) {
                //     return;
                // }
            quantities.each(function () {
                let value = parseFloat($(this).val());
                if (value === 0) {
                    hasZero = true;
                    return false; // Exit the loop early
                }
            });
        
            if (hasZero) {
                alert('Quantity cannot be 0.');
                return;
            }
        
            // All quantities are valid, submit the form
            this.submit();
        });
        

        $('.add-row').prepend('<td><span id="total-price" style="font-weight:bold">Total Price:</span></td>');
        updateTotalPrice()
        $(".field-product select").each(function () {
            if ($(this).val()) {  // Check if the select has a value
                var selectedText = $(this).find("option:selected").text(); // Get the selected option text
                $(this).addClass("d-none"); // Hide the select field
                $(this).siblings(".select2-container").addClass("d-none"); // Hide the select2 field
                $(this).after('<span class="readonly-label">' + selectedText + '</span>'); // Add a label with the value
            }
        });
        
        function updateTotalPrice() {
            _total_price = $('#total-price');
            field_total_price = $('.field-total_price p');
   
            total_price = 0;
            field_total_price.each(function () {
                total_price += parseFloat($(this).text());
            });
            _total_price.text('Total Price: ' + total_price.toFixed(2));

        }
        $(document).on('select2:select','.field-product', function (e) {
            e.stopPropagation();
            let row = $(this).closest('tr');
            let selectedProductId = $(this).val();

            // Get product prices from the first dropdown (same for all)
            let productPrices = $(this).data('product-prices') || "{}";


            // Get selected product price
            let price = productPrices[selectedProductId] || 0;
            row.data('price', price);

            // Update total price if quantity is already set
            let quantityInput = row.find('.field-quantity input');
            let totalPriceField = row.find('.field-total_price p');
         
            if (quantityInput.length && totalPriceField.length) {
                let quantity = parseFloat(quantityInput.val()) || 0;
                let totalPrice = (quantity * price).toFixed(2);
                totalPriceField.text(totalPrice);
                console.log( totalPrice)
            }
            updateTotalPrice() 
        });

        // Update total price when quantity changes
        $(document).on('input','.field-quantity input', function () {
            let row = $(this).closest('tr');
            
            let quantity = parseFloat($(this).val()) || 0;
            let price = parseFloat(row.data('price')) ||  parseFloat(row.find('.field-current_product_price input').val()) || 0;
            let totalPriceField = row.find('.field-total_price p');
            if (totalPriceField.length) {

                let totalPrice = (quantity * price).toFixed(2);
                totalPriceField.text(totalPrice);
            }
            updateTotalPrice() 
        });
    });
});
