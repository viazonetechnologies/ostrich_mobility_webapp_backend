"""
Dispatch Management Utility
Handles dispatch data validation, correction, and management
"""

from datetime import datetime, timedelta
import re
import json

class DispatchDataManager:
    def __init__(self):
        self.valid_statuses = ['pending', 'assigned', 'in_transit', 'delivered', 'cancelled']
    
    def validate_dispatch_record(self, record):
        """Validate a single dispatch record and return issues found"""
        issues = []
        suggestions = {}
        
        # Check customer ID
        customer_id = record.get('customer_id')
        if not customer_id or customer_id == 'None' or customer_id == 'null':
            issues.append("Customer ID is missing or invalid")
            suggestions['customer_id'] = "Assign to default customer or get valid customer ID"
        
        # Check product ID
        product_id = record.get('product_id')
        if product_id and str(product_id).isdigit():
            suggestions['product_id'] = int(product_id)
        elif product_id:
            issues.append("Product ID is not a valid number")
        
        # Check driver information
        driver = record.get('driver_name', '').strip()
        if not driver or len(driver) < 3 or self._contains_garbage(driver):
            issues.append("Driver name is missing, too short, or contains invalid characters")
            suggestions['driver_name'] = "Driver TBD"
        else:
            suggestions['driver_name'] = self._clean_text(driver)
        
        # Check vehicle information
        vehicle = record.get('vehicle_number', '').strip()
        if not vehicle or len(vehicle) < 4 or self._contains_garbage(vehicle):
            issues.append("Vehicle number is missing, too short, or contains invalid characters")
            suggestions['vehicle_number'] = "Vehicle TBD"
        else:
            suggestions['vehicle_number'] = self._clean_text(vehicle)
        
        # Check dates
        dispatch_date = record.get('dispatch_date')
        if self._is_invalid_date(dispatch_date):
            issues.append("Dispatch date is invalid or from 1970")
            suggestions['dispatch_date'] = datetime.now().strftime('%Y-%m-%d')
        
        estimated_delivery = record.get('estimated_delivery')
        if self._is_invalid_date(estimated_delivery):
            issues.append("Estimated delivery date is invalid")
            suggestions['estimated_delivery'] = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        
        # Check status
        status = record.get('status', '').lower()
        if status not in self.valid_statuses:
            issues.append(f"Status '{status}' is not valid")
            suggestions['status'] = 'pending'
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _contains_garbage(self, text):
        """Check if text contains garbage characters"""
        if not text:
            return True
        
        # Check for common garbage patterns
        garbage_patterns = [
            r'^[a-z]{4}$',  # Like 'szda'
            r'^[a-z]{4}\s+[a-z]{4}$',  # Like 'szda adsg'
            r'[^a-zA-Z0-9\s\-]',  # Non-alphanumeric except spaces and hyphens
        ]
        
        for pattern in garbage_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _clean_text(self, text):
        """Clean text by removing invalid characters"""
        if not text:
            return ""
        
        # Remove non-alphanumeric characters except spaces and hyphens
        cleaned = re.sub(r'[^a-zA-Z0-9\s\-]', '', text)
        # Remove extra spaces
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()
    
    def _is_invalid_date(self, date_str):
        """Check if date is invalid (1970, malformed, etc.)"""
        if not date_str:
            return True
        
        date_str = str(date_str)
        
        # Check for 1970 dates
        if '1970' in date_str:
            return True
        
        # Check for GMT format dates (usually malformed)
        if 'GMT' in date_str:
            return True
        
        # Try to parse as date
        try:
            parsed_date = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d')
            # Check if date is before 2020 (likely invalid)
            if parsed_date.year < 2020:
                return True
        except:
            return True
        
        return False
    
    def fix_dispatch_record(self, record):
        """Fix a dispatch record based on validation results"""
        validation = self.validate_dispatch_record(record)
        
        if validation['is_valid']:
            return record
        
        # Apply suggestions
        fixed_record = record.copy()
        for key, value in validation['suggestions'].items():
            fixed_record[key] = value
        
        return fixed_record
    
    def generate_dispatch_number(self, dispatch_id):
        """Generate a dispatch number for a given ID"""
        return f"DSP{dispatch_id:06d}"
    
    def format_dispatch_for_display(self, record):
        """Format dispatch record for display"""
        formatted = {
            'dispatch_number': record.get('dispatch_number', f"DSP{record.get('id', 0):06d}"),
            'customer': self._format_customer(record),
            'product': self._format_product(record),
            'driver': record.get('driver_name', 'TBD'),
            'vehicle': record.get('vehicle_number', 'TBD'),
            'status': record.get('status', 'pending').upper(),
            'dispatch_date': self._format_date(record.get('dispatch_date')),
            'estimated_delivery': self._format_date(record.get('estimated_delivery')),
            'actual_delivery': self._format_date(record.get('actual_delivery'))
        }
        
        return formatted
    
    def _format_customer(self, record):
        """Format customer information"""
        customer_id = record.get('customer_id')
        customer_name = record.get('customer_name')
        
        if customer_name and customer_name != 'Unknown Customer':
            return customer_name
        elif customer_id:
            return f"Customer ID: {customer_id}"
        else:
            return "Unknown Customer"
    
    def _format_product(self, record):
        """Format product information"""
        product_id = record.get('product_id')
        product_name = record.get('product_name')
        
        if product_name and product_name != 'Unknown Product':
            return product_name
        elif product_id:
            return f"Product ID: {product_id}"
        else:
            return "No Product"
    
    def _format_date(self, date_str):
        """Format date for display"""
        if not date_str:
            return "Not Set"
        
        try:
            if isinstance(date_str, str):
                # Handle different date formats
                if 'T' in date_str:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            else:
                date_obj = date_str
            
            return date_obj.strftime('%d %b %Y')
        except:
            return str(date_str)

# Example usage and test data
def test_dispatch_manager():
    """Test the dispatch manager with sample problematic data"""
    manager = DispatchDataManager()
    
    # Sample problematic dispatch record (like the one you provided)
    problematic_record = {
        'id': 1,
        'dispatch_number': 'DSP000001',
        'customer_id': 'None',
        'product_id': '2',
        'driver_name': 'szda adsg',
        'vehicle_number': '',
        'status': 'pending',
        'dispatch_date': '8/1/2026',
        'estimated_delivery': '1/1/1970',
        'actual_delivery': 'SAT, 03 JAN 2026 05:32:00 GMT'
    }
    
    print("Original Record:")
    print(json.dumps(problematic_record, indent=2))
    
    print("\nValidation Results:")
    validation = manager.validate_dispatch_record(problematic_record)
    print(f"Is Valid: {validation['is_valid']}")
    print("Issues:")
    for issue in validation['issues']:
        print(f"  - {issue}")
    
    print("\nFixed Record:")
    fixed_record = manager.fix_dispatch_record(problematic_record)
    print(json.dumps(fixed_record, indent=2))
    
    print("\nFormatted for Display:")
    formatted = manager.format_dispatch_for_display(fixed_record)
    print(json.dumps(formatted, indent=2))

if __name__ == "__main__":
    test_dispatch_manager()