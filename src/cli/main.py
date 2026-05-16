"""Interactive CLI for SMS Finance Tracker."""

import argparse
import sys
import os
from pathlib import Path
from decimal import Decimal
from typing import Optional

# Try to import colorama for colored output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLOR = True
except ImportError:
    COLOR = False
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = ""
    class Style:
        BRIGHT = DIM = RESET_ALL = ""


def print_header(text: str) -> None:
    """Print header with styling."""
    if COLOR:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
        print(f"{text.center(60)}")
        print(f"{'='*60}{Style.RESET_ALL}\n")
    else:
        print(f"\n{'='*60}")
        print(f"{text.center(60)}")
        print(f"{'='*60}\n")


def print_success(text: str) -> None:
    """Print success message."""
    if COLOR:
        print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")
    else:
        print(f"✓ {text}")


def print_error(text: str) -> None:
    """Print error message."""
    if COLOR:
        print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")
    else:
        print(f"✗ {text}")


def print_warning(text: str) -> None:
    """Print warning message."""
    if COLOR:
        print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")
    else:
        print(f"⚠ {text}")


def print_info(text: str) -> None:
    """Print info message."""
    if COLOR:
        print(f"{Fore.MAGENTA}ℹ {text}{Style.RESET_ALL}")
    else:
        print(f"ℹ {text}")


def load_rows_from_excel(path: str) -> list:
    """Load ledger rows from Excel file."""
    from openpyxl import load_workbook
    wb = load_workbook(path)
    ws = wb.active

    rows = []
    headers = [cell.value for cell in ws[1]]

    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        row_dict = dict(zip(headers, row))

        from src.models.ledger import LedgerRow
        lr = LedgerRow(
            date=str(row_dict.get("date", "")),
            time=str(row_dict.get("time", "")),
            month=str(row_dict.get("month", "")),
            source=str(row_dict.get("source", "")),
            account=str(row_dict.get("account", "")),
            type=str(row_dict.get("type", "")),
            amount=Decimal(str(row_dict.get("amount", 0))) if row_dict.get("amount") else None,
            currency=str(row_dict.get("currency", "BDT")),
            merchant_or_counterparty=str(row_dict.get("merchant_or_counterparty", "")),
            category=str(row_dict.get("category", "")),
            direction=str(row_dict.get("direction", "")),
            balance_after=Decimal(str(row_dict.get("balance_after", 0))) if row_dict.get("balance_after") else None,
            transaction_id=str(row_dict.get("transaction_id", "")),
            card_or_account_hint=str(row_dict.get("card_or_account_hint", "")),
            confidence=str(row_dict.get("confidence", "medium")),
            review_flag=str(row_dict.get("review_flag", "no")),
            review_reason=str(row_dict.get("review_reason", "")),
            original_sms=str(row_dict.get("original_sms", "")),
        )
        rows.append(lr)
    return rows


def get_input(prompt: str, default: str = "") -> str:
    """Get interactive input with default."""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()


def get_choice(prompt: str, choices: list, default: int = 0) -> str:
    """Get choice from list."""
    print(f"\n{prompt}:")
    for i, choice in enumerate(choices):
        marker = "→" if i == default else " "
        print(f"  {marker} {i+1}. {choice}")
    while True:
        try:
            val = input(f"\nSelect (default: {default+1}): ").strip()
            if not val:
                return choices[default]
            idx = int(val) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
            print_error("Invalid choice, try again")
        except ValueError:
            print_error("Invalid choice, try again")


def get_yes_no(prompt: str, default: bool = True) -> bool:
    """Get yes/no input."""
    default_str = "Y/n" if default else "y/N"
    while True:
        val = input(f"{prompt} ({default_str}): ").strip().lower()
        if not val:
            return default
        if val in ("y", "yes"):
            return True
        if val in ("n", "no"):
            return False


