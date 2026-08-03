# CarbonLedger Static Reference Data and Settings

# Country mappings with States, Cities, Ports, and Currencies
GEOGRAPHY_MAPPING = {
    "India": {
        "states": ["Maharashtra", "Delhi", "Tamil Nadu", "Karnataka", "West Bengal", "Gujarat"],
        "cities": ["Mumbai", "Delhi", "Chennai", "Bangalore", "Kolkata", "Ahmedabad"],
        "ports": ["Nhava Sheva (JNPT)", "Mundra Port", "Chennai Port"],
        "currency": "INR",
        "tax_label": "GST",
        "tax_format": r"27[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}" # Realistic Indian GST Format
    },
    "China": {
        "states": ["Shanghai", "Guangdong", "Beijing", "Hubei", "Sichuan", "Zhejiang"],
        "cities": ["Shanghai", "Shenzhen", "Guangzhou", "Beijing", "Wuhan", "Ningbo"],
        "ports": ["Shanghai Port", "Shenzhen Port", "Ningbo-Zhoushan Port"],
        "currency": "CNY",
        "tax_label": "USC",
        "tax_format": r"91[0-9A-Z]{16}"
    },
    "Germany": {
        "states": ["Bavaria", "Hesse", "Hamburg", "Berlin", "Baden-Württemberg", "North Rhine-Westphalia"],
        "cities": ["Munich", "Frankfurt", "Hamburg", "Berlin", "Stuttgart", "Cologne"],
        "ports": ["Hamburg Port", "Bremen Port"],
        "currency": "EUR",
        "tax_label": "VAT",
        "tax_format": r"DE[0-9]{9}"
    },
    "Japan": {
        "states": ["Tokyo", "Osaka", "Aichi", "Kanagawa", "Hyogo", "Fukuoka"],
        "cities": ["Tokyo", "Osaka", "Nagoya", "Yokohama", "Kobe", "Fukuoka"],
        "ports": ["Tokyo Port", "Nagoya Port", "Yokohama Port", "Kobe Port"],
        "currency": "JPY",
        "tax_label": "JCT",
        "tax_format": r"T[0-9]{13}"
    },
    "South Korea": {
        "states": ["Seoul", "Gyeonggi", "Busan", "Incheon", "Ulsan"],
        "cities": ["Seoul", "Suwon", "Busan", "Incheon", "Ulsan"],
        "ports": ["Busan Port", "Incheon Port"],
        "currency": "USD", # Standard Transactional Currency
        "tax_label": "VAT",
        "tax_format": r"[0-9]{3}-[0-9]{2}-[0-9]{5}"
    },
    "Vietnam": {
        "states": ["Hanoi", "Ho Chi Minh City", "Da Nang", "Hai Phong"],
        "cities": ["Hanoi", "Ho Chi Minh City", "Da Nang", "Hai Phong"],
        "ports": ["Cat Lai Port", "Hai Phong Port"],
        "currency": "USD",
        "tax_label": "PIT",
        "tax_format": r"[0-9]{10}"
    },
    "Thailand": {
        "states": ["Bangkok", "Chonburi", "Rayong", "Chiang Mai"],
        "cities": ["Bangkok", "Pattaya", "Rayong City", "Chiang Mai"],
        "ports": ["Laem Chabang Port"],
        "currency": "USD",
        "tax_label": "VAT",
        "tax_format": r"0[0-9]{12}"
    },
    "USA": {
        "states": ["New York", "California", "Illinois", "Texas", "Washington", "Florida"],
        "cities": ["New York", "Los Angeles", "Chicago", "Houston", "San Francisco", "Seattle"],
        "ports": ["Port of Los Angeles", "Port of NY/NJ", "Port of Seattle"],
        "currency": "USD",
        "tax_label": "EIN",
        "tax_format": r"[0-9]{2}-[0-9]{7}"
    },
    "Canada": {
        "states": ["Ontario", "British Columbia", "Quebec", "Alberta"],
        "cities": ["Toronto", "Vancouver", "Montreal", "Calgary"],
        "ports": ["Port of Vancouver", "Port of Montreal"],
        "currency": "USD",
        "tax_label": "BN",
        "tax_format": r"[0-9]{9}RC0001"
    },
    "UK": {
        "states": ["England", "Scotland", "Wales", "Northern Ireland"],
        "cities": ["London", "Manchester", "Birmingham", "Glasgow"],
        "ports": ["Port of Felixstowe", "Port of Southampton"],
        "currency": "EUR", # Represented as EUR transactional
        "tax_label": "VAT",
        "tax_format": r"GB[0-9]{9}"
    },
    "France": {
        "states": ["Île-de-France", "Provence-Alpes-Côte d'Azur", "Auvergne-Rhône-Alpes", "Occitanie"],
        "cities": ["Paris", "Marseille", "Lyon", "Toulouse"],
        "ports": ["Port of Marseille", "Port of Le Havre"],
        "currency": "EUR",
        "tax_label": "TVA",
        "tax_format": r"FR[A-Z0-9]{2}[0-9]{9}"
    },
    "Italy": {
        "states": ["Lombardy", "Lazio", "Piedmont", "Liguria", "Friuli-Venezia Giulia"],
        "cities": ["Milan", "Rome", "Turin", "Genoa", "Trieste"],
        "ports": ["Port of Genoa", "Port of Trieste"],
        "currency": "EUR",
        "tax_label": "IVA",
        "tax_format": r"IT[0-9]{11}"
    },
    "Turkey": {
        "states": ["Istanbul", "Izmir", "Ankara", "Bursa"],
        "cities": ["Istanbul", "Izmir", "Ankara", "Bursa"],
        "ports": ["Ambarli Port", "Izmir Port"],
        "currency": "EUR",
        "tax_label": "KDV",
        "tax_format": r"[0-9]{10}"
    },
    "UAE": {
        "states": ["Dubai", "Abu Dhabi", "Sharjah"],
        "cities": ["Dubai", "Abu Dhabi", "Sharjah"],
        "ports": ["Jebel Ali Port", "Khalifa Port"],
        "currency": "USD",
        "tax_label": "TRN",
        "tax_format": r"100[0-9]{12}"
    },
    "Australia": {
        "states": ["New South Wales", "Victoria", "Queensland", "Western Australia"],
        "cities": ["Sydney", "Melbourne", "Brisbane", "Perth"],
        "ports": ["Port of Sydney", "Port of Melbourne"],
        "currency": "USD",
        "tax_label": "ABN",
        "tax_format": r"[0-9]{11}"
    },
    "Brazil": {
        "states": ["São Paulo", "Rio de Janeiro", "São Paulo State", "Rio Grande do Sul"],
        "cities": ["São Paulo", "Rio de Janeiro", "Santos", "Porto Alegre"],
        "ports": ["Port of Santos"],
        "currency": "USD",
        "tax_label": "CNPJ",
        "tax_format": r"[0-9]{2}\.[0-9]{3}\.[0-9]{3}/0001-[0-9]{2}"
    }
}

