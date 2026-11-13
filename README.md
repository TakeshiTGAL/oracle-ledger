# Oracle Ledger (prototype)

One row for every Delphi oracle decision on Gensyn mainnet, built from public chain events and hash-checked market metadata. No API key and no node are needed.

This is the prototype behind a Gensyn Foundation grant application. The committed data is a snapshot built on 2026-11-11.

Browse the snapshot: https://takeshitgal.github.io/oracle-ledger/ (paste a market address, or add ?market=<address> to the URL)

## Reproduce the snapshot

    python3 build.py        # reads cache/, writes data/decisions.csv and data/summary.json

`cache/` holds the decoded logs and metadata files used for the snapshot, so the build runs offline and gives the same summary.

## Check against Delphi's official sources

    python3 check_official.py   # needs network, no API key

It reads the SDK address table and the official autoset subgraph and prints whether the snapshot's DPM settled and failed markets match the subgraph and how many LMSR decisions the subgraph has.

## Refresh from the chain

    python3 fetch.py <address>...   # pulls decoded logs from the public Gensyn explorer into cache/

## Sources
- Factories: 0x9C73417f79a1361c6aF9Bd828343badEE1b84936 (DPM, automated settlement) and 0x1819a2aeeb96da9ba1c5262a5c82b6f9c347f99c (LMSR)
- Oracle relayers (TruebitOracleRelayer): 0x6bba6fc6550dfcd9d38a85c80c07f972652e0616 and 0x2c21571036426ab6e333a1f4abd4aa986e855ac2
- Failure reasons come from the verified relayer enum: 0 EXECUTION_FAILED, 1 MALFORMED_RESULT, 2 INVALID_OUTCOME.

## Snapshot summary (2026-11-11)
- 641 markets (DPM 479, LMSR 162) and 587 oracle decisions
- DPM: 432 settled, 38 failed. LMSR: 111 settled, 6 failed.
- 640 of 641 markets match the SHA-256 committed at creation
- 43 failures with reason 2 and 1 with reason 0

## Columns in data/decisions.csv
generation, market, execution_id, question, judge_model, data_sources, mechanism, rules_hash_ok, requested_block, settled_block, status, fail_reason, outcome, transcripts, receipt_public, tx, verification_status

## License
MIT
