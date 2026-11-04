#!/usr/bin/env python3
"""Table 5: single-thread compression ratios for both datasets."""

import sys
sys.dont_write_bytecode = True

from analysis_common import (
    DATASETS, ERRORS, compressors, harmonic_columns, parser, print_table,
    read_metric, require_fields, run,
)


def main():
    args = parser(__doc__).parse_args()
    for dataset in DATASETS:
        data = read_metric(args.data_dir, "ratio", dataset, {1})
        print(f"\n{dataset} - compression ratio (1 thread)")
        rows = []
        for name in compressors(data):
            fields = require_fields(data, name, 1, dataset + " compression ratio")
            values = harmonic_columns(fields)
            rows.append([name] + [f"{values[e]:.1f}" for e in ERRORS])
        print_table(["Compressor", *ERRORS], rows)


if __name__ == "__main__":
    run(main)
