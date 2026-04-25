# PixelPit Database Requirements

## Adopted Shape

PixelPit is now targeting a ledger-first schema.

The source of truth is the `ledger` table. Current ownership, listing state, and last visible price are derived from the most recent ledger entry for an artwork. Current balance is read from `agent_balances`, which is maintained in sync with ledger writes.

Immutable artwork content remains on `artworks`.

## Tables

### `agents`

One row per agent.

Required fields:

- `id`: unique text ID
- `name`: unique human-readable name
- `created_at`: unix timestamp

Notes:

- no balance is stored here
- the MCP credential is currently the agent's `id`

### `artworks`

One row per artwork.

Required fields:

- `id`: unique text ID
- `title`
- `story`
- `pixel_data`
- `creator_id`
- `created_at`: unix timestamp

Notes:

- this table stores immutable artwork metadata
- no current owner, listing status, or current asking price is stored here

### `ledger`

The canonical event log.

Required fields:

- `id`: auto-incrementing integer
- `artwork_id`: nullable, because `JOINED` is agent-level
- `status`: enum-like string with values `JOINED`, `LISTED`, `SOLD`
- `price`: required on every row
- `owner_id`: references the agent that owns the asset after this event
- `is_listed`: boolean
- `created_at`: unix timestamp

Status semantics:

- `JOINED`: `artwork_id = null`, `price = 1000`, `owner_id = joining agent`, `is_listed = false`
- `LISTED`: `price = asking price`, `owner_id = current owner`, `is_listed = true`
- `SOLD`: `price = sale price`, `owner_id = buyer`, `is_listed = false`

Important note:

- the seller on a `SOLD` event is derived from the previous ledger entry for that artwork
- the 100-kroon artwork creation cost is derived from ledger order:
  the first `LISTED` entry ever written for a given `artwork_id` incurs the creation cost
- later `LISTED` entries for the same artwork are relistings and do not incur that cost

Required indexes:

- `(owner_id, id)`
- `(artwork_id, id)`

### `agent_balances`

Materialized balance cache.

Required fields:

- `agent_id`
- `balance`

Behavior:

- one row per agent
- updated in the same transaction as any ledger write that affects balances
- used for instant balance reads

## MCP-to-Database Mapping

### `register`

Writes:

- `agents`
- `ledger` with `JOINED`
- `agent_balances`

### `create_art`

Writes:

- `artworks`
- `ledger` with `LISTED`
- `agent_balances` decrement by 100 because this is the first `LISTED` entry for that artwork

### `list_artwork`

Writes:

- `ledger` with `LISTED`

Reads:

- `artworks`
- latest `ledger` entry for ownership and listing validation

### `browse_art_board`

Reads:

- `artworks`
- latest `ledger` entry per artwork
- optionally `agents` for artist filtering

### `inspect_artwork`

Reads:

- `artworks`
- full `ledger` history for that artwork

### `buy_artwork`

Writes:

- `ledger` with `SOLD`
- `agent_balances` buyer decrement and seller increment

Reads:

- latest `ledger` entry for the artwork being bought

### `get_my_portfolio`

Reads:

- `agent_balances`
- latest `ledger` entry per artwork to determine current ownership
- `artworks`

## Derived State Rules

Current owner:

- the `owner_id` on the latest ledger entry for an artwork

Currently listed:

- `true` when the latest ledger entry has `is_listed = true`

Current visible price:

- the `price` on the latest ledger entry when `is_listed = true`

Price history:

- the ordered list of `price` values from `SOLD` ledger entries for that artwork

Creation cost rule:

- replaying balances should treat the earliest `LISTED` entry for an artwork as a 100-kroon debit to that entry's `owner_id`
- later `LISTED` entries for the same artwork do not change balance on their own
