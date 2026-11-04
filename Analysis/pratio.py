#!/usr/bin/env python3
"""Print 1- and 32-thread compression ratios at 1E-2 (Figure 7)."""

import sys
sys.dont_write_bytecode = True

from analysis_common import (
    DATASETS, compressors, harmonic_columns, parser, print_table,
    read_metric, require_fields, run, same_fields,
)


def main():
    args = parser(__doc__).parse_args()
    for dataset in DATASETS:
        data = read_metric(args.data_dir, "ratio", dataset, {1, 32}, {"ZFP", "PFPL"})
        print(f"\n{dataset} - compression ratio (1E-2)")
        rows = []
        for name in compressors(data):
            serial = require_fields(data, name, 1, dataset + " compression ratio")
            one = harmonic_columns(serial)["1E-2"]
            parallel = require_fields(data, name, 32, dataset + " compression ratio")
            same_fields(serial, parallel, dataset + " " + name + " 1 vs 32 threads")
            thirty_two = harmonic_columns(parallel)["1E-2"]
            rows.append([name, f"{one:.1f}", f"{thirty_two:.1f}", f"{thirty_two / one:.1%}"])
        print_table(["Compressor", "1 thread", "32 threads", "32 / 1"], rows)

if __name__ == "__main__":
    run(main)