def load_app_config(config_path: Optional[str] = None):
    """Load FinTrack configuration."""
    from src.core.config import Config

    if config_path:
        cfg = Config(config_path=config_path)
        if not cfg._config_path:
            cfg.load(config_path)
    else:
        cfg = Config()
    return cfg


def _cli_overrides_from_args(args) -> dict:
    """Build CLI override dict from argparse namespace."""
    overrides = {}
    if getattr(args, "source", None) is not None:
        overrides["source"] = args.source
    if getattr(args, "input", None):
        overrides["input"] = args.input
    if getattr(args, "credentials", None):
        overrides["credentials"] = args.credentials
    if getattr(args, "filter", None) is not None:
        overrides["filter"] = args.filter
    if getattr(args, "parser", None) is not None:
        overrides["parser"] = args.parser
    if getattr(args, "output", None):
        overrides["output"] = args.output
    elif getattr(args, "command", None) == "pipeline":
        overrides["output"] = "output.xlsx"
    if getattr(args, "analyze", False):
        overrides["analyze"] = True
    if getattr(args, "forecast", False):
        overrides["forecast"] = True
    return overrides


def run_post_pipeline(rows: list, runtime_config: dict) -> None:
    """Run analytics and forecasting after pipeline."""
    analytics = runtime_config.get("analytics") or {}
    forecasting = runtime_config.get("forecasting") or {}

    run_analyze = analytics.get("enabled", False)
    run_forecast = forecasting.get("_run", False)

    if run_analyze and rows:
        print_info("Running analytics...")
        from src.analytics.modules.spending import SpendingAnalyzer

        insights = SpendingAnalyzer().analyze(rows)
        for insight in insights[:5]:
            print(f"  {insight.title}: {insight.description}")

    if run_forecast and rows:
        print_info("Running forecast...")
        model_type = forecasting.get("model", "linear")
        periods = forecasting.get("periods", 3)
        if model_type == "llm":
            from src.forecasting.models.llm import LLMForecaster

            forecaster = LLMForecaster({"periods": periods})
        else:
            from src.forecasting.models.linear import LinearForecaster

            forecaster = LinearForecaster({"periods": periods})
        forecasts = forecaster.predict(rows)
        for fc in forecasts:
            print(f"  {fc.period}: ৳{fc.predicted_value:,.0f}")


def execute_pipeline(
    config_path: Optional[str] = None,
    cli_overrides: Optional[dict] = None,
    prompt_missing: bool = False,
) -> int:
    """Run pipeline using config.yaml with optional CLI overrides."""
    from src.core.config import get_enabled_plugin
    from src.core.pipeline import Pipeline

    cfg = load_app_config(config_path)
    if config_path and not cfg.data and Path(config_path).exists():
        cfg.load(config_path)

    overrides = dict(cli_overrides or {})

    if prompt_missing:
        source_cfg = get_enabled_plugin("sources", cfg.data)
        source_type = overrides.get("source") or source_cfg.get("type", "csv")
        if source_type == "google_sheets":
            source_type = "google_sheet"
        if not overrides.get("input"):
            if source_type in ("csv",):
                overrides["input"] = get_input("CSV file path", source_cfg.get("path", "data.csv"))
            else:
                overrides["input"] = get_input(
                    "Google Sheet URL or ID",
                    source_cfg.get("sheet_url", ""),
                )
                if not overrides.get("credentials"):
                    overrides["credentials"] = get_input(
                        "Credentials file path",
                        source_cfg.get("credentials", "credentials.json"),
                    )
        if not overrides.get("output"):
            overrides["output"] = get_input("Output file path", cfg.data.get("_output_path", "output.xlsx"))

    runtime_config = cfg.build_runtime(overrides)
    output_path = runtime_config.get("_output_path", overrides.get("output", "output.xlsx"))

    source_cfg = get_enabled_plugin("sources", runtime_config)
    source_label = source_cfg.get("type", "unknown")
    print_info(f"Reading from {source_label}...")

    try:
        pipeline = Pipeline(runtime_config)
        raw_rows = list(pipeline._get_source().read())  # noqa: SLF001
        print_success(f"Read {len(raw_rows)} rows")

        filter_cfg = get_enabled_plugin("filters", runtime_config)
        if filter_cfg and not runtime_config.get("_skip_filter"):
            print_info(f"Running {filter_cfg.get('type', 'sender')} filter...")

        parser_cfg = get_enabled_plugin("parsers", runtime_config)
        if parser_cfg and not runtime_config.get("_skip_parser"):
            print_info(f"Running {parser_cfg.get('type', 'regex')} parser...")

        rows = pipeline.process(raw_rows)
        print_success(f"Parsed {len(rows)} transactions")

        if rows:
            total_amount = sum(float(r.amount or 0) for r in rows)
            print_info(f"Total value: ৳{total_amount:,.0f}")

        print_info(f"Writing to {output_path}...")
        pipeline.write_output(rows, output_path)
        print_success(f"Output written to {output_path}")

        if overrides.get("analyze"):
            runtime_config.setdefault("analytics", {})["enabled"] = True
        if overrides.get("forecast"):
            runtime_config.setdefault("forecasting", {})["_run"] = True

        run_post_pipeline(rows, runtime_config)

    except Exception as e:
        print_error(f"Pipeline failed: {e}")
        return 1

    return 0


