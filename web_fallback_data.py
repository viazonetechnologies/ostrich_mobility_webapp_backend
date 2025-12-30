"""
Enhanced Web App Fallback Data Integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_fallback_data import *
from datetime import datetime, timedelta
import random

class WebAppData:
    def __init__(self):
        self.users = USERS_DATA
        self.customers = CUSTOMERS_DATA
        self.products = PRODUCTS_DATA
        self.sales = SALES_DATA
        self.services = SERVICES_DATA
        self.regions = REGIONS_DATA
        
    def get_user_by_username(self, username):
        return next((u for u in self.users if u["username"] == username), None)
    
    def get_users_by_role(self, role=None, region=None):
        users = self.users
        if role:
            users = [u for u in users if u["role"] == role]
        if region:
            users = [u for u in users if u["region"] == region]
        return users
    
    def get_customers_by_type(self, customer_type=None, region=None):
        customers = self.customers
        if customer_type:
            customers = [c for c in customers if c["customer_type"] == customer_type]
        if region:
            customers = [c for c in customers if c["region"] == region]
        return customers
    
    def get_products_by_category(self, category=None):
        if category:
            return [p for p in self.products if p["category"] == category]
        return self.products
    
    def get_sales_summary(self, filters=None):
        sales = self.sales
        
        if filters:
            if filters.get("start_date"):
                sales = [s for s in sales if s["sale_date"] >= filters["start_date"]]
            if filters.get("end_date"):
                sales = [s for s in sales if s["sale_date"] <= filters["end_date"]]
            if filters.get("customer_type"):
                sales = [s for s in sales if s["customer_type"] == filters["customer_type"]]
            if filters.get("region"):
                sales = [s for s in sales if s["region"] == filters["region"]]
            if filters.get("sales_executive_id"):
                sales = [s for s in sales if s["sales_executive_id"] == int(filters["sales_executive_id"])]
            if filters.get("product_id"):
                sales = [s for s in sales if s["product_id"] == int(filters["product_id"])]
        
        # Calculate summary
        total_sales = len([s for s in sales if s["status"] == "COMPLETED"])
        total_revenue = sum(s["total_amount"] for s in sales if s["status"] == "COMPLETED")
        
        # By customer type
        by_customer_type = {}
        for customer_type in ["b2c", "b2b", "b2g"]:
            type_sales = [s for s in sales if s["customer_type"] == customer_type and s["status"] == "COMPLETED"]
            by_customer_type[customer_type] = {
                "count": len(type_sales),
                "revenue": sum(s["total_amount"] for s in type_sales)
            }
        
        # By products
        by_products = {}
        for sale in sales:
            if sale["status"] == "COMPLETED":
                product = next((p for p in self.products if p["id"] == sale["product_id"]), None)
                if product:
                    product_name = product["name"]
                    if product_name not in by_products:
                        by_products[product_name] = {"count": 0, "revenue": 0}
                    by_products[product_name]["count"] += sale["quantity"]
                    by_products[product_name]["revenue"] += sale["total_amount"]
        
        return {
            "total_sales": total_sales,
            "total_revenue": total_revenue,
            "by_customer_type": by_customer_type,
            "by_products": by_products
        }
    
    def get_sales_details(self, filters=None):
        sales = self.sales.copy()
        
        if filters:
            if filters.get("start_date"):
                sales = [s for s in sales if s["sale_date"] >= filters["start_date"]]
            if filters.get("end_date"):
                sales = [s for s in sales if s["sale_date"] <= filters["end_date"]]
            if filters.get("customer_type"):
                sales = [s for s in sales if s["customer_type"] == filters["customer_type"]]
            if filters.get("region"):
                sales = [s for s in sales if s["region"] == filters["region"]]
            if filters.get("sales_executive_id"):
                sales = [s for s in sales if s["sales_executive_id"] == int(filters["sales_executive_id"])]
            if filters.get("product_id"):
                sales = [s for s in sales if s["product_id"] == int(filters["product_id"])]
        
        # Enhance with related data
        for sale in sales:
            customer = next((c for c in self.customers if c["id"] == sale["customer_id"]), {})
            product = next((p for p in self.products if p["id"] == sale["product_id"]), {})
            sales_exec = next((u for u in self.users if u["id"] == sale["sales_executive_id"]), {})
            
            sale.update({
                "customer_name": customer.get("contact_person", "Unknown"),
                "product_name": product.get("name", "Unknown Product"),
                "sales_executive_name": f"{sales_exec.get('first_name', '')} {sales_exec.get('last_name', '')}".strip()
            })
        
        return sales
    
    def get_services_summary(self, filters=None):
        services = self.services
        
        if filters:
            if filters.get("start_date"):
                services = [s for s in services if s["created_date"] >= filters["start_date"]]
            if filters.get("end_date"):
                services = [s for s in services if s["created_date"] <= filters["end_date"]]
            if filters.get("region"):
                services = [s for s in services if s["region"] == filters["region"]]
            if filters.get("technician_id"):
                services = [s for s in services if s["technician_id"] == int(filters["technician_id"])]
        
        return {
            "total_services": len(services),
            "completed": len([s for s in services if s["status"] == "COMPLETED"]),
            "in_progress": len([s for s in services if s["status"] == "IN_PROGRESS"]),
            "scheduled": len([s for s in services if s["status"] == "SCHEDULED"]),
            "pending": len([s for s in services if s["status"] == "PENDING"])
        }
    
    def get_dashboard_stats(self, user_role, user_region=None):
        # Filter data based on user role and region
        if user_role == "sales_executive" and user_region:
            sales = [s for s in self.sales if s["region"] == user_region]
            customers = [c for c in self.customers if c["region"] == user_region]
            services = [s for s in self.services if s["region"] == user_region]
        else:
            sales = self.sales
            customers = self.customers
            services = self.services
        
        return {
            "total_customers": len(customers),
            "total_sales": len([s for s in sales if s["status"] == "COMPLETED"]),
            "total_revenue": sum(s["total_amount"] for s in sales if s["status"] == "COMPLETED"),
            "active_services": len([s for s in services if s["status"] in ["SCHEDULED", "IN_PROGRESS"]]),
            "b2c_customers": len([c for c in customers if c["customer_type"] == "b2c"]),
            "b2b_customers": len([c for c in customers if c["customer_type"] == "b2b"]),
            "b2g_customers": len([c for c in customers if c["customer_type"] == "b2g"])
        }

# Initialize web app data
web_app_data = WebAppData()