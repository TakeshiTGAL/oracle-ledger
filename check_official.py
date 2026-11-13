"""Compare the snapshot with Delphi's official sources: the SDK address table and the public subgraphs.
usage: python3 check_official.py
Prints one line per check. Needs network access. No API key."""
import csv, json, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SG = "https://api.goldsky.com/api/public/project_cmnoqdag1obop01z3efnu8ssq/subgraphs/{}/1.0.0/gn"
SDK_TABLE = "https://docs.delphi.fyi/tools/sdk/configuration.md"
LMSR_FACTORY = "0x1819a2aeeb96da9ba1c5262a5c82b6f9c347f99c"
DPM_FACTORY = "0x9c73417f79a1361c6af9bd828343badee1b84936"


def fetch(url, body=None):
    req = urllib.request.Request(url, data=body, headers={"content-type": "application/json", "user-agent": "oracle-ledger/0.1"})
    return urllib.request.urlopen(req, timeout=60).read().decode()


def all_proxies(subgraph, entity):
    out, last = set(), ""
    while True:
        q = '{ %s(first: 1000, where: {marketProxy_gt: "%s"}, orderBy: marketProxy) { marketProxy } }' % (entity, last)
        d = json.loads(fetch(SG.format(subgraph), json.dumps({"query": q}).encode()))
        if "errors" in d:
            return None
        rows = d["data"][entity]
        out |= {r["marketProxy"].lower() for r in rows}
        if len(rows) < 1000:
            return out
        last = rows[-1]["marketProxy"]


rows = list(csv.DictReader(open(os.path.join(HERE, "data", "decisions.csv"))))
dpm = {s: {r["market"].lower() for r in rows if r["generation"] == "dpm-auto" and r["status"] == s} for s in ("settled", "failed")}
lmsr = {r["market"].lower() for r in rows if r["generation"] == "lmsr"}

table = fetch(SDK_TABLE).lower()
print("SDK address table lists the DPM factory:", DPM_FACTORY in table)
print("SDK address table lists the LMSR factory:", LMSR_FACTORY in table)

settled = all_proxies("delphi-mainnet-autoset", "gatewayMarketSettleds")
failed = all_proxies("delphi-mainnet-autoset", "gatewayMarketFaileds")
print("autoset settled == snapshot DPM settled:", settled is not None and {m for m in settled if m in dpm["settled"] or m in lmsr} == dpm["settled"], f"({len(settled or [])} in subgraph, {len(dpm['settled'])} in snapshot)")
print("autoset failed == snapshot DPM failed:", failed is not None and {m for m in failed if m in dpm["failed"] or m in lmsr} == dpm["failed"], f"({len(failed or [])} in subgraph, {len(dpm['failed'])} in snapshot)")
print("LMSR decisions found in autoset:", len(((settled or set()) | (failed or set())) & lmsr))
