#!/usr/bin/env python3
"""Print 32-thread compression ratio and PSNR (Figure 9)."""

import sys
sys.dont_write_bytecode = True

from analysis_common import (
    BITS_PER_VALUE, DATASETS, ERRORS, compressors, harmonic_columns,
    nrmse_psnr, parser, print_table, read_metric, require_fields, run, same_fields,
)


def main():
    args = parser(__doc__).parse_args()
    for dataset in DATASETS:
        ratios = read_metric(args.data_dir, "ratio", dataset, {32})
        errors = read_metric(args.data_dir, "nrmse", dataset, {32})
        print(f"\n{dataset} - rate-distortion (32 threads)")
        rows = []
        for name in compressors(ratios, errors):
            ratio_fields = require_fields(ratios, name, 32, dataset + " ratio")
            nrmse_fields = require_fields(errors, name, 32, dataset + " NRMSE")
            same_fields(ratio_fields, nrmse_fields, dataset + " " + name + " rate-distortion")
            ratio_values = harmonic_columns(ratio_fields)
            for error_label in ERRORS:
                ratio = ratio_values[error_label]
                psnr = nrmse_psnr(
                    (values[error_label] for values in nrmse_fields.values()),
                    f"{dataset} {name} {error_label}",
                )
                bitrate = BITS_PER_VALUE[dataset] / ratio
                rows.append([name, error_label, f"{ratio:.1f}",
                             f"{bitrate:.3f}", f"{psnr:.1f}"])
        print_table(["Compressor", "Error", "Ratio", "Bitrate (bits/value)", "PSNR (dB)"], rows)

if __name__ == "__main__":
    run(main)
