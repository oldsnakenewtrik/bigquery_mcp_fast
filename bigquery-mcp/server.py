#!/usr/bin/env python3
"""
BigQuery MCP Server using FastMCP
"""

import os
import json
import sys
from typing import Dict, Any, Optional

# Debug: Print Python path and version info
print(f"DEBUG: Python version: {sys.version}", file=sys.stderr, flush=True)
print(f"DEBUG: Python path: {sys.path}", file=sys.stderr, flush=True)

# Try to import required modules and provide debugging info
try:
    from fastmcp import FastMCP
    print("DEBUG: FastMCP imported successfully", file=sys.stderr, flush=True)
except ImportError as e:
    print(f"DEBUG: FastMCP import failed: {e}", file=sys.stderr, flush=True)
    raise

try:
    from google.cloud import bigquery
    print("DEBUG: google.cloud.bigquery imported successfully", file=sys.stderr, flush=True)
except ImportError as e:
    print(f"DEBUG: google.cloud.bigquery import failed: {e}", file=sys.stderr, flush=True)
    # Check if google package exists at all
    try:
        import google
        print(f"DEBUG: google package found at: {google.__file__}", file=sys.stderr, flush=True)
    except ImportError:
        print("DEBUG: No google package found at all", file=sys.stderr, flush=True)
    raise

try:
    from google.oauth2 import service_account
    print("DEBUG: google.oauth2.service_account imported successfully", file=sys.stderr, flush=True)
except ImportError as e:
    print(f"DEBUG: google.oauth2.service_account import failed: {e}", file=sys.stderr, flush=True)
    raise

# Initialize FastMCP server
mcp = FastMCP("BigQuery MCP Server")

def get_bigquery_client():
    """Initialize BigQuery client with credentials"""
    import sys
    print("DEBUG: Starting BigQuery client initialization...", file=sys.stderr, flush=True)

    # Try environment variable first (for FastMCP deployment)
    creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    print(f"DEBUG: GOOGLE_APPLICATION_CREDENTIALS_JSON present: {creds_json is not None}", file=sys.stderr, flush=True)
    if creds_json:
        try:
            print("DEBUG: Parsing JSON credentials...", file=sys.stderr, flush=True)
            # Log first 100 chars to see if JSON looks valid
            print(f"DEBUG: JSON preview: {creds_json[:100]}...", file=sys.stderr, flush=True)
            creds_dict = json.loads(creds_json.strip())
            print(f"DEBUG: JSON parsed successfully, project_id: {creds_dict.get('project_id')}", file=sys.stderr, flush=True)
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            print("DEBUG: Credentials created successfully", file=sys.stderr, flush=True)
            print(f"DEBUG: Creating BigQuery client with project: {creds_dict.get('project_id')}", file=sys.stderr, flush=True)
            client = bigquery.Client(credentials=credentials)
            print("DEBUG: BigQuery client created successfully", file=sys.stderr, flush=True)
            return client
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON parsing failed: {e}", file=sys.stderr, flush=True)
            print(f"DEBUG: JSON content length: {len(creds_json)}", file=sys.stderr, flush=True)
            return None
        except Exception as e:
            print(f"DEBUG: Credentials creation failed: {e}", file=sys.stderr, flush=True)
            return None

    # Fallback to credentials file
    creds_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    print(f"DEBUG: GOOGLE_APPLICATION_CREDENTIALS: {creds_file}", file=sys.stderr, flush=True)
    if creds_file and os.path.exists(creds_file):
        try:
            print(f"DEBUG: Loading credentials from file: {creds_file}", file=sys.stderr, flush=True)
            return bigquery.Client.from_service_account_json(creds_file)
        except Exception as e:
            print(f"DEBUG: File credentials failed: {e}", file=sys.stderr, flush=True)
            return None

    # Try local credentials file (for local development)
    local_creds = os.path.join(os.path.dirname(__file__), 'service-account.json')
    print(f"DEBUG: Checking local credentials file: {local_creds}", file=sys.stderr, flush=True)
    if os.path.exists(local_creds):
        try:
            print("DEBUG: Loading local credentials file...", file=sys.stderr, flush=True)
            return bigquery.Client.from_service_account_json(local_creds)
        except Exception as e:
            print(f"DEBUG: Local credentials failed: {e}", file=sys.stderr, flush=True)
            return None

    # Default client (uses Application Default Credentials)
    try:
        print("DEBUG: Trying Application Default Credentials...", file=sys.stderr, flush=True)
        return bigquery.Client()
    except Exception as e:
        print(f"DEBUG: Default credentials failed: {e}", file=sys.stderr, flush=True)
        return None

# Initialize BigQuery clients (support multiple projects)
print("DEBUG: Initializing BigQuery clients...", file=sys.stderr, flush=True)
bq_clients = {}  # Dictionary to store clients by project_id
bq_client = None  # Default client for backward compatibility

