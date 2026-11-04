"""Shared CSV reading and aggregation for the artifact analysis scripts."""

import argparse
import csv
import math
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "test" / "experiment_csv"
DATASETS = ("NYX", "Miranda")
ERRORS = ("1E-2", "1E-3", "1E-4")
BITS_PER_VALUE = {"NYX": 32, "Miranda": 64}
COMPRESSOR_ORDER = ("ZFP", "PFPL", "SPERR", "SZ3.3", "Falcons")


class DataError(Exception):
    """Input data are missing, inconsistent, or cannot be aggregated."""


def parser(description):
    result = argparse.ArgumentParser(description=description)
    result.add_argument(
        "--data-dir", type=Path, default=DEFAULT_DATA_DIR,
        help="Directory containing cmpth/, decth/, ratio/, and nrmse/ CSVs "
        "(default: ../test/experiment_csv relative to this script).",
    )
    return result


def read_metric(data_dir, metric, dataset, threads, exclude_compressors=()):
    """Return compressor -> thread -> field -> error -> value for selected threads."""
    path = Path(data_dir) / metric / (dataset + "_omp.csv")
    if not path.is_file():
        raise DataError(f"Missing input CSV: {path}")
    result = {}
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        columns = {"dataset", "field", "type", "threads", *ERRORS}
        missing = columns.difference(reader.fieldnames or ())
        if missing:
            raise DataError(f"{path}: missing columns: {', '.join(sorted(missing))}")
        for line, row in enumerate(reader, start=2):
            if row["dataset"].strip() != dataset:
                raise DataError(f"{path}:{line}: unexpected dataset {row['dataset']!r}")
            try:
                thread = int(row["threads"])
            except (TypeError, ValueError) as error:
                raise DataError(f"{path}:{line}: invalid thread count") from error
            if thread not in threads:
                continue
            compressor = row["type"].strip()
            if compressor in exclude_compressors:
                continue
            field = row["field"].strip()
            if not compressor or not field:
                raise DataError(f"{path}:{line}: empty compressor or field")
            values = {}
            for error_label in ERRORS:
                try:
                    value = float(row[error_label])
                except (KeyError, TypeError, ValueError) as error:
                    raise DataError(f"{path}:{line}: invalid {error_label} value") from error
                if metric != "nrmse" and (not math.isfinite(value) or value <= 0):
                    raise DataError(f"{path}:{line}: {error_label} must be positive and finite")
                if metric == "nrmse" and math.isfinite(value) and value < 0:
                    raise DataError(f"{path}:{line}: NRMSE cannot be negative")
                values[error_label] = value
            fields = result.setdefault(compressor, {}).setdefault(thread, {})
            if field in fields:
                raise DataError(f"{path}:{line}: duplicate row for {compressor}, {thread} threads, {field}")
            fields[field] = values
    if not result:
        raise DataError(f"{path}: no rows for threads {sorted(threads)}")
    return result


def compressors(*groups):
    names = set().union(*(group.keys() for group in groups))
    return sorted(names, key=lambda name: (
        COMPRESSOR_ORDER.index(name) if name in COMPRESSOR_ORDER else len(COMPRESSOR_ORDER), name
    ))


def harmonic_mean(values):
    values = list(values)
    if not values or any(not math.isfinite(v) or v <= 0 for v in values):
        raise DataError("Values must be positive and finite")
    return len(values) / math.fsum(1.0 / value for value in values)


def harmonic_columns(fields):
    return {
        label: harmonic_mean(values[label] for values in fields.values())
        for label in ERRORS
    }


def nrmse_psnr(values, description):
    """Match the supplied notebook: discard NRMSE >= 10, RMS, then -20 log10."""
    values = list(values)
    valid = [v for v in values if math.isfinite(v) and 0 <= v < 10]
    discarded = len(values) - len(valid)
    if discarded:
        print(f"Warning: {description}: excluded {discarded} invalid or NRMSE >= 10 values", file=sys.stderr)
    if not valid:
        raise DataError(f"{description}: no valid NRMSE values")
    rms = math.sqrt(math.fsum(v * v for v in valid) / len(valid))
    return math.inf if rms == 0 else -20.0 * math.log10(rms)


def require_fields(data, compressor, thread, description):
    fields = data.get(compressor, {}).get(thread)
    if not fields:
        raise DataError(f"{description}: missing {compressor} data for {thread} thread(s)")
    return fields


def same_fields(first, second, description):
    if set(first) != set(second):
        raise DataError(
            f"{description}: different field sets "
            f"(only first: {sorted(set(first) - set(second))}; "
            f"only second: {sorted(set(second) - set(first))})"
        )


def print_table(headers, rows):
    rows = [[str(value) for value in row] for row in rows]
    widths = [max([len(str(header))] + [len(row[i]) for row in rows]) for i, header in enumerate(headers)]
    print("  ".join(str(value).ljust(widths[i]) if i == 0 else str(value).rjust(widths[i])
                    for i, value in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        line = "  ".join(value.ljust(widths[i]) if i == 0 else value.rjust(widths[i])
                         for i, value in enumerate(row))
        if row[0].casefold() == "falcons" and sys.stdout.isatty():
            line = f"\033[1m{line}\033[0m"
        print(line)


def run(main):
    try:
        main()
    except (DataError, OSError, csv.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