def run_interactive(config_path: Optional[str] = None) -> int:
    """Run interactive mode."""
    print_header("FinTrack - SMS Finance Tracker")

    print_info("Welcome to FinTrack!")
    print("This tool helps you parse SMS transactions, analyze spending, and forecast expenses.\n")

    cfg = load_app_config(config_path)
    from src.core.config import get_enabled_plugin

    filter_default = get_enabled_plugin("filters", cfg.data).get("type", "sender")
    parser_default = get_enabled_plugin("parsers", cfg.data).get("type", "ollama")
    filter_idx = 0 if filter_default == "ollama" else 1
    parser_idx = 0 if parser_default == "ollama" else 1

    print_header("Step 1: Select Data Source")
    source_type = get_choice(
        "Select input source",
        ["Google Sheets", "CSV File"],
        default=1
    )

    source_arg = "google_sheet" if source_type == "Google Sheets" else "csv"

    creds = None
    if source_type == "Google Sheets":
        input_path = get_input("Google Sheet URL or ID", "")
        if not input_path:
            print_error("Google Sheet URL is required")
            return 1

        creds = get_input("Credentials file path", "credentials.json")
    else:
        input_path = get_input("CSV file path", "data.csv")
        if not input_path or not Path(input_path).exists():
            print_error(f"File not found: {input_path}")
            return 1

    # Step 2: Select filter
    print_header("Step 2: Select Filter")
    filter_type = get_choice(
        "Select filter type",
        ["Ollama (AI-powered)", "Sender-based (fast)"],
        default=filter_idx,
    )

    filter_arg = "ollama" if "Ollama" in filter_type else "sender"

    # Step 3: Select parser
    print_header("Step 3: Select Parser")
    parser_type = get_choice(
        "Select parser type",
        ["Ollama (AI-powered)", "Regex (fallback)"],
        default=parser_idx,
    )

    parser_arg = "ollama" if "Ollama" in parser_type else "regex"

    # Step 4: Select output
    print_header("Step 4: Output Settings")
    output_path = get_input("Output file path", "output.xlsx")

    # Step 5: Select actions
    print_header("Step 5: Select Actions")
    analytics_default = cfg.data.get("analytics", {}).get("enabled", True)
    run_analyze = get_yes_no("Run analytics?", default=analytics_default)
    run_forecast = get_yes_no("Run forecast?", default=False)

    print_header("Running Pipeline")

    overrides = {
        "source": source_arg,
        "input": input_path,
        "filter": filter_arg,
        "parser": parser_arg,
        "output": output_path,
        "analyze": run_analyze,
        "forecast": run_forecast,
    }
    if creds:
        overrides["credentials"] = creds

    result = execute_pipeline(config_path=config_path, cli_overrides=overrides)
    if result == 0:
        print_header("Pipeline Complete!")
    return result


