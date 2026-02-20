#!/usr/bin/env python3
"""Test script to verify date parsing"""
import datetime

def format_in_out_date(date_str: str):
    """Format INDATE/OUTDATE as 'DD/MM/YYYY (HH:MM)' and return color based on past/future."""
    if not date_str or len(date_str) < 8:
        return date_str, "#808080"
    
    try:
        year = int(date_str[:4]) if date_str[:4].isdigit() else 2025
        month = int(date_str[4:6]) if date_str[4:6].isdigit() else 1
        day = int(date_str[6:8]) if date_str[6:8].isdigit() else 1
        hour = int(date_str[8:10]) if len(date_str) >= 10 and date_str[8:10].isdigit() else 0
        minute = int(date_str[10:12]) if len(date_str) >= 12 and date_str[10:12].isdigit() else 0
        
        file_date = datetime.datetime(year, month, day, hour, minute)
        now = datetime.datetime.now()
        
        formatted = f"{day:02d}/{month:02d}/{year} ({hour:02d}:{minute:02d})"
        
        if file_date < now:
            color = "#E57373"  # Softer red for past
            status = "PAST"
        else:
            color = "#81C784"  # Softer green for future
            status = "FUTURE"
        
        return formatted, color, status
    except Exception as e:
        return date_str, "#808080", f"ERROR: {e}"

# Test with actual data from example file
test_dates = [
    "202509110000",  # INDATE from example
    "212112310000",  # OUTDATE from example
]

print("Testing date parsing:")
print("=" * 60)
for date_str in test_dates:
    result = format_in_out_date(date_str)
    print(f"Input: {date_str}")
    print(f"Output: {result[0]}")
    print(f"Color: {result[1]}")
    print(f"Status: {result[2]}")
    print("-" * 60)
