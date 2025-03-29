document.addEventListener("DOMContentLoaded", function () {

    jQuery(document).ready(function ($) {
        $('#id_amount').on('input', function () {
            var amount = parseFloat($(this).val()) || 0;
            var amountToPay = parseFloat($('#id_amount_to_pay').val()) || 0;
            var balance = amountToPay - amount;
            $('#id_balance_amount').val(balance.toFixed(2));
        });

        document.getElementById('payment_form').addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent default submit first
        
            let balance = parseFloat($('#id_balance_amount').val());
            let amount = parseFloat($('#id_amount').val());
        
            if (isNaN(balance) || isNaN(amount)) {
                alert('Invalid amount or balance');
                return;
            }
            if (amount == 0) {
                alert('Amount cannot be zero');
                return;
            }
            if (balance < 0 ) {
                alert('Amount to pay cannot be more than balance amount');
                return;
            }
        
            // If valid, submit the form manually
            this.submit();
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
                        $('#id_amount').attr('max', parseFloat(response.amount_to_pay).toFixed(2));
                    }else{
                        $('#id_amount_to_pay').val(parseFloat(0.00).toFixed(2));
                        $('#id_amount').attr('max', parseFloat(0.00).toFixed(2));
                    }
                },
                error: function (xhr) {
                    console.error("Error fetching amount to pay:", xhr.responseText);
                }
            });
        });
    });

});