def cmd_analyze(args) -> int:
    """Run analytics on Excel output."""
    print_header("FinTrack - Analytics")

    if not args.input:
        args.input = get_input("Input Excel file", "output.xlsx")

    print_info(f"Loading data from: {args.input}")

    try:
        rows = load_rows_from_excel(args.input)
    except Exception as e:
        print_error(f"Error loading file: {e}")
        return 1

    print_success(f"Loaded {len(rows)} transactions\n")

    if rows:
        total = sum(float(r.amount or 0) for r in rows)
        print_info(f"Total value: ৳{total:,.0f}\n")

    from src.analytics.modules.spending import SpendingAnalyzer
    from src.analytics.modules.trends import TrendsAnalyzer
    from src.analytics.modules.anomaly import AnomalyDetector

    if args.module in ("all", "spending"):
        print_header("Spending Analysis")
        analyzer = SpendingAnalyzer()
        insights = analyzer.analyze(rows)
        for insight in insights:
            print(f"\n{ Fore.CYAN if COLOR else ''}{insight.title}{Style.RESET_ALL if COLOR else ''}")
            print(f"  {insight.description}")
            if args.details and insight.details:
                for k, v in insight.details.items():
                    print(f"    {k}: {v}")

    if args.module in ("all", "trends"):
        print_header("Trends Analysis")
        analyzer = TrendsAnalyzer()
        insights = analyzer.analyze(rows)
        for insight in insights:
            print(f"\n{ Fore.CYAN if COLOR else ''}{insight.title}{Style.RESET_ALL if COLOR else ''}")
            print(f"  {insight.description}")

    if args.module in ("all", "anomaly"):
        print_header("Anomaly Detection")
        analyzer = AnomalyDetector()
        insights = analyzer.analyze(rows)
        for insight in insights:
            print(f"\n{ Fore.CYAN if COLOR else ''}{insight.title}{Style.RESET_ALL if COLOR else ''}")
            print(f"  {insight.description}")
            if args.details and insight.details:
                details = insight.details.get("transactions", insight.details.get("spikes", []))
                for d in details[:5]:
                    print(f"    - {d}")

    return 0


def cmd_forecast(args) -> int:
    """Generate spending forecasts."""
    print_header("FinTrack - Forecast")

    if not args.input:
        args.input = get_input("Input Excel file", "output.xlsx")

    print_info(f"Loading data from: {args.input}")

    try:
        rows = load_rows_from_excel(args.input)
    except Exception as e:
        print_error(f"Error loading file: {e}")
        return 1

    print_success(f"Loaded {len(rows)} transactions\n")

    if len(rows) < 10:
        print_error("Not enough data for forecast (need at least 10 transactions)")
        return 1

    model_type = args.model or "linear"
    print_info(f"Using {model_type} model\n")

    if model_type == "llm":
        from src.forecasting.models.llm import LLMForecaster
        forecaster = LLMForecaster({"periods": args.periods})
    else:
        from src.forecasting.models.linear import LinearForecaster
        forecaster = LinearForecaster({"periods": args.periods})

    forecasts = forecaster.predict(rows)

    if not forecasts:
        print_error("Not enough data to generate forecast (need at least 2 months)")
        return 1

    print_header(f"Forecast - Next {args.periods} Months")
    for forecast in forecasts:
        print(f"\n{ Fore.CYAN if COLOR else ''}{forecast.period}{Style.RESET_ALL if COLOR else ''}")
        print(f"  Predicted: ৳{forecast.predicted_value:,.0f}")
        print(f"  Range: ৳{forecast.lower_bound:,.0f} - ৳{forecast.upper_bound:,.0f}")
        print(f"  Confidence: {forecast.confidence * 100:.0f}%")
        if forecast.details.get("reasoning"):
            print(f"  Note: {forecast.details['reasoning']}")

    return 0


