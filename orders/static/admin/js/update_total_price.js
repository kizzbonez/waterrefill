document.addEventListener("DOMContentLoaded", function () {
    // Ensure this script runs after Select2 is initialized
    django.jQuery(document).ready(function ($) {
        console.log(  $('.field-product select'))

        $('.field-product').on('select2:select', function (e) {
            console.log("test")
            let row = $(this).closest('tr');
            let selectedProductId = $(this).val();

            // Get product prices from the first dropdown (same for all)
            let productPricesJSON = $(this).data('product-prices') || "{}";
            let productPrices = JSON.parse(productPricesJSON);

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
            }
        });

        // Update total price when quantity changes
        $('.field-quantity input').on('input', function () {
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