def initialize_clients_from_env():
    """Initialize BigQuery clients from environment variables"""
    global bq_client

    # Look for multiple project credentials
    project_count = 1
    while True:
        env_name = f"GOOGLE_APPLICATION_CREDENTIALS_JSON_PROJECT{project_count}" if project_count > 1 else "GOOGLE_APPLICATION_CREDENTIALS_JSON"
        creds_json = os.getenv(env_name)

        if not creds_json:
            if project_count == 1:
                # Try the original method for the first project
                continue
            else:
                break  # No more projects

        print(f"DEBUG: Found credentials for project {project_count}: {env_name}", file=sys.stderr, flush=True)

        try:
            creds_dict = json.loads(creds_json.strip())
            project_id = creds_dict.get('project_id')

            if not project_id:
                print(f"DEBUG: Skipping project {project_count}: missing project_id", file=sys.stderr, flush=True)
                project_count += 1
                continue

            # Create credentials and client
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            client = bigquery.Client(credentials=credentials)

            # Test the connection
            datasets = list(client.list_datasets(max_results=1))
            print(f"DEBUG: Successfully initialized client for project: {project_id} ({len(datasets)} datasets)", file=sys.stderr, flush=True)

            # Store the client
            bq_clients[project_id] = client

            # Set as default if it's the first one
            if not bq_client:
                bq_client = client
                print(f"DEBUG: Set {project_id} as default project", file=sys.stderr, flush=True)

        except Exception as e:
            print(f"DEBUG: Failed to initialize project {project_count}: {e}", file=sys.stderr, flush=True)

        project_count += 1

    # If no environment variables found, try the original method
    if not bq_clients:
        print("DEBUG: No environment credentials found, trying original method...", file=sys.stderr, flush=True)
        try:
            default_client = get_bigquery_client()
            if default_client:
                project_id = default_client.project
                bq_clients[project_id] = default_client
                bq_client = default_client
                print(f"DEBUG: BigQuery client initialized for project: {project_id}", file=sys.stderr, flush=True)
            else:
                print("DEBUG: get_bigquery_client() returned None", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"DEBUG: Failed to initialize BigQuery client: {e}", file=sys.stderr, flush=True)

# Initialize all clients
initialize_clients_from_env()

print(f"DEBUG: Total projects initialized: {len(bq_clients)}", file=sys.stderr, flush=True)
for project_id in bq_clients.keys():
    print(f"DEBUG: Available project: {project_id}", file=sys.stderr, flush=True)

def get_client_for_project(project_id: str = None):
    """Get BigQuery client for specific project or default"""
    if project_id and project_id in bq_clients:
        return bq_clients[project_id]
    elif bq_clients:
        return list(bq_clients.values())[0]  # Return first available client
    return None

@mcp.tool
def run_query(sql: str, project_id: str = None) -> str:
    """
    Execute an arbitrary SQL statement against BigQuery.

    Args:
        sql: The SQL query to execute
        project_id: Optional project ID to run query against (uses default if not specified)

    Returns:
        JSON string of query results
    """
    client = get_client_for_project(project_id)
    if not client:
        return json.dumps({"error": "BigQuery client not initialized"})

    try:
        query_job = client.query(sql)
        results = query_job.result()

        # Convert results to list of dicts
        rows = []
        for row in results:
            rows.append(dict(row))

        if not rows:
            return json.dumps([], indent=2)

        return json.dumps(rows, indent=2, default=str)

    except Exception as e:
        return json.dumps({"error": f"BigQuery error: {str(e)}"})

@mcp.tool
def list_datasets(project_id: str = None) -> str:
    """
    List all dataset IDs in the specified project.

    Args:
        project_id: Optional project ID (uses default if not specified)

    Returns:
        JSON array of dataset IDs
    """
    client = get_client_for_project(project_id)
    if not client:
        return json.dumps({"error": "BigQuery client not initialized"})

    try:
        datasets = list(client.list_datasets())
        dataset_ids = [dataset.dataset_id for dataset in datasets]
        return json.dumps({
            "project": client.project,
            "datasets": dataset_ids
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"BigQuery error: {str(e)}"})

@mcp.tool
def test_bigquery_connection() -> str:
    """
    Test BigQuery client creation and basic connectivity.

    Returns:
        Information about BigQuery client creation and connection test
    """
    try:
        print("DEBUG: Testing BigQuery client creation...", file=sys.stderr, flush=True)
        client = get_bigquery_client()
        if not client:
            return json.dumps({"success": False, "error": "BigQuery client creation failed"})

        print("DEBUG: Testing basic BigQuery operation...", file=sys.stderr, flush=True)
        # Try a simple operation to test connectivity
        datasets = list(client.list_datasets(max_results=1))
        return json.dumps({
            "success": True,
            "project": client.project,
            "datasets_found": len(datasets),
            "test_query_successful": True
        })
    except Exception as e:
        print(f"DEBUG: BigQuery test failed: {e}", file=sys.stderr, flush=True)
        return json.dumps({
            "success": False,
            "error": f"BigQuery connection test failed: {str(e)}"
        })

