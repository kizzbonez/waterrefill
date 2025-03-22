import pandas as pd
from django.http import HttpResponse
from django.utils.timezone import make_aware
from datetime import datetime
from orders.models import Order, OrderDetails
from django.db.models import Sum
from products.models import Product
from admin_portal.models import CustomUser
from django.db.models import Sum, Count

def generate_sales_report(request):
    """Generate Sales Report for a Given Date Range and Download as Excel."""
    # Get date range from request parameters (YYYY-MM-DD format)
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')

    try:
        start_date = make_aware(datetime.strptime(start_date_str, "%Y-%m-%d"))
        end_date = make_aware(datetime.strptime(end_date_str, "%Y-%m-%d"))
    except ValueError:
        return HttpResponse("Invalid date format. Use YYYY-MM-DD", status=400)

    # Fetch orders within the date range
    orders = Order.objects.filter(created_at__range=[start_date, end_date])

    # Prepare data for export
    report_data = []

    for order in orders:
        order_details = OrderDetails.objects.filter(order=order)
        for item in order_details:
            report_data.append({
                "Date Per Day": order.created_at.strftime("%B %d, %Y"),
                "Order No.": order.id,
                "Customer Name": f"{order.customer.first_name} {order.customer.last_name}" if order.customer else "N/A",
                "Product": item.product.name if item.product else "Unknown",
                "Qty": item.quantity,
                "Item Amount": item.current_product_price,
                "Total Amount": item.total_price,
            })

    # Convert data to a Pandas DataFrame
    df = pd.DataFrame(report_data)

    # Add Grand Total Row
    if not df.empty:
        total_sum = df["Total Amount"].sum()
        df.loc[len(df)] = ["", "", "", "Grand Total", "", "", total_sum]

    # Create HTTP response for Excel download
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="sales_report_{start_date_str}_to_{end_date_str}.xlsx"'

    # Write DataFrame to Excel
    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Sales Report", index=False)

    return response
def generate_top_customers_report(request):
    """Generate an Excel report of Top 10 Customers with separate sheets showing products they bought"""

    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')

    try:
        start_date = make_aware(datetime.strptime(start_date_str, "%Y-%m-%d"))
        end_date = make_aware(datetime.strptime(end_date_str, "%Y-%m-%d"))
    except ValueError:
        return HttpResponse("Invalid date format. Use YYYY-MM-DD", status=400)

    # Aggregate top 10 customers based on total sales
    top_customers = Order.objects.filter(created_at__range=[start_date, end_date], customer__isnull=False) \
        .values('customer__id', 'customer__first_name', 'customer__last_name') \
        .annotate(total_sales=Sum('order_details__total_price')) \
        .order_by('-total_sales')[:10]  

    # Convert to DataFrame
    df_top_customers = pd.DataFrame(list(top_customers))

    # Rename columns
    df_top_customers.rename(columns={
        'customer__first_name': 'First Name',
        'customer__last_name': 'Last Name',
        'total_sales': 'Total Sales'
    }, inplace=True)

    # Create HTTP response for Excel download
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="top_customers_{start_date_str}_to_{end_date_str}.xlsx"'

    # Write to Excel
    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        # Write Top Customers Summary
        df_top_customers.to_excel(writer, sheet_name="Top Customers", index=False)

        # Add individual sheets per customer
        for customer in top_customers:
            customer_id = customer["customer__id"]
            customer_name = f"{customer['customer__first_name']} {customer['customer__last_name']}"

            # Get products bought by this customer in the date range
            customer_orders = OrderDetails.objects.filter(
                order__customer_id=customer_id, 
                order__created_at__range=[start_date, end_date]
            ).values(
                'product__name'
            ).annotate(
                total_quantity=Sum('quantity'),
                total_spent=Sum('total_price')
            )

            # Convert to DataFrame
            df_customer = pd.DataFrame(list(customer_orders))

            if not df_customer.empty:
                df_customer.rename(columns={
                    'product__name': 'Product',
                    'total_quantity': 'Quantity Purchased',
                    'total_spent': 'Total Spent'
                }, inplace=True)

                # Append Grand Total row
                grand_total = df_customer["Total Spent"].sum()
                df_customer.loc[len(df_customer)] = ["Grand Total", "", grand_total]

                # Write customer-specific sheet
                safe_sheet_name = customer_name[:31]  # Excel sheet names have a 31-character limit
                df_customer.to_excel(writer, sheet_name=safe_sheet_name, index=False)

    return response