def cmd_senders(args) -> int:
    """List and manage senders."""
    from src.models.senders import FINANCIAL_SENDERS, is_financial_sender

    print_header("Financial Senders Configuration")

    # Group senders
    enabled = {k: v for k, v in FINANCIAL_SENDERS.items() if v}
    disabled = {k: v for k, v in FINANCIAL_SENDERS.items() if not v}

    print(f"\n{Fore.GREEN if COLOR else ''}Enabled ({len(enabled)}):{Style.RESET_ALL if COLOR else ''}")
    for sender in sorted(enabled.keys()):
        print(f"  ✓ {sender}")

    print(f"\n{Fore.RED if COLOR else ''}Disabled ({len(disabled)}):{Style.RESET_ALL if COLOR else ''}")
    for sender in sorted(disabled.keys()):
        print(f"  ✗ {sender}")

    print(f"\nTotal: {len(FINANCIAL_SENDERS)} senders")

    if args.add or args.remove:
        # TODO: Implement add/remove
        print_warning("Add/remove not implemented yet")

    return 0


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="smsfin",
        description=f"{Fore.CYAN if COLOR else ''}FinTrack - SMS Finance Tracker{Style.RESET_ALL if COLOR else ''}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to config.yaml (default: auto-detect in project or cwd)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Interactive mode
    subparsers.add_parser("interactive", help="Run in interactive mode")
    subparsers.add_parser("i", help="Short for interactive")

    # Analyze
    analyze_parser = subparsers.add_parser("analyze", help="Run analytics on Excel output")
    analyze_parser.add_argument("input", nargs="?", help="Input Excel file")
    analyze_parser.add_argument("-m", "--module", default="all",
        choices=["all", "spending", "trends", "anomaly"],
        help="Analytics module to run")
    analyze_parser.add_argument("-d", "--details", action="store_true", help="Show detailed output")

    # Forecast
    forecast_parser = subparsers.add_parser("forecast", help="Generate spending forecast")
    forecast_parser.add_argument("input", nargs="?", help="Input Excel file")
    forecast_parser.add_argument("-m", "--model", default="linear",
        choices=["linear", "llm"],
        help="Forecasting model")
    forecast_parser.add_argument("-p", "--periods", type=int, default=3, help="Number of periods to forecast")

    # Senders
    senders_parser = subparsers.add_parser("senders", help="Manage financial senders")
    senders_parser.add_argument("--add", help="Add sender")
    senders_parser.add_argument("--remove", help="Remove sender")

    # Pipeline
    pipeline_parser = subparsers.add_parser("pipeline", help="Run full pipeline")
    pipeline_parser.add_argument(
        "-s", "--source", default=None,
        choices=["google_sheet", "csv"],
        help="Input source type (default: from config.yaml)",
    )
    pipeline_parser.add_argument("-i", "--input", help="Input source (sheet URL or CSV path)")
    pipeline_parser.add_argument(
        "-c", "--credentials",
        help="Credentials file for Google Sheets (default: from config.yaml)",
    )
    pipeline_parser.add_argument(
        "-o", "--output", default=None,
        help="Output file path (default: output.xlsx or config)",
    )
    pipeline_parser.add_argument(
        "--filter", default=None,
        choices=["none", "ollama", "sender"],
        help="Filter to use (default: from config.yaml)",
    )
    pipeline_parser.add_argument(
        "--parser", default=None,
        choices=["none", "regex", "ollama"],
        help="Parser to use (default: from config.yaml)",
    )
    pipeline_parser.add_argument("--analyze", action="store_true", help="Run analytics")
    pipeline_parser.add_argument("--forecast", action="store_true", help="Run forecasting")

    # Legacy commands
    gs_parser = subparsers.add_parser("parse-gsheet", help="Parse data from Google Sheet")
    gs_parser.add_argument("sheet_url", nargs="?", help="Google Sheet URL or ID")
    gs_parser.add_argument("-c", "--credentials", default="credentials.json", help="Credentials file")
    gs_parser.add_argument("-o", "--output", default="output.xlsx", help="Output Excel file")

    args = parser.parse_args(argv)

    if args.command in ("interactive", "i", None):
        return run_interactive(getattr(args, "config", None))

    elif args.command == "analyze":
        return cmd_analyze(args)

    elif args.command == "forecast":
        return cmd_forecast(args)

    elif args.command == "senders":
        return cmd_senders(args)

    elif args.command == "pipeline":
        return run_pipeline(args)

    elif args.command == "parse-gsheet":
        return run_parse_gsheet(args)

    else:
        parser.print_help()
        return 0