# Industry to Products Mapping
PRODUCT_TEMPLATES = {
    "Steel": [
        {"name": "Hot Rolled Steel Coil", "material": "Steel", "unit": "ton", "weight_mean": 2500, "cost_mean": 650, "price_mean": 850},
        {"name": "Cold Rolled Steel Sheet", "material": "Steel", "unit": "ton", "weight_mean": 2000, "cost_mean": 750, "price_mean": 980},
        {"name": "Galvanized Steel Plate", "material": "Steel", "unit": "ton", "weight_mean": 1800, "cost_mean": 800, "price_mean": 1050},
        {"name": "Steel Structural Rebar", "material": "Steel", "unit": "ton", "weight_mean": 5000, "cost_mean": 550, "price_mean": 700},
        {"name": "Seamless Carbon Steel Pipe", "material": "Steel", "unit": "ton", "weight_mean": 1200, "cost_mean": 900, "price_mean": 1200}
    ],
    "Aluminium": [
        {"name": "Aluminium Billet 6063", "material": "Aluminium", "unit": "ton", "weight_mean": 1500, "cost_mean": 2100, "price_mean": 2500},
        {"name": "Aluminium Sheet 5052", "material": "Aluminium", "unit": "ton", "weight_mean": 1000, "cost_mean": 2400, "price_mean": 2900},
        {"name": "Aluminium Extrusion Profile", "material": "Aluminium", "unit": "ton", "weight_mean": 800, "cost_mean": 2600, "price_mean": 3200},
        {"name": "Primary Aluminium Ingot", "material": "Aluminium", "unit": "ton", "weight_mean": 2200, "cost_mean": 1900, "price_mean": 2300}
    ],
    "Cement": [
        {"name": "Portland Cement Clinker", "material": "Cement", "unit": "ton", "weight_mean": 10000, "cost_mean": 45, "price_mean": 65},
        {"name": "Bulk Portland Cement CEM I", "material": "Cement", "unit": "ton", "weight_mean": 8000, "cost_mean": 55, "price_mean": 80},
        {"name": "Fly Ash Pozzolanic Cement", "material": "Cement", "unit": "ton", "weight_mean": 8000, "cost_mean": 48, "price_mean": 72},
        {"name": "Masonry Hydrated Lime Sack", "material": "Cement", "unit": "ton", "weight_mean": 2000, "cost_mean": 90, "price_mean": 130}
    ],
    "Chemical": [
        {"name": "Industrial Lubricant Grade A", "material": "Chemical", "unit": "liter", "weight_mean": 0.9, "cost_mean": 1.2, "price_mean": 2.5},
        {"name": "Ethylene Glycol Bulk", "material": "Chemical", "unit": "ton", "weight_mean": 5000, "cost_mean": 600, "price_mean": 850},
        {"name": "Sulfuric Acid 98%", "material": "Chemical", "unit": "ton", "weight_mean": 3000, "cost_mean": 80, "price_mean": 120},
        {"name": "Sodium Hydroxide Caustic Soda", "material": "Chemical", "unit": "ton", "weight_mean": 2000, "cost_mean": 350, "price_mean": 500}
    ],
    "Automobile": [
        {"name": "Automotive Chassis Frame", "material": "Steel", "unit": "pcs", "weight_mean": 320, "cost_mean": 1500, "price_mean": 2200},
        {"name": "Aluminium Alloy Wheel Rim", "material": "Aluminium", "unit": "pcs", "weight_mean": 12, "cost_mean": 45, "price_mean": 85},
        {"name": "Electric Car Battery Module", "material": "Chemical", "unit": "pcs", "weight_mean": 450, "cost_mean": 4500, "price_mean": 6500},
        {"name": "Combustion Engine Block 2.0L", "material": "Steel", "unit": "pcs", "weight_mean": 110, "cost_mean": 800, "price_mean": 1300}
    ],
    "Textile": [
        {"name": "Polyester Filament Yarn Spool", "material": "Plastic", "unit": "kg", "weight_mean": 5, "cost_mean": 1.1, "price_mean": 1.9},
        {"name": "Organic Cotton Woven Fabric Roll", "material": "Textile", "unit": "kg", "weight_mean": 25, "cost_mean": 4.5, "price_mean": 7.5},
        {"name": "Nylon Industrial Cord", "material": "Plastic", "unit": "kg", "weight_mean": 10, "cost_mean": 2.2, "price_mean": 3.8}
    ],
    "Plastic": [
        {"name": "Polyethylene (HDPE) Resin Granules", "material": "Plastic", "unit": "ton", "weight_mean": 1000, "cost_mean": 1100, "price_mean": 1400},
        {"name": "Polypropylene (PP) Sheet Rolls", "material": "Plastic", "unit": "ton", "weight_mean": 800, "cost_mean": 1250, "price_mean": 1650},
        {"name": "Polyvinyl Chloride (PVC) Powder", "material": "Plastic", "unit": "ton", "weight_mean": 1200, "cost_mean": 950, "price_mean": 1280}
    ],
    "Copper": [
        {"name": "Electrolytic Copper Wire Rod", "material": "Copper", "unit": "ton", "weight_mean": 1000, "cost_mean": 7800, "price_mean": 8800},
        {"name": "Copper Busbar 10x100mm", "material": "Copper", "unit": "ton", "weight_mean": 500, "cost_mean": 8300, "price_mean": 9600},
        {"name": "Seamless Copper Tube Coil", "material": "Copper", "unit": "ton", "weight_mean": 300, "cost_mean": 8600, "price_mean": 10200}
    ],
    "Mining": [
        {"name": "Iron Ore Concentrates Fines", "material": "Mining", "unit": "ton", "weight_mean": 50000, "cost_mean": 45, "price_mean": 95},
        {"name": "Bauxite Ore Crushed", "material": "Mining", "unit": "ton", "weight_mean": 40000, "cost_mean": 22, "price_mean": 48},
        {"name": "Copper Concentrate Powder", "material": "Mining", "unit": "ton", "weight_mean": 5000, "cost_mean": 1200, "price_mean": 1900}
    ],
    "Food Processing": [
        {"name": "Refined White Sugar Bulk Bag", "material": "Food", "unit": "ton", "weight_mean": 1000, "cost_mean": 350, "price_mean": 520},
        {"name": "Refined Soyabean Cooking Oil", "material": "Food", "unit": "liter", "weight_mean": 0.92, "cost_mean": 0.8, "price_mean": 1.4},
        {"name": "Wheat Flour Grade 1", "material": "Food", "unit": "ton", "weight_mean": 2000, "cost_mean": 280, "price_mean": 410}
    ],
    "Paper": [
        {"name": "Kraft Linerboard Paper Roll", "material": "Paper", "unit": "ton", "weight_mean": 1500, "cost_mean": 480, "price_mean": 650},
        {"name": "Bleached Softwood Kraft Pulp", "material": "Paper", "unit": "ton", "weight_mean": 1000, "cost_mean": 620, "price_mean": 810},
        {"name": "Corrugated Packaging Box Sheet", "material": "Paper", "unit": "ton", "weight_mean": 500, "cost_mean": 550, "price_mean": 760}
    ],
    "Electronics": [
        {"name": "Double-Sided PCB Board FR4", "material": "Electronics", "unit": "pcs", "weight_mean": 0.15, "cost_mean": 1.5, "price_mean": 3.8},
        {"name": "Integrated Microcontroller Chipset", "material": "Electronics", "unit": "pcs", "weight_mean": 0.005, "cost_mean": 0.6, "price_mean": 1.8},
        {"name": "Solder Paste Lead-Free Sn-Ag-Cu", "material": "Chemical", "unit": "kg", "weight_mean": 0.5, "cost_mean": 24, "price_mean": 45}
    ],
    "Machinery": [
        {"name": "CNC Machine Spindle Motor 11KW", "material": "Machinery", "unit": "pcs", "weight_mean": 45, "cost_mean": 350, "price_mean": 680},
        {"name": "Industrial Hydraulic Valve Manifold", "material": "Machinery", "unit": "pcs", "weight_mean": 18, "cost_mean": 180, "price_mean": 320},
        {"name": "Stainless Steel Ball Bearing 6204", "material": "Steel", "unit": "pcs", "weight_mean": 0.1, "cost_mean": 0.4, "price_mean": 1.2}
    ]
}

