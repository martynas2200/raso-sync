# raso-sync

A custom Frappe app that provides XML API endpoints for syncing data between ERPNext and RASO POS system.

## Features

- Direct XML Response: Returns XML documents directly (not JSON with embedded XML)

## API Endpoints

### Main Endpoint

**URL**: `/api/method/raso_sync.raso_sync.api.sync.sync`

**Parameters**:
- `DataType` (required): 1, 2, 3, or 4
- `FullSync` (optional): 1 for full sync, 0 for incremental (default: 1)
- `recentModified` (required when FullSync=0): ISO datetime (YYYY-MM-DDTHH:MM:SS)

