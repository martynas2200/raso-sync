# raso-sync

A custom Frappe app that provides XML API endpoints for syncing data between ERPNext and RASO POS system.

## Features

- Direct XML Response: Returns XML documents directly (not JSON with embedded XML)

## API Endpoints

### Main Endpoint

**URL**: `/api/method/raso_sync.api.sync.sync`

**Parameters**:
- `DataType` (required): 1, 2, 3, or 4
- `FullSync` (optional): 1 for full sync, 0 for incremental (default: 1)
- `recentModified` (required when FullSync=0): ISO datetime (YYYY-MM-DDTHH:MM:SS)

### Individual Endpoints

| DataType | Description    | Frappe DocType    | Individual Endpoint                                      |
|----------|----------------|-------------------|----------------------------------------------------------|
| 1        | Partners       | `Customer`        | `/api/method/raso_sync.api.partners.partners`            |
| 2        | GoodsGroups    | `Item Group`      | `/api/method/raso_sync.api.goods_groups.goods_groups`    |
| 3        | Goods          | `Item`            | `/api/method/raso_sync.api.goods.goods`                  |
| 4        | GoodsPrices    | `Item Price`      | `/api/method/raso_sync.api.goods_prices.goods_prices`    |