# Standardized Emission Factors (kg gas/unit of activity or weight)
EMISSION_FACTORS = {
    "electricity": {
        # kg CO2, CH4, N2O per kWh
        "India": {"CO2": 0.82, "CH4": 0.000008, "N2O": 0.000002, "CO2e": 0.83},
        "China": {"CO2": 0.61, "CH4": 0.000006, "N2O": 0.000001, "CO2e": 0.62},
        "Germany": {"CO2": 0.38, "CH4": 0.000004, "N2O": 0.000001, "CO2e": 0.39},
        "Japan": {"CO2": 0.47, "CH4": 0.000005, "N2O": 0.000001, "CO2e": 0.48},
        "South Korea": {"CO2": 0.45, "CH4": 0.000004, "N2O": 0.000001, "CO2e": 0.46},
        "Vietnam": {"CO2": 0.72, "CH4": 0.000007, "N2O": 0.000002, "CO2e": 0.73},
        "Thailand": {"CO2": 0.49, "CH4": 0.000005, "N2O": 0.000001, "CO2e": 0.50},
        "USA": {"CO2": 0.37, "CH4": 0.000003, "N2O": 0.0000008, "CO2e": 0.38},
        "Canada": {"CO2": 0.12, "CH4": 0.000001, "N2O": 0.0000003, "CO2e": 0.13},
        "UK": {"CO2": 0.21, "CH4": 0.000002, "N2O": 0.0000005, "CO2e": 0.22},
        "France": {"CO2": 0.05, "CH4": 0.0000005, "N2O": 0.0000001, "CO2e": 0.06},
        "Italy": {"CO2": 0.28, "CH4": 0.000003, "N2O": 0.0000007, "CO2e": 0.29},
        "Turkey": {"CO2": 0.41, "CH4": 0.000004, "N2O": 0.000001, "CO2e": 0.42},
        "UAE": {"CO2": 0.52, "CH4": 0.000005, "N2O": 0.000001, "CO2e": 0.53},
        "Australia": {"CO2": 0.68, "CH4": 0.000007, "N2O": 0.000002, "CO2e": 0.69},
        "Brazil": {"CO2": 0.09, "CH4": 0.000001, "N2O": 0.0000002, "CO2e": 0.10}
    },
    "fuel": {
        # kg per liter (or kg per kg for CNG)
        "Diesel": {"CO2": 2.68, "CH4": 0.00026, "N2O": 0.0021, "CO2e": 2.75},
        "Petrol": {"CO2": 2.31, "CH4": 0.00031, "N2O": 0.0015, "CO2e": 2.36},
        "CNG": {"CO2": 2.75, "CH4": 0.0011, "N2O": 0.0005, "CO2e": 2.80},
        "LPG": {"CO2": 1.51, "CH4": 0.00012, "N2O": 0.0003, "CO2e": 1.55},
        "Heavy Fuel Oil": {"CO2": 3.18, "CH4": 0.0004, "N2O": 0.0035, "CO2e": 3.29}
    },
    "transport": {
        # kg per tonne-km
        "Ocean Freight": {"CO2": 0.008, "CH4": 0.000001, "N2O": 0.0000005, "CO2e": 0.0084},
        "Rail": {"CO2": 0.022, "CH4": 0.000002, "N2O": 0.000001, "CO2e": 0.0226},
        "Road": {"CO2": 0.096, "CH4": 0.000008, "N2O": 0.000005, "CO2e": 0.0984},
        "Air": {"CO2": 0.602, "CH4": 0.00005, "N2O": 0.00003, "CO2e": 0.6135}
    },
    "material": {
        # kg CO2e per kg
        "Steel": {"CO2": 1.85, "CH4": 0.0001, "N2O": 0.00005, "CO2e": 1.90},
        "Aluminium": {"CO2": 11.2, "CH4": 0.0008, "N2O": 0.0002, "CO2e": 11.45},
        "Cement": {"CO2": 0.92, "CH4": 0.00002, "N2O": 0.00001, "CO2e": 0.93},
        "Chemical": {"CO2": 2.10, "CH4": 0.00015, "N2O": 0.00008, "CO2e": 2.15},
        "Plastic": {"CO2": 2.50, "CH4": 0.0002, "N2O": 0.0001, "CO2e": 2.58},
        "Copper": {"CO2": 3.80, "CH4": 0.0003, "N2O": 0.00015, "CO2e": 3.92},
        "Mining": {"CO2": 0.15, "CH4": 0.00001, "N2O": 0.000005, "CO2e": 0.16},
        "Textile": {"CO2": 4.50, "CH4": 0.0004, "N2O": 0.0002, "CO2e": 4.65},
        "Paper": {"CO2": 0.95, "CH4": 0.00008, "N2O": 0.00003, "CO2e": 0.98},
        "Electronics": {"CO2": 18.0, "CH4": 0.0015, "N2O": 0.0006, "CO2e": 18.25},
        "Machinery": {"CO2": 3.20, "CH4": 0.00025, "N2O": 0.0001, "CO2e": 3.30},
        "Food": {"CO2": 1.20, "CH4": 0.0001, "N2O": 0.00005, "CO2e": 1.25}
    },
    "waste": {
        # kg per kg (equivalent to tonnes per metric tonne)
        "Recycle": {"CO2": 0.02, "CH4": 0.000002, "N2O": 0.0000005, "CO2e": 0.021},
        "Landfill": {"CO2": 0.45, "CH4": 0.028, "N2O": 0.0001, "CO2e": 1.16}, # High methane penalty
        "Incineration": {"CO2": 0.32, "CH4": 0.00005, "N2O": 0.00002, "CO2e": 0.33}
    },
    "travel": {
        # kg per km
        "Flight Economy": {"CO2": 0.15, "CH4": 0.00001, "N2O": 0.000005, "CO2e": 0.16},
        "Flight Business": {"CO2": 0.45, "CH4": 0.00003, "N2O": 0.000015, "CO2e": 0.47},
        "Flight First Class": {"CO2": 0.60, "CH4": 0.00004, "N2O": 0.00002, "CO2e": 0.62},
        "Train": {"CO2": 0.03, "CH4": 0.000001, "N2O": 0.0000005, "CO2e": 0.031},
        "Car": {"CO2": 0.18, "CH4": 0.000015, "N2O": 0.00001, "CO2e": 0.19},
        "Hotel stay": {"CO2": 24.5, "CH4": 0.002, "N2O": 0.001, "CO2e": 25.0} # kg per night
    },
    "water": {
        # kg per m3
        "Supply": {"CO2": 0.3, "CH4": 0.000002, "N2O": 0.0000005, "CO2e": 0.31},
        "Treatment": {"CO2": 0.7, "CH4": 0.000005, "N2O": 0.000001, "CO2e": 0.72}
    }
}

