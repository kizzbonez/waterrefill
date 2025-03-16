document.addEventListener("DOMContentLoaded", function () {
    // Ensure this script runs after Select2 is initialized
    jQuery(document).ready(function ($) {

        $('.add-row').prepend('<td><span id="total-price" style="font-weight:bold">Total Price:</span></td>');

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
            console.log(row.attr('data-price'))
            
            let quantity = parseFloat($(this).val()) || 0;
            let price = parseFloat(row.data('price')) || 0;
            let totalPriceField = row.find('.field-total_price p');
            if (totalPriceField.length) {
                let totalPrice = (quantity * price).toFixed(2);
                totalPriceField.text(totalPrice);
            }
            updateTotalPrice() 
        });
    });
});
