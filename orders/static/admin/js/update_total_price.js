document.addEventListener("DOMContentLoaded", function () {
    // Ensure this script runs after Select2 is initialized
    jQuery(document).ready(function ($) {
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
        });

        // Update total price when quantity changes
        $(document).on('input','.field-quantity input', function () {
            let row = $(this).closest('tr');
            let quantity = parseFloat($(this).val()) || 0;
            let price = parseFloat(row.data('price')) || 0;
            let totalPriceField = row.find('.field-total_price p');

            if (totalPriceField.length) {
                let totalPrice = (quantity * price).toFixed(2);
                totalPriceField.text(totalPrice);
            }
        });
    });
});
