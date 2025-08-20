#!/usr/bin/env python3
"""
TORI Data Processing Script
Runs daily via GitHub Actions to fetch data from TORI API and store in SQL Server
"""

import datetime
import logging
import os
import io
import re
import pandas as pd
import pyodbc
import requests
from urllib.parse import quote


def get_access_token():
    """
    Get OAuth2 access token from Microsoft Azure AD
    """
    try:
        # OAuth2 endpoint
        token_url = "https://login.microsoftonline.com/05d75c05-fa1a-42e7-9cf1-eb416c396f2d/oauth2/v2.0/token"
        
        # OAuth2 credentials from environment variables (GitHub secrets)
        client_id = os.getenv('CLIENT_ID')
        client_secret = os.getenv('CLIENT_SECRET')
        
        if not client_id or not client_secret:
            raise ValueError("CLIENT_ID and CLIENT_SECRET environment variables must be set")
            
        scope = "4a730d72-d145-4f6a-91f8-9783c9ceed41/.default"
        grant_type = "client_credentials"
        
        # Prepare form data
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope,
            "grant_type": grant_type
        }
        
        # Headers
        headers = {
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": "TORI Data Processor"
        }
        
        logging.info("Requesting OAuth2 access token...")
        
        # Make token request
        response = requests.post(token_url, data=data, headers=headers, timeout=30)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise ValueError("Access token not found in response")
        
        logging.info("Successfully obtained access token")
        return access_token
        
    except Exception as e:
        logging.error(f"Error getting access token: {str(e)}")
        raise


def fetch_data_from_api(start_date=None, end_date=None):
    """
    Fetch TORI reports data using Bearer token authentication
    
    Args:
        start_date (str): Start date in format 'YYYY-MM-DDTHH:MM:SS' (optional)
        end_date (str): End date in format 'YYYY-MM-DDTHH:MM:SS' (optional)
    
    Returns:
        str: CSV data as string
    """
    try:
        # Get access token
        access_token = get_access_token()
        
        # Default time range if not provided (last 24 hours for daily run)
        if not start_date or not end_date:
            end_time = datetime.datetime.utcnow()
            start_time = end_time - datetime.timedelta(hours=24)
            start_date = start_time.strftime('%Y-%m-%dT%H:%M:%S')
            end_date = end_time.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Construct API URL with proper URL encoding
        base_url = "https://tori-agent.maersk-digital.net/reports/"
        params = f"start={quote(start_date)}&end={quote(end_date)}"
        api_url = f"{base_url}?{params}"
        
        # Setup headers with Bearer token
        headers = {
            "authorization": f"Bearer {access_token}",
            "accept": "*/*",
            "user-agent": "TORI Data Processor"
        }
        
        logging.info(f"Fetching TORI reports from {start_date} to {end_date}")
        logging.info(f"API URL: {api_url}")
        
        # Make API request
        response = requests.get(api_url, headers=headers, timeout=60)
        response.raise_for_status()
        
        csv_content = response.text
        logging.info(f"Successfully received {len(csv_content)} characters of CSV data")
        
        return csv_content
        
    except Exception as e:
        logging.error(f"Error fetching TORI reports: {str(e)}")
        raise


def create_table_if_not_exists(cursor, table_name, df):
    """
    Create table if it doesn't exist based on DataFrame columns
    """
    try:
        # Check if table exists
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = '{table_name}'
        """)
        
        if cursor.fetchone()[0] == 0:
            # Create table based on DataFrame columns
            columns_sql = []
            for column in df.columns:
                # Clean column name for SQL
                clean_column = re.sub(r'[^a-zA-Z0-9_]', '_', column)
                columns_sql.append(f"[{clean_column}] NVARCHAR(MAX)")
            
            create_sql = f"""
                CREATE TABLE [{table_name}] (
                    ID INT IDENTITY(1,1) PRIMARY KEY,
                    ProcessedDate DATETIME DEFAULT GETDATE(),
                    {', '.join(columns_sql)}
                )
            """
            
            logging.info(f"Creating table {table_name}")
            cursor.execute(create_sql)
            logging.info(f"Table {table_name} created successfully")
        else:
            logging.info(f"Table {table_name} already exists")
            
    except Exception as e:
        logging.error(f"Error creating table: {str(e)}")
        raise


def process_csv_data(csv_content):
    """
    Process CSV data and insert into SQL Server database
    
    Args:
        csv_content (str): CSV data as string
    """
    try:
        if not csv_content or csv_content.strip() == "":
            logging.warning("Empty CSV content received")
            return
        
        # Parse CSV using pandas
        df = pd.read_csv(io.StringIO(csv_content))
        
        if df.empty:
            logging.warning("CSV data is empty")
            return
        
        logging.info(f"Parsed {len(df)} records from CSV")
        logging.info(f"CSV columns: {list(df.columns)}")
        
        # Get Azure SQL Database credentials from environment variables
        sql_server = os.getenv('AZURE_SQL_SERVER')
        sql_database = os.getenv('AZURE_SQL_DATABASE')
        sql_username = os.getenv('AZURE_SQL_USERNAME')
        sql_password = os.getenv('AZURE_SQL_PASSWORD')
        
        if not all([sql_server, sql_database, sql_username, sql_password]):
            raise ValueError("Azure SQL Database environment variables not set (AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_USERNAME, AZURE_SQL_PASSWORD)")
        
        # Construct Azure SQL Database connection string
        connection_string = (
            f"Driver={{ODBC Driver 17 for SQL Server}};"
            f"Server={sql_server};"
            f"Database={sql_database};"
            f"Uid={sql_username};"
            f"Pwd={sql_password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        logging.info(f"Connecting to Azure SQL Database: {sql_server}/{sql_database}")
        
        # Connect to Azure SQL Database
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            
            table_name = "ToriReports"
            
            # Create table if it doesn't exist
            create_table_if_not_exists(cursor, table_name, df)
            
            # Clean column names for SQL
            clean_columns = [re.sub(r'[^a-zA-Z0-9_]', '_', col) for col in df.columns]
            
            # Insert data
            placeholders = ', '.join(['?' for _ in clean_columns])
            columns_sql = ', '.join([f'[{col}]' for col in clean_columns])
            
            insert_sql = f"INSERT INTO [{table_name}] ({columns_sql}) VALUES ({placeholders})"
            
            # Convert DataFrame to list of tuples for insertion
            # Ensure all values are converted to strings to avoid data type issues
            data_to_insert = []
            for _, row in df.iterrows():
                # Convert each value to string, handling NaN/None values
                converted_row = tuple(
                    str(value) if pd.notna(value) else None
                    for value in row
                )
                data_to_insert.append(converted_row)
            
            logging.info(f"Inserting {len(data_to_insert)} records into {table_name}")
            cursor.executemany(insert_sql, data_to_insert)
            conn.commit()
            
            logging.info(f"Successfully inserted {len(data_to_insert)} records")
            
    except Exception as e:
        logging.error(f"Error processing CSV data: {str(e)}")
        raise


def main():
    """
    Main function to fetch and process TORI data
    """
    try:
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        logging.info("Starting TORI data processing...")
        
        # Fetch CSV data from TORI API
        csv_data = fetch_data_from_api()
        
        if csv_data:
            # Process CSV and insert into database
            process_csv_data(csv_data)
            logging.info("Data processing completed successfully")
        else:
            logging.warning("No data received from API")
            
    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")
        raise


if __name__ == "__main__":
    main()
