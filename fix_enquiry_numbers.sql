-- Fix enquiry numbers to use sequential format
-- This script will update all timestamp-based enquiry numbers to sequential format

-- First, let's see what we have
SELECT id, enquiry_number, customer_id, created_at 
FROM enquiries 
ORDER BY id;

-- Update all enquiry numbers to sequential format based on ID
UPDATE enquiries 
SET enquiry_number = CONCAT('ENQ', LPAD(id, 6, '0'))
WHERE enquiry_number IS NULL 
   OR enquiry_number NOT LIKE 'ENQ%' 
   OR LENGTH(enquiry_number) != 9
   OR enquiry_number REGEXP '^ENQ[0-9]{10,}$';

-- Verify the changes
SELECT id, enquiry_number, customer_id, created_at 
FROM enquiries 
ORDER BY id;

-- Show count of fixed records
SELECT 
    COUNT(*) as total_enquiries,
    COUNT(CASE WHEN enquiry_number LIKE 'ENQ______' THEN 1 END) as proper_format,
    COUNT(CASE WHEN enquiry_number NOT LIKE 'ENQ______' THEN 1 END) as needs_fixing
FROM enquiries;