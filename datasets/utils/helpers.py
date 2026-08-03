import random
import string
import re
from datetime import datetime, timedelta
import numpy as np

def generate_gst_number(country, state_index, settings):
    """Generate country-specific realistic tax identifier matching the regex pattern."""
    geo = settings.GEOGRAPHY_MAPPING.get(country)
    if not geo:
        return "N/A"
    
    pattern = geo.get("tax_format")
    if not pattern:
        return "N/A"
    
    # Generate based on country rules
    if country == "India":
        # Format: 27[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}
        pan_chars = "".join(random.choices(string.ascii_uppercase, k=5))
        pan_nums = "".join(random.choices(string.digits, k=4))
        pan_suffix = random.choice(string.ascii_uppercase)
        entity_num = random.choice("123456789")
        check_char = random.choice(string.ascii_uppercase + string.digits)
        state_code = f"{27 + state_index:02d}"
        return f"{state_code}{pan_chars}{pan_nums}{pan_suffix}{entity_num}Z{check_char}"
        
    elif country == "China":
        # Format: 91[0-9A-Z]{16}
        chars = "".join(random.choices(string.ascii_uppercase + string.digits, k=16))
        return f"91{chars}"
        
    elif country == "Germany":
        # Format: DE[0-9]{9}
        nums = "".join(random.choices(string.digits, k=9))
        return f"DE{nums}"
        
    elif country == "Japan":
        # Format: T[0-9]{13}
        nums = "".join(random.choices(string.digits, k=13))
        return f"T{nums}"
        
    elif country == "USA":
        # Format: [0-9]{2}-[0-9]{7}
        part1 = "".join(random.choices(string.digits, k=2))
        part2 = "".join(random.choices(string.digits, k=7))
        return f"{part1}-{part2}"
        
    elif country == "UK":
        # Format: GB[0-9]{9}
        nums = "".join(random.choices(string.digits, k=9))
        return f"GB{nums}"
        
    elif country == "France":
        # Format: FR[A-Z0-9]{2}[0-9]{9}
        chars = "".join(random.choices(string.ascii_uppercase + string.digits, k=2))
        nums = "".join(random.choices(string.digits, k=9))
        return f"FR{chars}{nums}"
        
    elif country == "Italy":
        # Format: IT[0-9]{11}
        nums = "".join(random.choices(string.digits, k=11))
        return f"IT{nums}"
        
    elif country == "Brazil":
        # Format: [0-9]{2}\.[0-9]{3}\.[0-9]{3}/0001-[0-9]{2}
        n1 = "".join(random.choices(string.digits, k=2))
        n2 = "".join(random.choices(string.digits, k=3))
        n3 = "".join(random.choices(string.digits, k=3))
        n4 = "".join(random.choices(string.digits, k=2))
        return f"{n1}.{n2}.{n3}/0001-{n4}"
        
    else:
        # Default placeholder matching general lengths
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=12))

