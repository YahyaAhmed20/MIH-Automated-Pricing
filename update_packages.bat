@echo off
title RP Hospital Import Tool

echo.
echo ==========================================
echo        RP Hospital Import Tool
echo ==========================================
echo.

cd /d D:\desktop\rphospital

call Scripts\activate.bat

cd src

echo.
echo Using Excel File: APP.xlsx
echo.

echo.
echo ==========================================
echo Import Package Catalog...
echo ==========================================
python manage.py import_package_catalog APP.xlsx

if errorlevel 1 (
    echo.
    echo ##########################################
    echo ERROR: Package Catalog Import Failed
    echo ##########################################
    pause
    exit /b
)

echo.
echo ==========================================
echo Import Cash Packages...
echo ==========================================
python manage.py import_cash_packages APP.xlsx

if errorlevel 1 (
    echo.
    echo ##########################################
    echo ERROR: Cash Package Import Failed
    echo ##########################################
    pause
    exit /b
)

echo.
echo ==========================================
echo Migrate Contract Entities...
echo ==========================================
python manage.py migrate_contract_entities APP.xlsx

if errorlevel 1 (
    echo.
    echo ##########################################
    echo ERROR: Contract Migration Failed
    echo ##########################################
    pause
    exit /b
)

echo.
echo ==========================================
echo Import Company Contracts...
echo ==========================================
python manage.py import_company_contracts APP.xlsx

if errorlevel 1 (
    echo.
    echo ##########################################
    echo ERROR: Company Contract Import Failed
    echo ##########################################
    pause
    exit /b
)

echo.
echo ==========================================
echo Import Company Discounts...
echo ==========================================
python manage.py import_company_discounts APP.xlsx

if errorlevel 1 (
    echo.
    echo ##########################################
    echo ERROR: Company Discount Import Failed
    echo ##########################################
    pause
    exit /b
)

echo.
echo ==========================================
echo Import Special Offers...
echo ==========================================
python manage.py import_special_offers APP.xlsx

if errorlevel 1 (
    echo.
    echo ##########################################
    echo ERROR: Special Offers Import Failed
    echo ##########################################
    pause
    exit /b
)

echo.
echo ==========================================
echo Import Service Records...
echo ==========================================
python manage.py import_service_records APP.xlsx

if errorlevel 1 (
    echo.
    echo ##########################################
    echo ERROR: Service Records Import Failed
    echo ##########################################
    pause
    exit /b
)

echo.
echo ==========================================
echo Import Pricing Details...
echo ==========================================
python manage.py import_pricing_details APP.xlsx

if errorlevel 1 (
    echo.
    echo ##########################################
    echo ERROR: Pricing Details Import Failed
    echo ##########################################
    pause
    exit /b
)

echo.
echo ==========================================
echo Import Similar Invoices...
echo ==========================================
python manage.py import_similar_invoices APP.xlsx

if errorlevel 1 (
    echo.
    echo ##########################################
    echo ERROR: Similar Invoices Import Failed
    echo ##########################################
    pause
    exit /b
)

echo.
echo ==========================================
echo SUCCESS - All Imports Completed
echo ==========================================
echo.

pause