@mcp.tool
def test_json_parsing() -> str:
    """
    Test JSON parsing of the credentials without creating BigQuery client.

    Returns:
        Information about JSON parsing success/failure
    """
    creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if not creds_json:
        return json.dumps({"error": "GOOGLE_APPLICATION_CREDENTIALS_JSON not set"})

    try:
        print(f"DEBUG: Raw JSON length: {len(creds_json)}", file=sys.stderr, flush=True)
        print(f"DEBUG: First 200 chars: {creds_json[:200]}", file=sys.stderr, flush=True)
        print(f"DEBUG: Last 200 chars: {creds_json[-200:]}", file=sys.stderr, flush=True)

        creds_dict = json.loads(creds_json.strip())
        return json.dumps({
            "success": True,
            "project_id": creds_dict.get('project_id'),
            "type": creds_dict.get('type'),
            "client_email": creds_dict.get('client_email'),
            "has_private_key": 'private_key' in creds_dict,
            "private_key_length": len(creds_dict.get('private_key', ''))
        })
    except json.JSONDecodeError as e:
        return json.dumps({
            "success": False,
            "error": f"JSON parsing failed: {str(e)}",
            "error_position": e.pos if hasattr(e, 'pos') else 'unknown'
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        })

@mcp.tool
def debug_credentials() -> str:
    """
    Debug BigQuery credentials and client status.

    Returns:
        Debug information about credentials and client initialization
    """
    debug_info = {
        "bq_client_initialized": bq_client is not None,
        "env_vars_present": {
            "GOOGLE_APPLICATION_CREDENTIALS_JSON": os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON') is not None,
            "GOOGLE_APPLICATION_CREDENTIALS": os.getenv('GOOGLE_APPLICATION_CREDENTIALS') is not None
        },
        "local_creds_file_exists": os.path.exists(os.path.join(os.path.dirname(__file__), 'service-account.json'))
    }

    if bq_client:
        try:
            # Test a simple operation
            datasets = list(bq_client.list_datasets(max_results=1))
            debug_info["test_query_successful"] = True
            debug_info["project"] = bq_client.project
            debug_info["datasets_count"] = len(datasets)
        except Exception as e:
            debug_info["test_query_error"] = str(e)
            debug_info["test_query_successful"] = False
    else:
        debug_info["client_status"] = "BigQuery client is None - check server initialization logs"

    return json.dumps(debug_info, indent=2)

@mcp.tool
def list_tables(dataset_id: str, project_id: str = None) -> str:
    """
    List all table IDs in a specific dataset.

    Args:
        dataset_id: The dataset ID to list tables from
        project_id: Optional project ID (uses default if not specified)

    Returns:
        JSON array of table IDs
    """
    client = get_client_for_project(project_id)
    if not client:
        return json.dumps({"error": "BigQuery client not initialized"})

    try:
        dataset_ref = client.dataset(dataset_id)
        tables = list(client.list_tables(dataset_ref))
        table_ids = [table.table_id for table in tables]
        return json.dumps({
            "project": client.project,
            "dataset": dataset_id,
            "tables": table_ids
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"BigQuery error: {str(e)}"})

@mcp.tool
def list_projects() -> str:
    """
    List all available BigQuery projects that this server can access.

    Returns:
        JSON array of project IDs
    """
    if not bq_clients:
        return json.dumps({"error": "No BigQuery clients initialized"})

    projects = list(bq_clients.keys())
    return json.dumps({
        "available_projects": projects,
        "default_project": list(bq_clients.keys())[0] if projects else None
    }, indent=2)

@mcp.tool
def switch_project(project_id: str) -> str:
    """
    Switch the default project for operations.

    Args:
        project_id: The project ID to set as default

    Returns:
        Confirmation of project switch
    """
    global bq_client

    if project_id not in bq_clients:
        return json.dumps({
            "error": f"Project '{project_id}' not available",
            "available_projects": list(bq_clients.keys())
        })

    bq_client = bq_clients[project_id]
    return json.dumps({
        "success": True,
        "current_project": project_id,
        "available_projects": list(bq_clients.keys())
    }, indent=2)

@mcp.tool
def add_project_credentials(credentials_json: str) -> str:
    """
    Add credentials for a new BigQuery project.

    Args:
        credentials_json: Full JSON credentials string for the new project

    Returns:
        Confirmation of project addition
    """
    try:
        creds_dict = json.loads(credentials_json.strip())
        project_id = creds_dict.get('project_id')

        if not project_id:
            return json.dumps({"error": "Invalid credentials: missing project_id"})

        if project_id in bq_clients:
            return json.dumps({"error": f"Project '{project_id}' already exists"})

        # Create credentials and client
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        new_client = bigquery.Client(credentials=credentials)

        # Test the connection
        datasets = list(new_client.list_datasets(max_results=1))

        # Add to clients dictionary
        bq_clients[project_id] = new_client

        return json.dumps({
            "success": True,
            "project_added": project_id,
            "available_projects": list(bq_clients.keys()),
            "datasets_found": len(datasets)
        }, indent=2)

    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Failed to add project: {str(e)}"})

if __name__ == "__main__":
    mcp.run()