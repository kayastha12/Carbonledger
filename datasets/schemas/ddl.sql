-- ============================================================================
-- CarbonLedger - Complete PostgreSQL DDL Schema
-- ============================================================================

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. MASTER REFERENCE TABLES
-- ----------------------------------------------------------------------------

CREATE TABLE countries (
    CountryID INT PRIMARY KEY,
    CountryName VARCHAR(100) NOT NULL UNIQUE,
    Currency VARCHAR(10) NOT NULL,
    TaxLabel VARCHAR(20) NOT NULL,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE cities (
    CityID INT PRIMARY KEY,
    CityName VARCHAR(100) NOT NULL,
    CountryName VARCHAR(100) NOT NULL REFERENCES countries(CountryName),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE ports (
    PortID INT PRIMARY KEY,
    PortName VARCHAR(100) NOT NULL,
    CountryName VARCHAR(100) NOT NULL REFERENCES countries(CountryName),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE transport_modes (
    TransportModeID INT PRIMARY KEY,
    ModeName VARCHAR(50) NOT NULL UNIQUE,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE currencies (
    CurrencyID INT PRIMARY KEY,
    CurrencyCode VARCHAR(10) NOT NULL UNIQUE,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE material_categories (
    MaterialCategoryID INT PRIMARY KEY,
    CategoryName VARCHAR(100) NOT NULL UNIQUE,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE emission_factors (
    FactorID INT PRIMARY KEY,
    Category VARCHAR(100) NOT NULL,
    Activity VARCHAR(100) NOT NULL,
    CO2 NUMERIC(12,6) NOT NULL CHECK (CO2 >= 0),
    CH4 NUMERIC(12,6) NOT NULL CHECK (CH4 >= 0),
    N2O NUMERIC(12,6) NOT NULL CHECK (N2O >= 0),
    CO2e NUMERIC(12,6) NOT NULL CHECK (CO2e >= 0),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

-- ----------------------------------------------------------------------------
-- 2. COMPANY & OPERATIONS MASTER TABLES
-- ----------------------------------------------------------------------------

CREATE TABLE companies (
    CompanyID INT PRIMARY KEY,
    CompanyName VARCHAR(255) NOT NULL,
    Industry VARCHAR(100) NOT NULL,
    Country VARCHAR(100) NOT NULL REFERENCES countries(CountryName),
    State VARCHAR(100),
    City VARCHAR(100),
    GSTNumber VARCHAR(50),
    RegistrationNumber VARCHAR(50),
    AnnualRevenue NUMERIC(18,2) CHECK (AnnualRevenue >= 0),
    Employees INT CHECK (Employees >= 0),
    CarbonReportingRequired BOOLEAN DEFAULT FALSE,
    NetZeroTargetYear INT,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE suppliers (
    SupplierID INT PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    SupplierName VARCHAR(255) NOT NULL,
    Country VARCHAR(100) NOT NULL REFERENCES countries(CountryName),
    State VARCHAR(100),
    City VARCHAR(100),
    Email VARCHAR(255),
    Phone VARCHAR(50),
    SupplierCategory VARCHAR(100),
    MaterialCategory VARCHAR(100),
    SupplierRating NUMERIC(3,1) CHECK (SupplierRating >= 1.0 AND SupplierRating <= 5.0),
    EmissionScore NUMERIC(5,2) CHECK (EmissionScore >= 0),
    PaymentTerms VARCHAR(50),
    GSTNumber VARCHAR(50),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE customers (
    CustomerID INT PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    CustomerName VARCHAR(255) NOT NULL,
    Industry VARCHAR(100),
    Country VARCHAR(100) NOT NULL REFERENCES countries(CountryName),
    GST VARCHAR(50),
    CreditLimit NUMERIC(18,2) CHECK (CreditLimit >= 0),
    RiskRating VARCHAR(20),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE plants (
    PlantID INT PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    PlantName VARCHAR(255) NOT NULL,
    Country VARCHAR(100) NOT NULL REFERENCES countries(CountryName),
    State VARCHAR(100),
    City VARCHAR(100),
    Latitude NUMERIC(9,6),
    Longitude NUMERIC(9,6),
    ProductionCapacity NUMERIC(18,2) CHECK (ProductionCapacity >= 0),
    EnergySource VARCHAR(100),
    PlantType VARCHAR(100),
    OperationalStatus VARCHAR(50),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE warehouses (
    WarehouseID INT PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    WarehouseName VARCHAR(255) NOT NULL,
    Country VARCHAR(100) NOT NULL REFERENCES countries(CountryName),
    City VARCHAR(100),
    Latitude NUMERIC(9,6),
    Longitude NUMERIC(9,6),
    Capacity NUMERIC(18,2) CHECK (Capacity >= 0),
    TemperatureControlled BOOLEAN DEFAULT FALSE,
    WarehouseType VARCHAR(100),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE employees (
    EmployeeID INT PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    Department VARCHAR(100),
    Designation VARCHAR(100),
    ManagerID INT REFERENCES employees(EmployeeID),
    Salary NUMERIC(18,2) CHECK (Salary >= 0),
    Grade VARCHAR(20),
    TravelCategory VARCHAR(50),
    JoiningDate DATE,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE vehicles (
    VehicleID VARCHAR(50) PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    VehicleType VARCHAR(100),
    RegistrationNumber VARCHAR(50) UNIQUE,
    FuelType VARCHAR(50),
    Capacity NUMERIC(12,2) CHECK (Capacity >= 0),
    EmissionClass VARCHAR(50),
    PurchaseDate DATE,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE drivers (
    DriverID VARCHAR(50) PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    WarehouseID INT NOT NULL REFERENCES warehouses(WarehouseID),
    LicenseType VARCHAR(50),
    Experience INT CHECK (Experience >= 0),
    ContactNumber VARCHAR(50),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE products (
    ProductID INT PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    SKU VARCHAR(50) UNIQUE,
    ProductName VARCHAR(255) NOT NULL,
    Category VARCHAR(100),
    Material VARCHAR(100),
    Weight NUMERIC(12,3) CHECK (Weight >= 0),
    Unit VARCHAR(20),
    StandardEmissionFactor NUMERIC(10,4) CHECK (StandardEmissionFactor >= 0),
    SellingPrice NUMERIC(18,2) CHECK (SellingPrice >= 0),
    ManufacturingCost NUMERIC(18,2) CHECK (ManufacturingCost >= 0),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE bom (
    BOMID INT PRIMARY KEY,
    ProductID INT NOT NULL REFERENCES products(ProductID),
    SupplierID INT NOT NULL REFERENCES suppliers(SupplierID),
    Material VARCHAR(100),
    Quantity NUMERIC(12,4) CHECK (Quantity >= 0),
    Unit VARCHAR(20),
    WastePercentage NUMERIC(5,2) CHECK (WastePercentage >= 0 AND WastePercentage <= 100),
    Cost NUMERIC(18,2) CHECK (Cost >= 0),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

-- ----------------------------------------------------------------------------
-- 3. TRANSACTIONAL & OPERATIONAL TABLES
-- ----------------------------------------------------------------------------

CREATE TABLE weather (
    WeatherID INT PRIMARY KEY,
    Date DATE NOT NULL,
    Temperature NUMERIC(4,1),
    Humidity NUMERIC(4,1),
    Rainfall NUMERIC(6,2) CHECK (Rainfall >= 0),
    WindSpeed NUMERIC(4,1) CHECK (WindSpeed >= 0),
    City VARCHAR(100) NOT NULL,
    Country VARCHAR(100) NOT NULL REFERENCES countries(CountryName),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE shutdowns (
    ShutdownID INT PRIMARY KEY,
    PlantID INT NOT NULL REFERENCES plants(PlantID),
    StartDate DATE NOT NULL,
    EndDate DATE NOT NULL,
    Reason VARCHAR(100),
    ProductionLoss NUMERIC(18,2) CHECK (ProductionLoss >= 0),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE purchase_orders (
    POID INT PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    SupplierID INT NOT NULL REFERENCES suppliers(SupplierID),
    PODate DATE NOT NULL,
    ExpectedDelivery DATE,
    Status VARCHAR(50),
    Currency VARCHAR(10) NOT NULL,
    Subtotal NUMERIC(18,2) CHECK (Subtotal >= 0),
    Tax NUMERIC(18,2) CHECK (Tax >= 0),
    ShippingCost NUMERIC(18,2) CHECK (ShippingCost >= 0),
    GrandTotal NUMERIC(18,2) CHECK (GrandTotal >= 0),
    DraftDate TIMESTAMP,
    SubmittedDate TIMESTAMP,
    ApprovedDate TIMESTAMP,
    ReleasedDate TIMESTAMP,
    DeliveredDate TIMESTAMP,
    ClosedDate TIMESTAMP,
    CancelledDate TIMESTAMP,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE purchase_order_items (
    POItemID INT PRIMARY KEY,
    POID INT NOT NULL REFERENCES purchase_orders(POID),
    ProductID INT NOT NULL REFERENCES products(ProductID),
    Quantity NUMERIC(12,2) CHECK (Quantity >= 0),
    Unit VARCHAR(20),
    UnitPrice NUMERIC(18,2) CHECK (UnitPrice >= 0),
    Discount NUMERIC(18,2) CHECK (Discount >= 0),
    TotalPrice NUMERIC(18,2) CHECK (TotalPrice >= 0),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE invoices (
    InvoiceID INT PRIMARY KEY,
    POID INT NOT NULL REFERENCES purchase_orders(POID),
    SupplierID INT NOT NULL REFERENCES suppliers(SupplierID),
    InvoiceNumber VARCHAR(100) NOT NULL UNIQUE,
    InvoiceDate DATE NOT NULL,
    PaymentStatus VARCHAR(50),
    Subtotal NUMERIC(18,2) CHECK (Subtotal >= 0),
    GST NUMERIC(18,2) CHECK (GST >= 0),
    Discount NUMERIC(18,2) CHECK (Discount >= 0),
    Freight NUMERIC(18,2) CHECK (Freight >= 0),
    GrandTotal NUMERIC(18,2) CHECK (GrandTotal >= 0),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE payments (
    PaymentID INT PRIMARY KEY,
    InvoiceID INT NOT NULL REFERENCES invoices(InvoiceID),
    PaymentMethod VARCHAR(50),
    Bank VARCHAR(100),
    Amount NUMERIC(18,2) CHECK (Amount >= 0),
    PaymentDate DATE NOT NULL,
    TransactionReference VARCHAR(100) UNIQUE,
    PaymentStatus VARCHAR(50),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE exchange_rates (
    ExchangeRateID INT PRIMARY KEY,
    Currency VARCHAR(10) NOT NULL,
    ExchangeRate NUMERIC(12,4) CHECK (ExchangeRate > 0),
    Date DATE NOT NULL,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

-- PARTITIONED TABLE: erp_export
CREATE TABLE erp_export (
    ERPID INT NOT NULL,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    InvoiceID INT NOT NULL REFERENCES invoices(InvoiceID),
    POID INT NOT NULL REFERENCES purchase_orders(POID),
    GLAccount VARCHAR(20) NOT NULL,
    CostCenter VARCHAR(50) NOT NULL,
    PostingDate DATE NOT NULL,
    MaterialCode VARCHAR(50),
    Quantity NUMERIC(12,2),
    Amount NUMERIC(18,2),
    Currency VARCHAR(10) NOT NULL,
    CreatedDate TIMESTAMP,
    UpdatedDate TIMESTAMP,
    Status VARCHAR(20),
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64),
    PRIMARY KEY (ERPID, PostingDate)
) PARTITION BY RANGE (PostingDate);

CREATE TABLE shipping_manifest (
    ManifestID INT PRIMARY KEY,
    InvoiceID INT NOT NULL REFERENCES invoices(InvoiceID),
    POID INT NOT NULL REFERENCES purchase_orders(POID),
    SupplierID INT NOT NULL REFERENCES suppliers(SupplierID),
    OriginCountry VARCHAR(100) REFERENCES countries(CountryName),
    DestinationCountry VARCHAR(100) REFERENCES countries(CountryName),
    Port VARCHAR(100),
    TransportMode VARCHAR(50),
    ContainerNumber VARCHAR(50),
    Weight NUMERIC(12,2) CHECK (Weight >= 0),
    Distance NUMERIC(12,2) CHECK (Distance >= 0),
    ShipmentDate DATE NOT NULL,
    ArrivalDate DATE NOT NULL,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

-- PARTITIONED TABLE: logistics
CREATE TABLE logistics (
    LogisticsID INT NOT NULL,
    ManifestID INT NOT NULL REFERENCES shipping_manifest(ManifestID),
    VehicleID VARCHAR(50) NOT NULL REFERENCES vehicles(VehicleID),
    DriverID VARCHAR(50) NOT NULL REFERENCES drivers(DriverID),
    WarehouseID INT NOT NULL REFERENCES warehouses(WarehouseID),
    Latitude NUMERIC(9,6),
    Longitude NUMERIC(9,6),
    FuelConsumed NUMERIC(12,2) CHECK (FuelConsumed >= 0),
    TravelDistance NUMERIC(12,2) CHECK (TravelDistance >= 0),
    AverageSpeed NUMERIC(5,1) CHECK (AverageSpeed >= 0),
    DelayHours NUMERIC(5,1) CHECK (DelayHours >= 0),
    Temperature NUMERIC(4,1),
    Humidity NUMERIC(4,1),
    Timestamp TIMESTAMP NOT NULL,
    CreatedDate TIMESTAMP,
    UpdatedDate TIMESTAMP,
    Status VARCHAR(20),
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64),
    PRIMARY KEY (LogisticsID, Timestamp)
) PARTITION BY RANGE (Timestamp);

-- ----------------------------------------------------------------------------
-- 4. UTILITIES & CARBON COMPLIANCE TABLES
-- ----------------------------------------------------------------------------

CREATE TABLE electricity_bills (
    ElectricityID INT PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    PlantID INT NOT NULL REFERENCES plants(PlantID),
    BillingMonth VARCHAR(20) NOT NULL,
    ConsumptionKWh NUMERIC(18,2) CHECK (ConsumptionKWh >= 0),
    PeakDemand NUMERIC(12,2) CHECK (PeakDemand >= 0),
    EnergyCharge NUMERIC(18,2) CHECK (EnergyCharge >= 0),
    GridEmissionFactor NUMERIC(8,4) CHECK (GridEmissionFactor >= 0),
    RenewablePercentage NUMERIC(5,2) CHECK (RenewablePercentage >= 0 AND RenewablePercentage <= 100),
    CO2Emission NUMERIC(18,4) CHECK (CO2Emission >= 0),
    CH4Emission NUMERIC(18,6) CHECK (CH4Emission >= 0),
    N2OEmission NUMERIC(18,6) CHECK (N2OEmission >= 0),
    CO2eEmission NUMERIC(18,4) CHECK (CO2eEmission >= 0),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE water_bills (
    WaterBillID INT PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    PlantID INT NOT NULL REFERENCES plants(PlantID),
    Consumption NUMERIC(18,2) CHECK (Consumption >= 0),
    TreatmentCost NUMERIC(18,2) CHECK (TreatmentCost >= 0),
    EmissionFactor NUMERIC(8,4) CHECK (EmissionFactor >= 0),
    CO2Emission NUMERIC(18,4) CHECK (CO2Emission >= 0),
    CH4Emission NUMERIC(18,6) CHECK (CH4Emission >= 0),
    N2OEmission NUMERIC(18,6) CHECK (N2OEmission >= 0),
    CO2eEmission NUMERIC(18,4) CHECK (CO2eEmission >= 0),
    BillingMonth VARCHAR(20) NOT NULL,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE fuel_logs (
    FuelLogID INT PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    VehicleID VARCHAR(50) NOT NULL REFERENCES vehicles(VehicleID),
    FuelType VARCHAR(50),
    FuelVolume NUMERIC(12,2) CHECK (FuelVolume >= 0),
    FuelCost NUMERIC(12,2) CHECK (FuelCost >= 0),
    Mileage NUMERIC(12,2) CHECK (Mileage >= 0),
    EmissionFactor NUMERIC(8,4) CHECK (EmissionFactor >= 0),
    CO2Emission NUMERIC(18,4) CHECK (CO2Emission >= 0),
    CH4Emission NUMERIC(18,6) CHECK (CH4Emission >= 0),
    N2OEmission NUMERIC(18,6) CHECK (N2OEmission >= 0),
    CO2eEmission NUMERIC(18,4) CHECK (CO2eEmission >= 0),
    FuelDate DATE NOT NULL,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE waste_logs (
    WasteID INT PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    WasteCategory VARCHAR(100),
    WasteWeight NUMERIC(12,3) CHECK (WasteWeight >= 0),
    DisposalMethod VARCHAR(100),
    Recycler VARCHAR(255),
    EmissionFactor NUMERIC(8,4) CHECK (EmissionFactor >= 0),
    CO2Emission NUMERIC(18,4) CHECK (CO2Emission >= 0),
    CH4Emission NUMERIC(18,6) CHECK (CH4Emission >= 0),
    N2OEmission NUMERIC(18,6) CHECK (N2OEmission >= 0),
    CO2eEmission NUMERIC(18,4) CHECK (CO2eEmission >= 0),
    WasteDate DATE NOT NULL,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE employee_travel (
    TravelID INT PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    EmployeeID INT NOT NULL REFERENCES employees(EmployeeID),
    Department VARCHAR(100),
    TravelMode VARCHAR(50),
    Origin VARCHAR(100),
    Destination VARCHAR(100),
    Distance NUMERIC(12,2) CHECK (Distance >= 0),
    HotelNights INT CHECK (HotelNights >= 0),
    FlightClass VARCHAR(50),
    EmissionFactor NUMERIC(8,4) CHECK (EmissionFactor >= 0),
    CO2Emission NUMERIC(18,4) CHECK (CO2Emission >= 0),
    CH4Emission NUMERIC(18,6) CHECK (CH4Emission >= 0),
    N2OEmission NUMERIC(18,6) CHECK (N2OEmission >= 0),
    CO2eEmission NUMERIC(18,4) CHECK (CO2eEmission >= 0),
    TravelDate DATE NOT NULL,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE cbam_reporting (
    CBAMID INT PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    SupplierID INT NOT NULL REFERENCES suppliers(SupplierID),
    ProductID INT NOT NULL REFERENCES products(ProductID),
    InvoiceID INT NOT NULL REFERENCES invoices(InvoiceID),
    EmbeddedEmission NUMERIC(12,3) CHECK (EmbeddedEmission >= 0),
    DirectEmission NUMERIC(12,3) CHECK (DirectEmission >= 0),
    IndirectEmission NUMERIC(12,3) CHECK (IndirectEmission >= 0),
    CarbonPrice NUMERIC(8,2) CHECK (CarbonPrice >= 0),
    ReportingQuarter VARCHAR(20),
    VerificationStatus VARCHAR(50),
    SubmissionStatus VARCHAR(50),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE manufacturing_orders (
    ManufacturingOrderID INT PRIMARY KEY,
    PlantID INT NOT NULL REFERENCES plants(PlantID),
    ProductID INT NOT NULL REFERENCES products(ProductID),
    ProductionDate DATE NOT NULL,
    Shift VARCHAR(50),
    MachineHours NUMERIC(10,2) CHECK (MachineHours >= 0),
    ElectricityConsumed NUMERIC(12,2) CHECK (ElectricityConsumed >= 0),
    QuantityProduced NUMERIC(12,2) CHECK (QuantityProduced >= 0),
    WasteGenerated NUMERIC(12,2) CHECK (WasteGenerated >= 0),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE inventory (
    InventoryID INT PRIMARY KEY,
    WarehouseID INT NOT NULL REFERENCES warehouses(WarehouseID),
    ProductID INT NOT NULL REFERENCES products(ProductID),
    AvailableStock NUMERIC(12,2) CHECK (AvailableStock >= 0),
    ReservedStock NUMERIC(12,2) CHECK (ReservedStock >= 0),
    MinimumStock NUMERIC(12,2) CHECK (MinimumStock >= 0),
    MaximumStock NUMERIC(12,2) CHECK (MaximumStock >= 0),
    ReorderLevel NUMERIC(12,2) CHECK (ReorderLevel >= 0),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE targets (
    TargetID INT PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    Scope1Target NUMERIC(5,2) CHECK (Scope1Target >= 0),
    Scope2Target NUMERIC(5,2) CHECK (Scope2Target >= 0),
    Scope3Target NUMERIC(5,2) CHECK (Scope3Target >= 0),
    NetZeroYear INT,
    CurrentEmission NUMERIC(18,2) CHECK (CurrentEmission >= 0),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE offsets (
    OffsetID INT PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    OffsetProject VARCHAR(255),
    OffsetType VARCHAR(100),
    CreditsPurchased INT CHECK (CreditsPurchased >= 0),
    CreditsUsed INT CHECK (CreditsUsed >= 0),
    CarbonReduction NUMERIC(18,2) CHECK (CarbonReduction >= 0),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE audits (
    AuditID INT PRIMARY KEY,
    SupplierID INT NOT NULL REFERENCES suppliers(SupplierID),
    AuditDate DATE NOT NULL,
    Auditor VARCHAR(255),
    ComplianceScore NUMERIC(5,2) CHECK (ComplianceScore >= 0),
    RiskLevel VARCHAR(50),
    Findings TEXT,
    Status VARCHAR(50),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE lifecycle (
    LifecycleID INT PRIMARY KEY,
    ProductID INT NOT NULL REFERENCES products(ProductID),
    RawMaterialEmission NUMERIC(12,3) CHECK (RawMaterialEmission >= 0),
    ManufacturingEmission NUMERIC(12,3) CHECK (ManufacturingEmission >= 0),
    TransportEmission NUMERIC(12,3) CHECK (TransportEmission >= 0),
    UsageEmission NUMERIC(12,3) CHECK (UsageEmission >= 0),
    EndOfLifeEmission NUMERIC(12,3) CHECK (EndOfLifeEmission >= 0),
    TotalEmission NUMERIC(12,3) CHECK (TotalEmission >= 0),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

-- ----------------------------------------------------------------------------
-- 5. UNSTRUCTURED / AI RAG DOCUMENTS AND LABELS
-- ----------------------------------------------------------------------------

CREATE TABLE documents (
    DocumentID INT PRIMARY KEY,
    CompanyID INT NOT NULL REFERENCES companies(CompanyID),
    SupplierID INT NOT NULL REFERENCES suppliers(SupplierID),
    DocumentType VARCHAR(100),
    OCRText TEXT,
    Language VARCHAR(50),
    FileName VARCHAR(255),
    FilePath VARCHAR(255),
    QualityScore NUMERIC(4,2),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE embeddings (
    EmbeddingID INT PRIMARY KEY,
    DocumentID INT NOT NULL REFERENCES documents(DocumentID),
    ChunkID INT,
    ChunkText TEXT,
    EmbeddingModel VARCHAR(100),
    VectorDimensions INT,
    EmbeddingVersion VARCHAR(20),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

CREATE TABLE ai_labels (
    LabelID INT PRIMARY KEY,
    RecordID VARCHAR(100) NOT NULL,
    Label VARCHAR(50) NOT NULL,
    Severity VARCHAR(50),
    ExpectedEmission NUMERIC(18,4),
    ActualEmission NUMERIC(18,4),
    RootCause VARCHAR(255),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'Active',
    BatchID VARCHAR(50),
    GeneratorVersion VARCHAR(10),
    CreatedByGenerator VARCHAR(100),
    GenerationTimestamp TIMESTAMP,
    Source VARCHAR(50),
    Checksum VARCHAR(64)
);

-- ----------------------------------------------------------------------------
-- 6. PARTITION TABLES DEFINITIONS (Range Partitions)
-- ----------------------------------------------------------------------------

-- erp_export partitions
CREATE TABLE erp_export_2023 PARTITION OF erp_export
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');

CREATE TABLE erp_export_2024 PARTITION OF erp_export
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE erp_export_2025 PARTITION OF erp_export
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

CREATE TABLE erp_export_2026 PARTITION OF erp_export
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

-- logistics partitions
CREATE TABLE logistics_2023 PARTITION OF logistics
    FOR VALUES FROM ('2023-01-01 00:00:00') TO ('2024-01-01 00:00:00');

CREATE TABLE logistics_2024 PARTITION OF logistics
    FOR VALUES FROM ('2024-01-01 00:00:00') TO ('2025-01-01 00:00:00');

CREATE TABLE logistics_2025 PARTITION OF logistics
    FOR VALUES FROM ('2025-01-01 00:00:00') TO ('2026-01-01 00:00:00');

CREATE TABLE logistics_2026 PARTITION OF logistics
    FOR VALUES FROM ('2026-01-01 00:00:00') TO ('2027-01-01 00:00:00');

-- ----------------------------------------------------------------------------
-- 7. COMPOSITE INDEXES & VIEWS FOR OPTIMIZATION
-- ----------------------------------------------------------------------------

-- Indexes for performance
CREATE INDEX idx_po_company_supplier ON purchase_orders(CompanyID, SupplierID);
CREATE INDEX idx_po_items_po_product ON purchase_order_items(POID, ProductID);
CREATE INDEX idx_invoices_po ON invoices(POID);
CREATE INDEX idx_shipping_invoice ON shipping_manifest(InvoiceID);
CREATE INDEX idx_mfg_plant_product ON manufacturing_orders(PlantID, ProductID);
CREATE INDEX idx_cbam_quarter ON cbam_reporting(ReportingQuarter);

-- Business analytics view: Quarterly CBAM Carbon Tax Liability report
CREATE VIEW view_quarterly_cbam_liability AS
SELECT 
    c.CompanyName,
    r.ReportingQuarter,
    COUNT(r.CBAMID) as TotalItemsImported,
    SUM(r.EmbeddedEmission) as TotalEmbeddedEmissionsTonnes,
    SUM(r.EmbeddedEmission * r.CarbonPrice) as EstimatedCarbonTaxLiabilityUSD
FROM cbam_reporting r
JOIN companies c ON r.CompanyID = c.CompanyID
GROUP BY c.CompanyName, r.ReportingQuarter;

-- ----------------------------------------------------------------------------
-- 8. POSTGRESQL IMPORT COPY SCRIPTS
-- ----------------------------------------------------------------------------
-- Command sequences to import the generated files rapidly via psql client:
--
-- \copy countries FROM 'output/master/countries.csv' DELIMITER ',' CSV HEADER;
-- \copy cities FROM 'output/master/cities.csv' DELIMITER ',' CSV HEADER;
-- \copy ports FROM 'output/master/ports.csv' DELIMITER ',' CSV HEADER;
-- \copy transport_modes FROM 'output/master/transport_modes.csv' DELIMITER ',' CSV HEADER;
-- \copy currencies FROM 'output/master/currencies.csv' DELIMITER ',' CSV HEADER;
-- \copy material_categories FROM 'output/master/material_categories.csv' DELIMITER ',' CSV HEADER;
-- \copy emission_factors FROM 'output/master/emission_factors.csv' DELIMITER ',' CSV HEADER;
-- \copy companies FROM 'output/master/companies.csv' DELIMITER ',' CSV HEADER;
-- \copy suppliers FROM 'output/master/suppliers.csv' DELIMITER ',' CSV HEADER;
-- \copy customers FROM 'output/master/customers.csv' DELIMITER ',' CSV HEADER;
-- \copy plants FROM 'output/master/plants.csv' DELIMITER ',' CSV HEADER;
-- \copy warehouses FROM 'output/master/warehouses.csv' DELIMITER ',' CSV HEADER;
-- \copy employees FROM 'output/master/employees.csv' DELIMITER ',' CSV HEADER;
-- \copy vehicles FROM 'output/master/vehicles.csv' DELIMITER ',' CSV HEADER;
-- \copy drivers FROM 'output/master/drivers.csv' DELIMITER ',' CSV HEADER;
-- \copy products FROM 'output/master/products.csv' DELIMITER ',' CSV HEADER;
-- \copy bom FROM 'output/master/bom.csv' DELIMITER ',' CSV HEADER;
--
-- \copy weather FROM 'output/transactional/weather.csv' DELIMITER ',' CSV HEADER;
-- \copy shutdowns FROM 'output/transactional/shutdowns.csv' DELIMITER ',' CSV HEADER;
-- \copy purchase_orders FROM 'output/transactional/purchase_orders.csv' DELIMITER ',' CSV HEADER;
-- \copy purchase_order_items FROM 'output/transactional/purchase_order_items.csv' DELIMITER ',' CSV HEADER;
-- \copy invoices FROM 'output/transactional/invoices.csv' DELIMITER ',' CSV HEADER;
-- \copy payments FROM 'output/transactional/payments.csv' DELIMITER ',' CSV HEADER;
-- \copy exchange_rates FROM 'output/transactional/exchange_rates.csv' DELIMITER ',' CSV HEADER;
-- \copy erp_export FROM 'output/transactional/erp_export.csv' DELIMITER ',' CSV HEADER;
-- \copy shipping_manifest FROM 'output/transactional/shipping_manifest.csv' DELIMITER ',' CSV HEADER;
-- \copy logistics FROM 'output/transactional/logistics.csv' DELIMITER ',' CSV HEADER;
-- \copy electricity_bills FROM 'output/transactional/electricity_bills.csv' DELIMITER ',' CSV HEADER;
-- \copy water_bills FROM 'output/transactional/water_bills.csv' DELIMITER ',' CSV HEADER;
-- \copy fuel_logs FROM 'output/transactional/fuel_logs.csv' DELIMITER ',' CSV HEADER;
-- \copy waste_logs FROM 'output/transactional/waste_logs.csv' DELIMITER ',' CSV HEADER;
-- \copy employee_travel FROM 'output/transactional/employee_travel.csv' DELIMITER ',' CSV HEADER;
-- \copy cbam_reporting FROM 'output/transactional/cbam_reporting.csv' DELIMITER ',' CSV HEADER;
-- \copy manufacturing_orders FROM 'output/transactional/manufacturing_orders.csv' DELIMITER ',' CSV HEADER;
-- \copy inventory FROM 'output/transactional/inventory.csv' DELIMITER ',' CSV HEADER;
-- \copy targets FROM 'output/transactional/targets.csv' DELIMITER ',' CSV HEADER;
-- \copy offsets FROM 'output/transactional/offsets.csv' DELIMITER ',' CSV HEADER;
-- \copy audits FROM 'output/transactional/audits.csv' DELIMITER ',' CSV HEADER;
-- \copy lifecycle FROM 'output/transactional/lifecycle.csv' DELIMITER ',' CSV HEADER;
-- \copy documents FROM 'output/transactional/documents.csv' DELIMITER ',' CSV HEADER;
-- \copy embeddings FROM 'output/transactional/embeddings.csv' DELIMITER ',' CSV HEADER;
-- \copy ai_labels FROM 'output/transactional/ai_labels.csv' DELIMITER ',' CSV HEADER;
