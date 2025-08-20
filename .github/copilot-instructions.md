<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# TORI Data Processing Azure Function (Python)

This is a Python Azure Function project that:
- Uses a Timer Trigger to run every 30 minutes
- Fetches CSV data from the TORI API endpoint
- Parses the CSV data using pandas
- Inserts the data into a SQL Server database using pyodbc

## Key Components:
- **ToriDataProcessor/__init__.py**: Main function with timer trigger
- **ToriDataProcessor/function.json**: Function configuration with timer schedule
- **requirements.txt**: Python dependencies
- **Database**: Automatically creates table structure based on CSV headers
- **API Integration**: Calls TORI API with Bearer token authentication

## Technologies:
- Azure Functions (Python)
- pandas for CSV parsing
- pyodbc for SQL Server database operations
- requests for HTTP API calls

## Configuration:
- API token stored in local.settings.json as ToriApiToken
- SQL Server connection string configured as SqlConnectionString
- Timer runs every 30 minutes (0 */30 * * * *)

## Dependencies:
- azure-functions
- requests
- pandas
- pyodbc
- sqlalchemy
- urllib3