def generate_top_products_report(request):
    """Generate an Excel report of Top 10 Products with separate sheets showing order details with dates"""

    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')

    try:
        start_date = make_aware(datetime.strptime(start_date_str, "%Y-%m-%d"))
        end_date = make_aware(datetime.strptime(end_date_str, "%Y-%m-%d"))
    except ValueError:
        return HttpResponse("Invalid date format. Use YYYY-MM-DD", status=400)

    # Aggregate top 10 products based on total quantity sold
    top_products = OrderDetails.objects.filter(order__created_at__range=[start_date, end_date]) \
        .values('product__id', 'product__name') \
        .annotate(
            total_quantity=Sum('quantity'),
            total_sales=Sum('total_price')
        ) \
        .order_by('-total_quantity')[:10]  # Get top 10 products

    # Convert to DataFrame
    df_top_products = pd.DataFrame(list(top_products))

    # Rename columns
    df_top_products.rename(columns={
        'product__name': 'Product Name',
        'total_quantity': 'Total Quantity Sold',
        'total_sales': 'Total Sales (₱)'
    }, inplace=True)

    # Create HTTP response for Excel download
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="top_products_{start_date_str}_to_{end_date_str}.xlsx"'

    # Write to Excel
    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        # Write Top Products Summary
        df_top_products.to_excel(writer, sheet_name="Top Products", index=False)

        # Add individual sheets per product
        for product in top_products:
            product_id = product["product__id"]
            product_name = product["product__name"]

            # Get orders that included this product in the date range
            product_orders = OrderDetails.objects.filter(
                product_id=product_id, 
                order__created_at__range=[start_date, end_date]
            ).values(
                'order__id', 
                'order__created_at',
                'order__customer__first_name', 
                'order__customer__last_name', 
                'quantity', 
                'total_price'
            )

            # Convert to DataFrame
            df_product_orders = pd.DataFrame(list(product_orders))

            if not df_product_orders.empty:
                df_product_orders.rename(columns={
                    'order__id': 'Order ID',
                    'order__created_at': 'Order Date',
                    'order__customer__first_name': 'First Name',
                    'order__customer__last_name': 'Last Name',
                    'quantity': 'Quantity Purchased',
                    'total_price': 'Total Spent'
                }, inplace=True)

                # Format date
                df_product_orders['Order Date'] = pd.to_datetime(df_product_orders['Order Date']).dt.strftime('%Y-%m-%d')

                # Append Grand Total row
                grand_total = df_product_orders["Total Spent"].sum()
                df_product_orders.loc[len(df_product_orders)] = ["", "Grand Total", "", "", "", grand_total]

                # Write product-specific sheet
                safe_sheet_name = product_name[:31]  # Excel sheet names have a 31-character limit
                df_product_orders.to_excel(writer, sheet_name=safe_sheet_name, index=False)

    return response

    return response
def generate_inventory_report(request):
    """Generate and Download Inventory Report"""

    # Fetch all products
    products = Product.objects.all()

    # Prepare data for export
    report_data = []

    for product in products:
        report_data.append({
            "Product Name": product.name,
            "Stock Available": product.stock,
            "Stock Alert Level": product.stock_alert_level,
            "Status": "Low Stock" if product.stock <= product.stock_alert_level else "In Stock",
        })

    # Convert data to Pandas DataFrame
    df = pd.DataFrame(report_data)

    # Create HTTP response for Excel download
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="inventory_report.xlsx"'

    # Write DataFrame to Excel
    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Inventory Report", index=False)

    return response