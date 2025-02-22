$(document).ready(function () {
    // Listen for form submission
    $("#forecast_demand button").on('click',function (event) {
        _this = $(this)
        // Get values from form inputs
        let productId = $("#product_id").val();
        let startDate = $("#start_date_prod").val();
        let endDate = $("#end_date_prod").val();
        console.log()
        // Call the function and handle the returned Promise
        getForecastData(startDate, endDate, productId, 'product')
            .then((result) => {
                _this.parents('form').siblings('h2:first').html(`${(Number(result.forecasts[0][0].forecast) || 0).toFixed(2)} - MAPE(${(Number(result.forecasts[0][0].mape) || 0).toFixed(2)})`
            );
                // You can update the UI here with `result`
            })
            .catch((error) => {
                console.error(" Failed to fetch forecast:", error);
            });
    });

    $("#forecast_sales button").on('click',function (event) {
        _this = $(this)
        // Get values from form inputs

        let startDate = $("#start_date").val();
        let endDate = $("#end_date").val();
        // Call the function and handle the returned Promise
        getForecastData(startDate, endDate, null, 'sales')
            .then((result) => {
                _this.parents('form').siblings('h2:first').html(`₱${(Number(result.forecasts[0].forecast) || 0).toFixed(2)} - MAPE(${(Number(result.forecasts[0].mape) || 0).toFixed(2)})`
            );
                // You can update the UI here with `result`
            })
            .catch((error) => {
                console.error(" Failed to fetch forecast:", error);
            });
    });
    

    function getForecastData(start_date, end_date, product_id, type) {
        return new Promise((resolve, reject) => {
            // Ensure dates are in the correct order
            if (new Date(start_date) > new Date(end_date)) {
                console.warn("⚠️ start_date is later than end_date. Swapping them...");
                [start_date, end_date] = [end_date, start_date]; // Swap the values
            }
    
            // Construct API URL
            let apiUrl = `/admin-api/forecast-product?start_date=${start_date}&end_date=${end_date}&type=${type}`;
            if (product_id) {
                apiUrl += `&product_id=${product_id}`;
            }
    
            // Make the AJAX GET request
            $.ajax({
                url: apiUrl,
                type: "GET",
                dataType: "json",
                success: function (data, textStatus, xhr) {
                    if (xhr.status === 200) {
                        resolve(data);  // Return the data when successful
                    } else {
                        reject(new Error(`Unexpected status: ${xhr.status}`));
                    }
                },
                error: function (xhr, status, error) {
                    reject(new Error(`Error: ${xhr.status} - ${error}`));
                }
            });
        });
    }
    
});
