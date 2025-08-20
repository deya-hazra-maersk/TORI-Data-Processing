# TORI Data Processing - GitHub Actions

This project processes TORI data daily using GitHub Actions instead of Azure Functions.

## Overview

- **Schedule**: Runs daily at 8:00 AM UTC (configurable)
- **Trigger**: GitHub Actions cron job with manual trigger option
- **Data Source**: TORI API with OAuth2 authentication
- **Database**: SQL Server for data storage
- **Processing**: CSV parsing with pandas

## Setup Instructions

### 1. Repository Setup

1. Push this code to your GitHub repository
2. The workflow file is located at `.github/workflows/tori-data-processing.yml`

### 2. Configure GitHub Secrets

Go to your repository settings > Secrets and variables > Actions, and add these secrets:

**Azure AD OAuth2 Credentials:**
- `CLIENT_ID`: Your Azure AD application client ID
- `CLIENT_SECRET`: Your Azure AD application client secret

**Azure SQL Database Credentials:**
- `AZURE_SQL_SERVER`: Your Azure SQL server (e.g., `top-insights-dev.database.windows.net`)
- `AZURE_SQL_DATABASE`: Your Azure SQL database name (e.g., `top-insights-dev-db1`)
- `AZURE_SQL_USERNAME`: Your Azure SQL username (e.g., `CloudSA8bd104de`)
- `AZURE_SQL_PASSWORD`: Your Azure SQL password

### 3. Workflow Configuration

The workflow runs:
- **Daily at 8:00 AM UTC** (modify the cron expression in the workflow file if needed)
- **Manually** via the "Actions" tab in GitHub (workflow_dispatch trigger)

To change the schedule, edit the cron expression in `.github/workflows/tori-data-processing.yml`:
```yaml
schedule:
  - cron: '0 8 * * *'  # Daily at 8:00 AM UTC
```

Common cron expressions:
- `'0 */6 * * *'` - Every 6 hours
- `'0 0 * * *'` - Daily at midnight UTC
- `'0 9 * * 1-5'` - Weekdays at 9:00 AM UTC

### 4. Data Processing

The script:
1. Fetches data from the last 24 hours (for daily runs)
2. Authenticates with Azure AD using OAuth2
3. Calls the TORI API to get CSV data
4. Creates a SQL Server table if it doesn't exist
5. Inserts the processed data into the database

### 5. Monitoring

- Check workflow runs in the "Actions" tab of your GitHub repository
- Logs are available for each workflow run
- Failed runs will send notifications if configured

## File Structure

```
├── .github/
│   └── workflows/
│       └── tori-data-processing.yml  # GitHub Actions workflow
├── main.py                           # Main processing script
├── requirements.txt                  # Python dependencies
└── README.md                        # This file
```

## Migration from Azure Functions

This replaces the Azure Functions setup with:
- GitHub Actions for scheduling (instead of Timer Trigger)
- Environment variables via GitHub Secrets (instead of local.settings.json)
- Standalone Python script (instead of Azure Functions runtime)

The core data processing logic remains the same.
## Testing

To test the workflow:
1. Go to the "Actions" tab in your GitHub repository
2. Select "TORI Data Processing" workflow
3. Click "Run workflow" to trigger it manually
4. Monitor the logs for any issues

## Troubleshooting

1. **Authentication Issues**: Verify CLIENT_ID and CLIENT_SECRET secrets
2. **Database Connection**: Check Azure SQL Database credentials (AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_USERNAME, AZURE_SQL_PASSWORD)
3. **API Access**: Ensure the TORI API endpoint is accessible and credentials are valid
4. **Cron Schedule**: Remember GitHub Actions uses UTC time
5. **Azure SQL Firewall**: Ensure GitHub Actions IP ranges are allowed in your Azure SQL firewall rules

## API Endpoint

The script calls the TORI API endpoint:
```
GET https://tori-agent.maersk-digital.net/reports/?start={start_time}&end={end_time}
```

- Fetches data from the last 24 hours (for daily runs)
- Uses OAuth2 Bearer token authentication
- Expects CSV response format

## Database Schema

The script automatically creates a `ToriReports` table with:
- `ID`: Auto-incrementing primary key
- `ProcessedDate`: Timestamp when record was processed
- Dynamic columns based on CSV headers (all as NVARCHAR(MAX))

## Migration Notes

This GitHub Actions version:
- Runs daily instead of every 30 minutes
- Uses environment variables instead of local.settings.json
- Removes Azure Functions dependencies
- Maintains the same core data processing logic