def generate_container_number():
    """Generate realistic ISO 6346 container number (4 letters, 6 digits, 1 check digit)."""
    prefix = "".join(random.choices(string.ascii_uppercase, k=3)) + "U"
    serial = "".join(random.choices(string.digits, k=6))
    
    # Calculate check digit
    char_vals = {c: i + 10 + (i // 10) for i, c in enumerate(string.ascii_uppercase)}
    for d in string.digits:
        char_vals[d] = int(d)
        
    full_str = prefix + serial
    total = sum(char_vals[char] * (2 ** idx) for idx, char in enumerate(full_str))
    check_digit = (total % 11) % 10
    
    return f"{prefix}{serial}-{check_digit}"

def generate_phone_number(country):
    """Generate a realistic phone number based on country prefix."""
    prefixes = {
        "India": "+91 98", "China": "+86 13", "Germany": "+49 17",
        "Japan": "+81 90", "South Korea": "+82 10", "Vietnam": "+84 9",
        "Thailand": "+66 8", "USA": "+1 212", "Canada": "+1 416",
        "UK": "+44 79", "France": "+33 6", "Italy": "+39 34",
        "Turkey": "+90 53", "UAE": "+971 50", "Australia": "+61 4",
        "Brazil": "+55 11"
    }
    prefix = prefixes.get(country, "+1 555")
    suffix = "".join(random.choices(string.digits, k=8))
    return f"{prefix} {suffix[:4]}-{suffix[4:]}"

def generate_email(name, domain="carbonledger-simulation.com"):
    """Clean name and generate a valid email."""
    clean_name = re.sub(r"[^a-zA-Z0-9]", "", name).lower()
    return f"{clean_name[:15]}@{domain}"

def get_seasonal_date_distribution(start_year=2023, end_year=2026, count=1000):
    """Generate dates between 2023 and 2026 with realistic business seasonality.
    - Q4 Procurement Spikes (higher density in Oct-Dec)
    - Q1 Slowdowns (lower density in Jan-Feb)
    """
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    total_days = (end_date - start_date).days
    
    # Generate weights for each month
    # Standard month weights (1.0 is average). Q4 has higher weights, Q1 has lower weights.
    month_weights = {
        1: 0.7,  2: 0.8,  3: 1.0, 
        4: 1.0,  5: 0.9,  6: 0.95, 
        7: 1.0,  8: 1.0,  9: 1.1, 
        10: 1.3, 11: 1.4, 12: 1.5
    }
    
    dates = []
    # Vectorized calculation for rapid date selection
    daily_weights = []
    for day_offset in range(total_days + 1):
        cur_date = start_date + timedelta(days=day_offset)
        daily_weights.append(month_weights[cur_date.month])
        
    daily_weights = np.array(daily_weights)
    daily_weights = daily_weights / daily_weights.sum()
    
    chosen_offsets = np.random.choice(total_days + 1, size=count, p=daily_weights)
    return [start_date + timedelta(days=int(offset)) for offset in chosen_offsets]

def get_seasonal_utility_load(date_val, plant_country):
    """Simulates monthly electricity & water utility seasonality.
    - Summer AC spikes (July/August in Northern hemisphere, Jan/Feb in Southern hemisphere)
    - Winter heating spikes (Jan/Dec in Northern hemisphere)
    """
    month = date_val.month
    
    # Southern hemisphere countries
    southern_countries = ["Australia", "Brazil"]
    is_southern = plant_country in southern_countries
    
    if is_southern:
        # Summer: Dec, Jan, Feb. Winter: June, July, Aug.
        if month in [12, 1, 2]:
            factor = 1.35 # Summer AC peak
        elif month in [6, 7, 8]:
            factor = 1.15 # Winter heating peak
        else:
            factor = 0.90 # Mild shoulder seasons
    else:
        # Northern hemisphere
        if month in [7, 8]:
            factor = 1.40 # Summer cooling peak
        elif month in [12, 1]:
            factor = 1.25 # Winter heating peak
        else:
            factor = 0.85 # Mild shoulder seasons
            
    # Add random operational variance (±10%)
    factor *= random.uniform(0.9, 1.1)
    return factor

def get_logistics_delay(transport_mode, country, date_val):
    """Monsoon delay simulator for logistics.
    - Monsoon months in South/Southeast Asia (June-August) cause significant road/rail delays.
    - Winter blizzards in Northern countries (December-February) cause road/air delays.
    """
    month = date_val.month
    delay = 0.0
    
    # Monsoon regions
    monsoon_countries = ["India", "Vietnam", "Thailand"]
    # Cold winter regions
    cold_countries = ["Germany", "Canada", "UK", "France", "USA"]
    
    if country in monsoon_countries and month in [6, 7, 8]:
        if transport_mode == "Road":
            delay = random.uniform(2.0, 12.0) # Flooded roads
        elif transport_mode == "Rail":
            delay = random.uniform(1.0, 6.0)
            
    elif country in cold_countries and month in [12, 1, 2]:
        if transport_mode == "Road":
            delay = random.uniform(3.0, 15.0) # Snow storms
        elif transport_mode == "Air":
            delay = random.uniform(4.0, 24.0) # Flight cancellations
            
    # Normal background noise delay
    if delay == 0.0:
        if random.random() < 0.15: # 15% chance of typical minor delays
            delay = random.uniform(0.5, 3.0)
            
    return round(delay, 2)
