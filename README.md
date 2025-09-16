# BigQuery MCP Server

A Model Context Protocol (MCP) server for Google BigQuery integration. This server provides tools for querying BigQuery datasets, listing tables, and managing multiple BigQuery projects.

## ⚠️ Security Notice

This project requires Google Cloud service account credentials. **NEVER** commit actual credentials to version control. Always use environment variables or secure credential management systems.

## Features

- Execute SQL queries against BigQuery
- List datasets and tables
- Support for multiple BigQuery projects
- Both Python (FastMCP) and TypeScript implementations
- Secure credential handling via environment variables

## Prerequisites

1. Google Cloud Project with BigQuery API enabled
2. Service account with appropriate BigQuery permissions:
   - `roles/bigquery.user`
   - `roles/bigquery.dataViewer` (or more specific dataset permissions)
3. Node.js 18+ (for TypeScript version)
4. Python 3.8+ (for Python version)

## Installation

### TypeScript Version

```bash
npm install
npm run build
```

### Python Version

```bash
cd bigquery-mcp
pip install -r requirements.txt
```

## Configuration

### 1. Set up Google Cloud Credentials

Choose one of the following methods:

**Option A: Service Account File**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account.json
```

**Option B: JSON String (for cloud deployment)**
```bash
export GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account",...}'
```

### 2. Set Project ID
```bash
export BIGQUERY_PROJECT=your-project-id
```

### 3. Copy Example Files
```bash
# Copy environment example
cp bigquery-mcp/.env.example bigquery-mcp/.env

# Edit with your values
vim bigquery-mcp/.env
```

## Usage

### TypeScript Server
```bash
npm start
```

### Python Server
```bash
cd bigquery-mcp
python server.py
```

## Available Tools

- `run_query(sql, project_id?)` - Execute SQL queries
- `list_datasets(project_id?)` - List available datasets
- `list_tables(dataset_id, project_id?)` - List tables in a dataset
- `test_bigquery_connection()` - Test connectivity
- `debug_credentials()` - Debug credential setup

## Security Best Practices

1. **Never commit credentials**: Use `.gitignore` to exclude credential files
2. **Use environment variables**: Store sensitive data in environment variables
3. **Principle of least privilege**: Grant minimal required permissions
4. **Rotate credentials**: Regularly rotate service account keys
5. **Monitor access**: Enable audit logging for BigQuery access

## FastMCP Deployment

For FastMCP cloud deployment, use the `GOOGLE_APPLICATION_CREDENTIALS_JSON` environment variable:

```json
{
  "deployment": {
    "env": {
      "GOOGLE_APPLICATION_CREDENTIALS_JSON": "${YOUR_CREDENTIALS_JSON}",
      "BIGQUERY_PROJECT": "${YOUR_PROJECT_ID}"
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Authentication errors**: Verify credentials and project ID
2. **Permission denied**: Check IAM roles and dataset permissions
3. **Client not initialized**: Ensure environment variables are set correctly

### Debug Tools

Use the built-in debug tools:
- `test_bigquery_connection()` - Test basic connectivity
- `debug_credentials()` - Check credential configuration
- `test_json_parsing()` - Verify JSON credential format

## Contributing

1. Ensure no credentials are committed
2. Update `.gitignore` for any new credential patterns
3. Test with environment variables only
4. Follow security best practices

## License

MIT License - see LICENSE file for details
