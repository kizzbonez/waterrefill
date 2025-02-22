import json
import pandas as pd
import numpy as np
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum
from django.db.models.functions import TruncDay
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from products.models import Product  # Ensure Product is imported
from orders.models import OrderDetails, Order  # Ensure OrderDetails is imported
from payments.models import Payment  # Ensure Payment is imported
import traceback

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(staff_member_required, name='dispatch')
class AdminAPI(APIView):
    """Class-based API for Admin-only actions"""

    def get(self, request):
        """Handle GET request"""
        return Response({"message": "Admin-only GET request!"}, status=status.HTTP_200_OK)

    def post(self, request):
        """Handle POST request with automatic status handling"""
        if not request.data:
            return Response({"error": "Request body is empty"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "POST request received!", "data": request.data},
            status=status.HTTP_201_CREATED  # 201 Created
        )


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(staff_member_required, name='dispatch')
class ForecastView(APIView):
    """Class-based API to display product forecast data"""

    def get(self, request):
        """Handle GET request for forecast data"""
        return self._process_forecast_request(request)

    def post(self, request):
        """Handle POST request for forecast data"""
        return self._process_forecast_request(request)

    def _process_forecast_request(self, request):
        """Shared method for GET and POST requests"""
        try:
            start_date = request.GET.get("start_date")
            end_date = request.GET.get("end_date")
            forecast_type = request.GET.get("type")
            product_id = request.GET.get("product_id")  # Fixed: Was using "end_date" instead of "product_id"
            forecast_data = []

            # Ensure forecast_type is provided
            if not forecast_type:
                return Response({"error": "Missing 'type' parameter"}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure product_id is provided
            if not product_id and  forecast_type == "product":
                return Response({"error": "Missing 'product_id' parameter"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate date format
            date_format = "%Y-%m-%d"
            try:
                start_date_fi = datetime.strptime(start_date, date_format) if start_date else timezone.now()
                end_date_fi = datetime.strptime(end_date, date_format) if end_date else timezone.now()
            except ValueError:
                return Response({"error": "Invalid date format, expected YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)

            time_diff_days = (end_date_fi - start_date_fi).days
            if time_diff_days < 0:
                return Response({"error": "End date must be after start date"}, status=status.HTTP_400_BAD_REQUEST)
            elif time_diff_days == 0:
                return Response({"error": "Start and end date cannot be the same"}, status=status.HTTP_400_BAD_REQUEST)
            # Fetch forecast data
            try:
                if forecast_type == "product":
                    forecast_data = [self._calculate_product_forecast(product_id, time_diff_days)  ]
                elif forecast_type == "sales":
                    forecast_data = self._calculate_sales_forecast(time_diff_days)
                else:
                    return Response({"error": "Invalid 'type' parameter"}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Product.DoesNotExist:  # ✅ Handles non-existent product
                 return Response({"error": f"Product with ID {product_id} not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:  # ✅ Catches any unexpected errors
                 print(traceback.format_exc())
                 return Response({"error": "An unexpected error occurred", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                "title": "Product Forecast",
                "forecasts": forecast_data,
                "day_difference": time_diff_days
            }, status=status.HTTP_200_OK)
                    # If forecast_data is empty, return 404 (No sales data found)
            if not forecast_data:
                return Response({"error": "No sales data found for this product"}, status=status.HTTP_404_NOT_FOUND)   
        except Exception as e:
            print(traceback.format_exc())  # Prints full error traceback with line numb
            return Response({"error": "An error occurred", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _calculate_sales_forecast(self, forecast_days=0):
        forecast_results = []
   

        sales_query = Payment.objects.filter(status=1) \
            .annotate(day=TruncDay("created_at")) \
            .values("day") \
            .annotate(total=Sum("amount")) \
            .order_by("day")

        # ✅ Convert to dictionary for fast lookup
        sales_dict = {entry["day"].date(): float(entry["total"]) for entry in sales_query}

        start_date = min(sales_dict.keys())
        today = timezone.now().date()
        all_dates = pd.date_range(start=start_date, end=today, freq="D")
        date_diff = (today - start_date).days
        # ✅ Generate full date range from `start_date` to `today`
 

        # ✅ Fill in missing days with 0 sales
        filled_sales = [{"day": date, "total": sales_dict.get(date.date(), 0)} for date in all_dates]

        # ✅ Extract labels & data for charts
        daily_sales_labels = [entry["day"].strftime("%b %d") for entry in filled_sales]
        daily_sales_data = [entry["total"] for entry in filled_sales]
         # # ✅ Create DataFrame for structured data
        df = pd.DataFrame({"date": all_dates, "sales":   filled_sales})
        # #replace NaN values with 0
        df['sales'] = df['sales'].fillna(0)
        historical_data = df.to_dict(orient="records")
        forecast_sales = self.calculate_wma(daily_sales_data,window_size= date_diff , growth_rate=0.00, forecast_days=forecast_days)
        mape_value = self.calculate_mape(   daily_sales_data,forecast_sales)
        forecast_results.append({
            "historical_sales": historical_data,
            "forecast": sum(forecast_sales),
            "mape": round(mape_value, 2)
        })

        return forecast_results
        return forecast_results
       




    def _calculate_product_forecast(self, product_id=None, forecast_days=0):
        """
        Calculate demand forecast for a selected product using Weighted Moving Average (WMA)
        and compute MAPE against actual sales.
        """
        forecast_results = []
    
        # Get the product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
           raise ValueError(f"Product with ID {product_id} not found")

        # Fetch sales data for the product
        sales_query = OrderDetails.objects.filter(product=product, order__status=4)

       # Fetch sales data and ensure date is formatted correctly
        sales_data = (
            sales_query.annotate(day=TruncDay("order__created_at"))
            .values("day")
            .annotate(total_sold=Sum("quantity"))
            .order_by("day")
        )
       
        sales_data = [
            {"day": entry["day"].date(), "total_sold": float(entry["total_sold"] or 0.0)}
            for entry in sales_data
            if entry["day"] is not None  # Avoid None values
        ]

        # ✅ Convert to dictionary for fast lookup (Ensure correct data types)
        sales_dict = {
            entry["day"]: float(entry.get("total_sold", 0.0))
            for entry in sales_data
            if "day" in entry and entry["day"] is not None
        }
        # ✅ Debug: Print sales_dict to verify structure
        # Should be {date: float, date: float, ...}

        # ✅ Handle case where no sales data is found
        if not sales_dict:
            raise ValueError("No sales data found for this product")

        # ✅ Generate full date range from first sale to today
        start_date = min(sales_dict.keys())
        today = timezone.now().date()
        all_dates = pd.date_range(start=start_date, end=today, freq="D")
        date_diff = (today - start_date).days
        # ✅ Fill in missing days with 0 instead of NaN
        daily_sales = [float(sales_dict.get(date.date(), 0.0)) for date in all_dates]
        
        # # ✅ Create DataFrame for structured data
        df = pd.DataFrame({"date": all_dates, "sales": daily_sales})
        # #replace NaN values with 0
        df['sales'] = df['sales'].fillna(0)
        historical_data = df.to_dict(orient="records")
      
        # Calculate Weighted Moving Average (WMA)
        forecast_demand = self.calculate_wma(daily_sales,window_size= date_diff , growth_rate=0.00, forecast_days=forecast_days)
        mape_value = self.calculate_mape(   daily_sales,forecast_demand)


        forecast_results.append({
            "product": product.name,
            "product_id": product.id,
            "historical_sales": historical_data,
            "forecast": sum(forecast_demand),
            "mape": round(mape_value, 2)
        })

        return forecast_results

    def calculate_wma(self, sales,window_size=0, growth_rate=0.0, forecast_days=0):
        """
        Calculate the Weighted Moving Average (WMA) for the given sales data.
        """
        if not sales or forecast_days == 0:
            return []
        
        weights = np.arange(1, window_size + 1)  # Assign weights (1,2,3,...)
        recent_sales = sales[-window_size:]  # Get last `window_size` sales data
        wma = np.dot(recent_sales, weights) / np.sum(weights)  # Compute WMA 

        forecast_sales = [wma * (1 + growth_rate) ** i for i in range(forecast_days)]
        return forecast_sales

    def calculate_mape(self, actual_sales, forecast_sales):
        """
        Compute the Mean Absolute Percentage Error (MAPE) between actual and forecasted sales.
        """
        errors = [abs((actual - forecast) / actual) * 100 for actual, forecast in zip(actual_sales, forecast_sales) if actual != 0]
        return sum(errors) / len(errors) if errors else 0
