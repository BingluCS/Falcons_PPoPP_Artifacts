#!/usr/bin/env python3
"""Print single-thread compression and decompression throughput (Figure 8)."""

import sys
sys.dont_write_bytecode = True

from analysis_common import (
    DATASETS, ERRORS, compressors, harmonic_columns, parser, print_table,
    read_metric, require_fields, run, same_fields,
)


def main():
    args = parser(__doc__).parse_args()
    results = {}
    for dataset in DATASETS:
        compression = read_metric(args.data_dir, "cmpth", dataset, {1})
        decompression = read_metric(args.data_dir, "decth", dataset, {1})
        names = compressors(compression, decompression)
        results[dataset] = {"Compression": {}, "Decompression": {}}
        for name in names:
            comp_fields = require_fields(compression, name, 1, dataset + " compression throughput")
            dec_fields = require_fields(decompression, name, 1, dataset + " decompression throughput")
            same_fields(comp_fields, dec_fields, dataset + " " + name + " throughput")
            for title, fields in (("Compression", comp_fields), ("Decompression", dec_fields)):
                means = harmonic_columns(fields)
                # test.py records bytes / 1024**3 / seconds (GiB/s).
                results[dataset][title][name] = {e: means[e] * 1024 for e in ERRORS}

        for title in ("Compression", "Decompression"):
            print(f"\n{dataset} - {title} throughput (1 thread, MiB/s)")
            rows = []
            for name in names:
                values = results[dataset][title][name]
                rows.append([name] + [f"{values[e]:.1f}" for e in ERRORS])
            print_table(["Compressor", *ERRORS], rows)

if __name__ == "__main__":
    run(main)
