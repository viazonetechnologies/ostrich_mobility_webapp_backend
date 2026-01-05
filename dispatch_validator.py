"""
Dispatch Data Validation Module
Provides comprehensive validation for dispatch operations
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional

class DispatchValidator:
    """Comprehensive validation for dispatch data"""
    
    # Valid status values
    VALID_STATUSES = ['pending', 'assigned', 'in_transit', 'delivered', 'cancelled']
    
    # Phone number regex pattern
    PHONE_PATTERN = re.compile(r'^[\+]?[1-9][\d]{0,15}$')
    
    # Vehicle number patterns (Indian format)
    VEHICLE_PATTERNS = [
        re.compile(r'^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$'),  # Standard format
        re.compile(r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{1,4}$'),  # Flexible format
    ]
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_dispatch_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate complete dispatch data
        Returns: {
            'is_valid': bool,
            'errors': List[str],
            'warnings': List[str],
            'cleaned_data': Dict[str, Any]
        }
        """
        self.errors = []
        self.warnings = []
        cleaned_data = {}
        
        # Validate customer
        customer_validation = self._validate_customer_id(data.get('customer_id'))
        if customer_validation['error']:
            self.errors.append(customer_validation['error'])
        else:
            cleaned_data['customer_id'] = customer_validation['value']
        
        # Validate product (optional)
        if data.get('product_id'):
            product_validation = self._validate_product_id(data.get('product_id'))
            if product_validation['error']:
                self.errors.append(product_validation['error'])
            else:
                cleaned_data['product_id'] = product_validation['value']
        
        # Validate driver information
        driver_validation = self._validate_driver_info(
            data.get('driver_name'), 
            data.get('driver_phone')
        )
        if driver_validation['errors']:
            self.errors.extend(driver_validation['errors'])
        if driver_validation['warnings']:
            self.warnings.extend(driver_validation['warnings'])
        cleaned_data.update(driver_validation['cleaned_data'])
        
        # Validate vehicle information
        vehicle_validation = self._validate_vehicle_info(data.get('vehicle_number'))
        if vehicle_validation['error']:
            self.errors.append(vehicle_validation['error'])
        if vehicle_validation['warning']:
            self.warnings.append(vehicle_validation['warning'])
        cleaned_data['vehicle_number'] = vehicle_validation['value']
        
        # Validate dates
        date_validation = self._validate_dates(
            data.get('dispatch_date'),
            data.get('estimated_delivery')
        )
        if date_validation['errors']:
            self.errors.extend(date_validation['errors'])
        if date_validation['warnings']:
            self.warnings.extend(date_validation['warnings'])
        cleaned_data.update(date_validation['cleaned_data'])
        
        # Validate status
        status_validation = self._validate_status(data.get('status'))
        cleaned_data['status'] = status_validation['value']
        if status_validation['warning']:
            self.warnings.append(status_validation['warning'])
        
        # Validate optional fields
        cleaned_data.update(self._validate_optional_fields(data))
        
        return {
            'is_valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'cleaned_data': cleaned_data
        }
    
    def _validate_customer_id(self, customer_id: Any) -> Dict[str, Any]:
        """Validate customer ID"""
        if not customer_id:
            return {'error': 'Customer ID is required', 'value': None}
        
        if str(customer_id).lower() in ['none', 'null', '']:
            return {'error': 'Customer ID cannot be None or empty', 'value': None}
        
        try:
            customer_id = int(customer_id)
            if customer_id <= 0:
                return {'error': 'Customer ID must be a positive number', 'value': None}
            return {'error': None, 'value': customer_id}
        except (ValueError, TypeError):
            return {'error': 'Customer ID must be a valid number', 'value': None}
    
    def _validate_product_id(self, product_id: Any) -> Dict[str, Any]:
        """Validate product ID (optional)"""
        if not product_id:
            return {'error': None, 'value': None}
        
        try:
            product_id = int(product_id)
            if product_id <= 0:
                return {'error': 'Product ID must be a positive number', 'value': None}
            return {'error': None, 'value': product_id}
        except (ValueError, TypeError):
            return {'error': 'Product ID must be a valid number', 'value': None}
    
    def _validate_driver_info(self, driver_name: str, driver_phone: str) -> Dict[str, Any]:
        """Validate driver information"""
        errors = []
        warnings = []
        cleaned_data = {}
        
        # Validate driver name
        if not driver_name or not driver_name.strip():
            errors.append('Driver name is required')
        else:
            driver_name = driver_name.strip()
            if len(driver_name) < 2:
                errors.append('Driver name must be at least 2 characters long')
            elif len(driver_name) > 100:
                warnings.append('Driver name is unusually long')
                driver_name = driver_name[:100]
            
            # Check for valid characters
            if not re.match(r'^[a-zA-Z\s\.]+$', driver_name):
                warnings.append('Driver name contains unusual characters')
            
            cleaned_data['driver_name'] = driver_name
        
        # Validate driver phone (optional but recommended)
        if driver_phone:
            driver_phone = re.sub(r'[^\d\+]', '', driver_phone.strip())
            if not self.PHONE_PATTERN.match(driver_phone):
                warnings.append('Driver phone number format may be invalid')
            cleaned_data['driver_phone'] = driver_phone
        else:
            warnings.append('Driver phone number not provided')
            cleaned_data['driver_phone'] = None
        
        return {
            'errors': errors,
            'warnings': warnings,
            'cleaned_data': cleaned_data
        }
    
    def _validate_vehicle_info(self, vehicle_number: str) -> Dict[str, Any]:
        """Validate vehicle information"""
        if not vehicle_number or not vehicle_number.strip():
            return {
                'error': 'Vehicle number is required',
                'warning': None,
                'value': None
            }
        
        vehicle_number = vehicle_number.strip().upper()
        
        # Check minimum length
        if len(vehicle_number) < 4:
            return {
                'error': 'Vehicle number must be at least 4 characters long',
                'warning': None,
                'value': None
            }
        
        # Check for valid Indian vehicle number format
        is_valid_format = any(pattern.match(vehicle_number) for pattern in self.VEHICLE_PATTERNS)
        
        warning = None
        if not is_valid_format:
            warning = 'Vehicle number format may not follow standard Indian format'
        
        return {
            'error': None,
            'warning': warning,
            'value': vehicle_number
        }
    
    def _validate_dates(self, dispatch_date: str, estimated_delivery: str) -> Dict[str, Any]:
        """Validate dispatch and delivery dates"""
        errors = []
        warnings = []
        cleaned_data = {}
        
        current_date = datetime.now().date()
        
        # Validate dispatch date
        if dispatch_date:
            try:
                if '1970' in str(dispatch_date) or 'GMT' in str(dispatch_date):
                    warnings.append('Invalid dispatch date detected, using current date')
                    cleaned_data['dispatch_date'] = current_date.strftime('%Y-%m-%d')
                else:
                    parsed_date = datetime.strptime(dispatch_date, '%Y-%m-%d').date()
                    
                    # Check if date is too far in the past
                    if parsed_date < current_date - timedelta(days=365):
                        warnings.append('Dispatch date is more than a year in the past')
                    
                    # Check if date is too far in the future
                    if parsed_date > current_date + timedelta(days=30):
                        warnings.append('Dispatch date is more than 30 days in the future')
                    
                    cleaned_data['dispatch_date'] = parsed_date.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                warnings.append('Invalid dispatch date format, using current date')
                cleaned_data['dispatch_date'] = current_date.strftime('%Y-%m-%d')
        else:
            cleaned_data['dispatch_date'] = current_date.strftime('%Y-%m-%d')
        
        # Validate estimated delivery date
        if estimated_delivery:
            try:
                if '1970' in str(estimated_delivery) or 'GMT' in str(estimated_delivery):
                    warnings.append('Invalid estimated delivery date, calculating from dispatch date')
                    dispatch_dt = datetime.strptime(cleaned_data['dispatch_date'], '%Y-%m-%d').date()
                    cleaned_data['estimated_delivery'] = (dispatch_dt + timedelta(days=2)).strftime('%Y-%m-%d')
                else:
                    parsed_delivery = datetime.strptime(estimated_delivery, '%Y-%m-%d').date()
                    dispatch_dt = datetime.strptime(cleaned_data['dispatch_date'], '%Y-%m-%d').date()
                    
                    # Check if delivery is before dispatch
                    if parsed_delivery < dispatch_dt:
                        errors.append('Estimated delivery date cannot be before dispatch date')
                    
                    # Check if delivery is too far in the future
                    if parsed_delivery > dispatch_dt + timedelta(days=30):
                        warnings.append('Estimated delivery is more than 30 days after dispatch')
                    
                    cleaned_data['estimated_delivery'] = parsed_delivery.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                warnings.append('Invalid estimated delivery date format')
                dispatch_dt = datetime.strptime(cleaned_data['dispatch_date'], '%Y-%m-%d').date()
                cleaned_data['estimated_delivery'] = (dispatch_dt + timedelta(days=2)).strftime('%Y-%m-%d')
        else:
            # Auto-calculate estimated delivery (2 days from dispatch)
            dispatch_dt = datetime.strptime(cleaned_data['dispatch_date'], '%Y-%m-%d').date()
            cleaned_data['estimated_delivery'] = (dispatch_dt + timedelta(days=2)).strftime('%Y-%m-%d')
        
        return {
            'errors': errors,
            'warnings': warnings,
            'cleaned_data': cleaned_data
        }
    
    def _validate_status(self, status: str) -> Dict[str, Any]:
        """Validate dispatch status"""
        if not status:
            return {'value': 'pending', 'warning': 'Status not provided, defaulting to pending'}
        
        status = status.lower().strip()
        if status not in self.VALID_STATUSES:
            return {
                'value': 'pending',
                'warning': f'Invalid status "{status}", defaulting to pending. Valid statuses: {", ".join(self.VALID_STATUSES)}'
            }
        
        return {'value': status, 'warning': None}
    
    def _validate_optional_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate optional fields"""
        cleaned_data = {}
        
        # Tracking notes
        tracking_notes = data.get('tracking_notes', '').strip()
        if tracking_notes and len(tracking_notes) > 1000:
            tracking_notes = tracking_notes[:1000]
            self.warnings.append('Tracking notes truncated to 1000 characters')
        cleaned_data['tracking_notes'] = tracking_notes or None
        
        # Dispatch number (auto-generated if not provided)
        dispatch_number = data.get('dispatch_number', '').strip()
        if dispatch_number and len(dispatch_number) > 50:
            dispatch_number = dispatch_number[:50]
            self.warnings.append('Dispatch number truncated to 50 characters')
        cleaned_data['dispatch_number'] = dispatch_number or None
        
        return cleaned_data
    
    def validate_update_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for dispatch updates (less strict)"""
        self.errors = []
        self.warnings = []
        cleaned_data = {}
        
        # For updates, most fields are optional
        if 'status' in data:
            status_validation = self._validate_status(data['status'])
            cleaned_data['status'] = status_validation['value']
            if status_validation['warning']:
                self.warnings.append(status_validation['warning'])
        
        if 'actual_delivery' in data:
            try:
                if data['actual_delivery']:
                    parsed_date = datetime.strptime(data['actual_delivery'], '%Y-%m-%d').date()
                    cleaned_data['actual_delivery'] = parsed_date.strftime('%Y-%m-%d')
                else:
                    cleaned_data['actual_delivery'] = None
            except (ValueError, TypeError):
                self.errors.append('Invalid actual delivery date format')
        
        if 'tracking_notes' in data:
            tracking_notes = data['tracking_notes'].strip() if data['tracking_notes'] else ''
            if len(tracking_notes) > 1000:
                tracking_notes = tracking_notes[:1000]
                self.warnings.append('Tracking notes truncated to 1000 characters')
            cleaned_data['tracking_notes'] = tracking_notes
        
        # Validate driver info if provided
        if 'driver_name' in data or 'driver_phone' in data:
            driver_validation = self._validate_driver_info(
                data.get('driver_name'), 
                data.get('driver_phone')
            )
            if driver_validation['errors']:
                self.errors.extend(driver_validation['errors'])
            if driver_validation['warnings']:
                self.warnings.extend(driver_validation['warnings'])
            cleaned_data.update(driver_validation['cleaned_data'])
        
        # Validate vehicle info if provided
        if 'vehicle_number' in data:
            vehicle_validation = self._validate_vehicle_info(data['vehicle_number'])
            if vehicle_validation['error']:
                self.errors.append(vehicle_validation['error'])
            if vehicle_validation['warning']:
                self.warnings.append(vehicle_validation['warning'])
            cleaned_data['vehicle_number'] = vehicle_validation['value']
        
        return {
            'is_valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'cleaned_data': cleaned_data
        }

