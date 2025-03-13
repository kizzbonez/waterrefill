document.addEventListener("DOMContentLoaded", function () {

    jQuery(document).ready(function ($) {
        $('#id_amount').on('input', function () {
            var amount = parseFloat($(this).val()) || 0;
            var amountToPay = parseFloat($('#id_amount_to_pay').val()) || 0;
            var balance = amountToPay - amount;
            $('#id_balance_amount').val(balance.toFixed(2));
        });

        $('#id_order_id').on('select2:select', function (e) {
            var selectedValue = $(this).val();
            console.log("Selected Value:", selectedValue);
            $.ajax({
                url: '/admin/payments/payment/get-amount-to-pay/',  // Use your correct Django admin AJAX URL
                type: 'GET',
                data: { order_id: selectedValue },
                success: function (response) {
                    if (response.amount_to_pay) {
                        $('#id_amount_to_pay').val(parseFloat(response.amount_to_pay).toFixed(2));
                    }else{
                        $('#id_amount_to_pay').val(parseFloat(0.00).toFixed(2));
                    }
                },
                error: function (xhr) {
                    console.error("Error fetching amount to pay:", xhr.responseText);
                }
            });
        });
    });

});