def run_parse_gsheet(args) -> int:
    """Run parse-gsheet command."""
    if not args.sheet_url:
        args.sheet_url = get_input("Google Sheet URL or ID")
        if not args.sheet_url:
            print_error("Sheet URL is required")
            return 1

    from src.io.google_sheets import read_google_sheet
    from src.core.processor import build_rows
    from src.io.excel_writer import create_workbook, write_sheet, save_workbook, ledger_to_values
    from src.models.ledger import LEDGER_HEADERS

    print_info(f"Reading from Google Sheet: {args.sheet_url}")

    try:
        raw_rows = list(read_google_sheet(args.sheet_url, args.credentials))
    except Exception as e:
        print_error(f"Error: {e}")
        return 1

    print_success(f"Read {len(raw_rows)} rows")

    rows, stats = build_rows(raw_rows)
    print_success(f"Parsed {len(rows)} transactions")

    if not rows:
        print_error("No transactions found")
        return 1

    wb = create_workbook()
    ws = wb.active
    ws.title = "Ledger"

    ledger_data = ledger_to_values(rows)
    write_sheet(ws, LEDGER_HEADERS, ledger_data, "Ledger")

    from src.core.processor import summarize_monthly, summarize_categories, summarize_accounts
    monthly_data = summarize_monthly(rows)
    if monthly_data:
        ws_summary = wb.create_sheet("Summary")
        write_sheet(ws_summary,
            ["Month", "Income", "Expense", "Transfer In", "Transfer Out", "Net", "Notices", "Ignored"],
            monthly_data, "Summary")

    category_data = summarize_categories(rows)
    if category_data:
        ws_cat = wb.create_sheet("Categories")
        write_sheet(ws_cat, ["Month", "Category", "Total"], category_data, "Categories")

    account_data = summarize_accounts(rows)
    if account_data:
        ws_acc = wb.create_sheet("Account Totals")
        write_sheet(ws_acc, ["Source", "Account", "Direction", "Total"], account_data, "AccountTotals")

    save_workbook(wb, args.output)
    print_success(f"Output written to: {args.output}")

    return 0


def run_pipeline(args) -> int:
    """Run pipeline command."""
    print_header("FinTrack Pipeline")

    overrides = _cli_overrides_from_args(args)
    config_path = getattr(args, "config", None)

    if not overrides.get("input"):
        cfg = load_app_config(config_path)
        from src.core.config import get_enabled_plugin
        source_cfg = get_enabled_plugin("sources", cfg.data)
        stype = overrides.get("source") or source_cfg.get("type", "csv")
        if stype == "google_sheets":
            stype = "google_sheet"
        if stype == "csv":
            overrides.setdefault("input", "data.csv")
        overrides.setdefault("source", stype)

    return execute_pipeline(
        config_path=config_path,
        cli_overrides=overrides,
        prompt_missing=not overrides.get("input"),
    )



if __name__ == "__main__":
    sys.exit(main())
