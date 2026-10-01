# Invalid initial execution — do not analyze

The first run produced duplicated evaluation blocks and failed the frozen verifier's row-count check. All outcome values in `summary.json` are invalid and excluded from the canonical results. `manifest.json` retains the original file sizes and SHA-256 values. The five CSVs are gzip-compressed byte-for-byte copies; `COMPRESSED_OUTPUT_INDEX.json` records their raw and compressed hashes. Decompress a `.csv.gz` to reconstruct the exact original CSV.