class DispatchDataCleaner:
    """Utility class for cleaning existing dispatch data"""
    
    @staticmethod
    def clean_existing_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean a list of existing dispatch records"""
        validator = DispatchValidator()
        cleaned_records = []
        
        for record in records:
            validation_result = validator.validate_dispatch_data(record)
            
            # Use cleaned data even if there are warnings
            cleaned_record = record.copy()
            cleaned_record.update(validation_result['cleaned_data'])
            
            # Add validation metadata
            cleaned_record['_validation_errors'] = validation_result['errors']
            cleaned_record['_validation_warnings'] = validation_result['warnings']
            cleaned_record['_is_valid'] = validation_result['is_valid']
            
            cleaned_records.append(cleaned_record)
        
        return cleaned_records
    
    @staticmethod
    def get_data_quality_report(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a data quality report for dispatch records"""
        total_records = len(records)
        if total_records == 0:
            return {'total_records': 0, 'quality_score': 100}
        
        validator = DispatchValidator()
        valid_records = 0
        total_errors = 0
        total_warnings = 0
        error_types = {}
        warning_types = {}
        
        for record in records:
            validation_result = validator.validate_dispatch_data(record)
            
            if validation_result['is_valid']:
                valid_records += 1
            
            # Count errors by type
            for error in validation_result['errors']:
                total_errors += 1
                error_types[error] = error_types.get(error, 0) + 1
            
            # Count warnings by type
            for warning in validation_result['warnings']:
                total_warnings += 1
                warning_types[warning] = warning_types.get(warning, 0) + 1
        
        quality_score = (valid_records / total_records) * 100
        
        return {
            'total_records': total_records,
            'valid_records': valid_records,
            'invalid_records': total_records - valid_records,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'quality_score': round(quality_score, 2),
            'error_breakdown': error_types,
            'warning_breakdown': warning_types,
            'recommendations': DispatchDataCleaner._generate_recommendations(error_types, warning_types)
        }
    
    @staticmethod
    def _generate_recommendations(error_types: Dict[str, int], warning_types: Dict[str, int]) -> List[str]:
        """Generate recommendations based on common errors and warnings"""
        recommendations = []
        
        if 'Customer ID is required' in error_types:
            recommendations.append('Ensure all dispatch records have valid customer IDs')
        
        if 'Driver name is required' in error_types:
            recommendations.append('Implement driver name validation at data entry')
        
        if 'Vehicle number is required' in error_types:
            recommendations.append('Make vehicle number a mandatory field')
        
        if any('date' in error.lower() for error in error_types):
            recommendations.append('Implement proper date validation and formatting')
        
        if any('phone' in warning.lower() for warning in warning_types):
            recommendations.append('Consider implementing phone number format validation')
        
        if any('vehicle number format' in warning.lower() for warning in warning_types):
            recommendations.append('Consider implementing Indian vehicle number format validation')
        
        return recommendations