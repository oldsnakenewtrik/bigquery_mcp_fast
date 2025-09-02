#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { z } from "zod";
import { BigQuery } from "@google-cloud/bigquery";
import express from "express";
import fs from "node:fs";
let bigqueryOptions = {};
const keyFile = process.env.GOOGLE_APPLICATION_CREDENTIALS;
const credsJson = process.env.GOOGLE_APPLICATION_CREDENTIALS_JSON;
if (credsJson) {
    bigqueryOptions.credentials = JSON.parse(credsJson);
}
else if (keyFile) {
    if (!fs.existsSync(keyFile)) {
        throw new Error(`Service account file not found at path: ${keyFile}`);
    }
    bigqueryOptions.keyFilename = keyFile;
}
else {
    throw new Error("Either GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable is required");
}
const bigquery = new BigQuery(bigqueryOptions);
const server = new McpServer({
    name: "bigquery-mcp",
    version: "0.1.0",
});
server.tool("run_query", {
    sql: z.string().describe("Standard SQL query to execute in BigQuery"),
    params: z.record(z.unknown()).optional().describe("Named query parameters"),
    location: z.string().optional().describe("Optional job location override"),
}, async ({ sql, params, location }) => {
    try {
        const options = { query: sql, params };
        if (location)
            options.location = location;
        const [rows] = await bigquery.query(options);
        if (!Array.isArray(rows)) {
            return {
                content: [{ type: "text", text: JSON.stringify([], null, 2) }],
            };
        }
        return {
            content: [{ type: "text", text: JSON.stringify(rows, null, 2) }],
        };
    }
    catch (err) {
        return {
            content: [{ type: "text", text: `BigQuery error: ${err?.message || String(err)}` }],
            isError: true,
        };
    }
});
server.tool("list_datasets", {}, async () => {
    try {
        const [datasets] = await bigquery.getDatasets();
        const names = datasets.map((d) => d.id);
        return { content: [{ type: "text", text: JSON.stringify(names, null, 2) }] };
    }
    catch (err) {
        return { content: [{ type: "text", text: `BigQuery error: ${err?.message || String(err)}` }], isError: true };
    }
});
server.tool("list_tables", {
    datasetId: z.string().describe("Dataset ID to list tables from"),
}, async ({ datasetId }) => {
    try {
        const [tables] = await bigquery.dataset(datasetId).getTables();
        const names = tables.map((t) => t.id);
        return { content: [{ type: "text", text: JSON.stringify(names, null, 2) }] };
    }
    catch (err) {
        return { content: [{ type: "text", text: `BigQuery error: ${err?.message || String(err)}` }], isError: true };
    }
});
// @ts-ignore
const app = express();
// @ts-ignore
const transport = new SSEServerTransport(app, '/sse');
await server.connect(transport);
const port = process.env.PORT || 3000;
app.listen(port, () => {
    console.error(`BigQuery MCP server running on port ${port}`);
});
