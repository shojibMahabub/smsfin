# FinTrack - SMS Finance Tracker

## Project Overview

**FinTrack** is an intelligent SMS finance tracker that parses financial transaction SMS messages, categorizes spending, generates reports, and provides forecasts using local AI (Ollama).

## Mission

Track and analyze financial data from phone SMS, categorize transactions, generate reports, and provide forecasts/notifications.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Interactive mode (prompts; uses config.yaml defaults)
python -m src.cli.main interactive

# Pipeline with config.yaml defaults (sender filter + ollama parser by default)
python -m src.cli.main pipeline -s csv -i data.csv -o output.xlsx

# Fast pipeline (no AI)
python -m src.cli.main pipeline -s csv -i data.csv -o output.xlsx \
  --filter sender --parser regex

# Custom config file
python -m src.cli.main --config /path/to/config.yaml pipeline -i data.csv -s csv

# Run analytics on Excel output
python -m src.cli.main analyze output.xlsx

# Generate forecast
python -m src.cli.main forecast output.xlsx

# List financial senders
python -m src.cli.main senders
```

## Execution Paths

| Path | Command | Behavior |
|------|---------|----------|
| Config-driven | `pipeline`, `interactive` | Loads `config.yaml`, merges CLI flag overrides |
| Legacy | `parse-gsheet` | NRB regex via `processor.build_rows`, full Excel workbook |

**Override precedence:** CLI flags > `config.yaml` > built-in defaults.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI (src/cli/main.py)                    │
│              --config  pipeline | interactive                │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              Config (src/core/config.py)                       │
│         YAML load + ${ENV} expansion + CLI merge             │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              Pipeline (src/core/pipeline.py)                   │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐                    │
│  │ Source  │──▶│ Filter  │──▶│ Parser  │                    │
│  │ csv /   │   │ sender /│   │ ollama /│                    │
│  │ sheets  │   │ ollama  │   │ regex   │                    │
│  └─────────┘   └─────────┘   └─────────┘                    │
│                              ┌──────────▼──────────┐        │
│                              │ Output excel / json │        │
│                              └─────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│         Analytics | Forecasting | Notifications (plugins)    │
└─────────────────────────────────────────────────────────────┘

Legacy: processor.py + nrb.py ──▶ parse-gsheet (multi-sheet Excel)
```

## Commands

| Command | Description |
|---------|-------------|
| `interactive` / `i` | Guided prompts; defaults from config |
| `pipeline` | Full pipeline via Config + Pipeline |
| `analyze` | Analytics on Excel output |
| `forecast` | Spending forecasts |
| `senders` | List financial senders (add/remove not implemented) |
| `parse-gsheet` | Legacy Google Sheet → NRB regex → full Excel |

Global flag: `--config PATH` — custom config file (auto-detects `config.yaml` in cwd or project root).

## Pipeline Options

```bash
# Config defaults + analytics (when analytics.enabled: true)
python -m src.cli.main pipeline -s csv -i data.csv -o output.xlsx --analyze

# Override filter/parser from config
python -m src.cli.main pipeline -s csv -i data.csv -o output.xlsx \
  --filter sender --parser regex --forecast
```

### Pipeline Arguments

| Argument | Options | Description |
|----------|---------|-------------|
| `-s, --source` | `csv`, `google_sheet` | Input source (default: config) |
| `-i, --input` | path/URL | Input file or sheet URL |
| `-o, --output` | path | Output file (default: `output.xlsx`) |
| `-c, --credentials` | path | Google service account JSON |
| `--filter` | `none`, `ollama`, `sender` | SMS classifier (default: config) |
| `--parser` | `none`, `regex`, `ollama` | Transaction parser (default: config) |
| `--analyze` | flag | Run spending analytics after pipeline |
| `--forecast` | flag | Run forecasting after pipeline |

## Configuration

Edit [`config.yaml`](config.yaml). Valid filter types: **`sender`**, **`ollama`** (not `keyword`).

Environment placeholders are expanded on load:

- `${VAR}` — replaced with env value, or empty if unset
- `${VAR:-default}` — replaced with env value, or `default` if unset

Example:

```yaml
filters:
  - type: sender
    enabled: true

parsers:
  - type: ollama
    model: gemma4:e4b
    enabled: true
    fallback: regex

sources:
  - type: google_sheets
    sheet_url: "${GOOGLE_SHEET_URL}"
    credentials: "${GOOGLE_CREDENTIALS:-credentials.json}"

outputs:
  - type: excel
    enabled: true

analytics:
  enabled: true
  anomaly_threshold: 5000

forecasting:
  model: linear
  periods: 3
```