# GL Account Mappings
GL_ACCOUNTS = {
    "101000": "Cash & Cash Equivalents",
    "120000": "Accounts Receivable",
    "140000": "Raw Material Inventory",
    "140500": "Finished Goods Inventory",
    "210000": "Accounts Payable",
    "400000": "Revenue - Product Sales",
    "501000": "Cost of Goods Sold - Materials",
    "502000": "Cost of Goods Sold - Labor",
    "511000": "Utility Expense - Electricity",
    "512000": "Utility Expense - Water",
    "513000": "Freight and Transportation Out",
    "514000": "Business Travel Expense",
    "515000": "Waste Disposal & ESG Compliance",
    "516000": "Fuel & Fleet Operations Expense",
    "517000": "Carbon Credits & Offsets",
    "518000": "Factory Shutdown & Plant Maintenance"
}

# Cost Center Mappings
COST_CENTERS = [
    "CC_CORP_HQ", "CC_SALES_MKTG", "CC_RD", 
    "CC_PLANT_OPS_01", "CC_PLANT_OPS_02", "CC_PLANT_OPS_03",
    "CC_LOGISTICS", "CC_WAREHOUSE_01", "CC_WAREHOUSE_02",
    "CC_HR_ADMIN", "CC_ESG_SUSTAINABILITY"
]
