# Workbook Contract — Observed Legacy Prototype

> **Status:** This describes the **previous Excel/VBA prototype**, not a final, approved workbook schema for the C# add-in. Obtain and inspect the real workbook before final implementation or migration. The column list is a historical baseline only.

## Observed worksheet and table

Worksheet: `Symbols`; Excel table: `TblSymbols`.

| Field | Ownership | Meaning / caveat |
|---|---|---|
| `Symbol` | User | Ticker label, editable |
| `FullName` | Data | Long security name |
| `InsCode` | User | **Text identifier**; digits must be preserved exactly |
| `ISIN` | User | Instrument ISIN, where known |
| `TradingStatus` | Data | Added to legacy table after `ISIN`; derived from individual instrument state |
| `LastPrice` | Data | Last traded price |
| `LastChangePct` | Data calculation | Excel numeric fraction, shown as percent |
| `BuyValue` | Derived data | **Estimated** retail buy value, in IRR |
| `BuyerCount` | Data | Retail buyer count |
| `SellValue` | Derived data | **Estimated** retail sell value, in IRR |
| `SellerCount` | Data | Retail seller count |
| `BuyQueueVol` | Data calculation | Buy queue volume if order book and price limits are trustworthy |
| `SellQueueVol` | Data calculation | Sell queue volume |
| `BuyPerCapita` | User formula | Retail purchase value per buyer |
| `SellPerCapita` | User formula | Retail sale value per seller |
| `PE` | Data | P/E, nullable/unavailable in some responses |
| `ClosePrice` | Data | Closing price |
| `TradeValue` | Data | Exchange-reported traded value; confirm original units |
| `BuyerPower` | User formula | Buy-per-capita / sell-per-capita when denominator > 0 |
| `NetRealMoneyFlow` | Derived data | Estimated `BuyValue - SellValue` |

A later user-discussed display column (originally titled in Persian, meaning **Status**) may be formula-driven; its presence in the current workbook has **not been verified**. The add-in must not overwrite any user-owned formula column.

## Historical formulas and estimates

```text
BuyValue       = buy_I_Volume * LastPrice
SellValue      = sell_I_Volume * LastPrice
BuyPerCapita   = IF(BuyerCount > 0, BuyValue / BuyerCount, 0)
SellPerCapita  = IF(SellerCount > 0, SellValue / SellerCount, 0)
BuyerPower     = IF(SellPerCapita > 0, BuyPerCapita / SellPerCapita, 0)
NetRealMoneyFlow = BuyValue - SellValue
LastChangePct  = (LastPrice / PreviousPrice) - 1, if PreviousPrice > 0
```

`BuyValue` and `SellValue` estimate IRR notional using aggregate volume multiplied by a single last price; they are **not** exact transaction-by-transaction execution amounts. Never present them as exact executed cashflows. Preserve IRR/IRT distinctions.

## Trading-state evidence

Legacy tests observed `instrumentState.cEtaval` values:

| Raw code (trimmed) | Source title (English translation) | Normalized state |
|---|---|---|
| `A` | Permitted | `ACTIVE` |
| `IS` | Prohibited / Halted | `HALTED` |
| Other or missing | Not verified | `UNKNOWN` until verified |

The test instruments SHPNA (`7745894403636165`) and FGOSTAR (`8725363201030474`) were absent from a bulk MarketWatch response but had valid details and `IS` status in the individual API. Missing in bulk data **does not establish invalid ID or halted state**.

A user-visible formula column may present `HALTED` as halted, otherwise require `ACTIVE` before using current queue volumes to call buy-queue, sell-queue, or normal. Unknown or failed status must not be silently labeled normal. Queue data must have adequate freshness before being presented as current.

## Write safety and migration

- Treat `Symbol`, `InsCode`, `ISIN`, and user formula columns as **user-owned**. Never clear or overwrite them during refresh.
- Update by named table columns, not fixed numeric offsets. Reject or report unexpected schema without destructive writes.
- Preserve old valid values on API failure and clearly mark their freshness/quality. A missing record is not valid evidence of numeric zero.
- Do not hard-code 37 symbols, ticker order, or the original prototype layout into business logic.
- Obtain PO approval for schema changes; provide migration/rollback strategy and automated tests.

## Source mappings observed previously (require revalidation)

- Bulk: `ClosingPrice/GetMarketWatch`; retail participants: `ClientType/GetClientTypeAll`.
- Individual: `ClosingPrice/GetClosingPriceInfo/{InsCode}` for trading date/time and `instrumentState`.
- Limits: `MarketData/GetStaticThreshold/{InsCode}/{TradeDate}` for order-book queue matching.
- Historic interpretation: `pdv` last price, `pcl` close price, `qtc` traded value, `pe` P/E, `py` previous reference price. Revalidate against live official data and current endpoint shapes before treating mappings as stable.