```bash
export GOOGLE_SHEET_URL="https://docs.google.com/spreadsheets/d/..."
export GOOGLE_CREDENTIALS="credentials.json"
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

## Filter System

### Sender Filter (fast)
- Uses `FINANCIAL_SENDERS` in `src/models/senders.py`
- Enabled sender (`True`) → transaction; disabled → promotional

### Ollama Filter (AI)
- Parallel batch classification with progress (`classify_batch`)
- Classifies: transaction, otp, login, promotional, chat, unknown

## Parser System

### Ollama Parser
- Extracts structured fields via local LLM
- Falls back to regex parser on failure

### Regex Parser
- Bank-specific patterns in `src/parsers/`:
  - **NRB Bank** (`nrb.py`)
  - **Dhaka Bank** (`dhaka_bank.py`) — senders `DHAKA BANK`, `DHAKABANK.`
  - **DBBL** (`dbbl.py`) — sender `16216`
  - **bKash** (`bkash.py`) — senders `bKash`, `bKashNotice`
- Unmatched SMS are skipped; use Ollama parser for other providers or new regex modules

## Analytics Modules

| Module | Description |
|--------|-------------|
| `spending` | Totals, top category, monthly average |
| `trends` | Monthly and category trends |
| `anomaly` | Large/unusual transactions |

```bash
python -m src.cli.main analyze output.xlsx -m spending -d
```

## Forecasting

1. **Linear** (default): regression on monthly totals
2. **LLM**: Ollama with reasoning

```bash
python -m src.cli.main forecast output.xlsx -m linear
python -m src.cli.main forecast output.xlsx -m llm -p 6
```

## Dependencies

From `requirements.txt`:

- `openpyxl` — Excel
- `gspread`, `google-auth`, `google-auth-oauthlib` — Google Sheets
- `pyyaml` — config
- `colorama` — CLI colors (optional)
- `requests` — Telegram (optional)

**External:** [Ollama](https://ollama.com) CLI + model (e.g. `ollama pull gemma4:e4b`)

## File Structure

```
src/
├── cli/main.py              # CLI entry point
├── core/
│   ├── config.py            # YAML + env expansion + CLI merge
│   ├── pipeline.py          # Pipeline orchestrator
│   └── processor.py         # Legacy build_rows + summaries
├── models/
│   ├── ledger.py            # LedgerRow
│   └── senders.py           # FINANCIAL_SENDERS
├── parsers/
│   ├── filters/             # sender, ollama
│   ├── implementations/     # regex, ollama
│   └── nrb.py               # NRB Bank regex
├── io/
│   ├── sources/             # csv, google_sheets
│   ├── outputs/             # excel, json
│   └── notifications/       # telegram
├── analytics/modules/
├── forecasting/models/
└── plugins/                 # Plugin registry
```

## Adding New Components

### Add New Sender

Edit `src/models/senders.py`:

```python
FINANCIAL_SENDERS = {
    "MyBank": True,
    "PromoSender": False,
}
```

### Add New Parser Plugin

1. Create `src/parsers/implementations/my_parser.py` with `plugin = MyParser`
2. Register in `src/parsers/implementations/__init__.py`

### Add Notification Channel

1. Create `src/io/notifications/channels/my_channel.py`
2. Register in `src/io/notifications/channels/__init__.py`

## Data Format

### Input CSV

```csv
Date,From,Empty,Content,Device
"May 24, 2025 at 01:23 PM",NRB Bank,,"NRB Credit Card Bill...",Samsung
```

Required columns: `Date`, `From`, `Content`

### Output Excel

| Command | Sheets |
|---------|--------|
| `pipeline` / `interactive` | **Ledger** only |
| `parse-gsheet` | Ledger, Summary, Categories, Account Totals |

## Current Limitations

- Telegram is configured in `config.yaml` but **not sent** by CLI after pipeline
- `senders --add` / `--remove` not implemented
- Regex parser: NRB Bank only unless Ollama parser is used
- Default config uses Ollama parser (slow on large exports)

## Troubleshooting

### Ollama not running

```bash
ollama serve
ollama pull gemma4:e4b
```

### No transactions parsed

1. Check senders: `python -m src.cli.main senders`
2. Fast path: `--filter sender --parser regex`
3. Verbose analytics: `analyze -d`

### Slow processing

```bash
python -m src.cli.main pipeline -s csv -i data.csv -o out.xlsx \
  --filter sender --parser regex
```

## License

Private - For personal use only
