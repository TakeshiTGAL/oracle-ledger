"""Fetch all decoded logs of a contract from the public Gensyn mainnet explorer (Blockscout v2). Cached as JSONL."""
import json, os, sys, time, urllib.request
E = "https://gensyn-mainnet.explorer.alchemy.com/api/v2"
HERE = os.path.dirname(os.path.abspath(__file__))
def get(path, tries=5):
    for i in range(tries):
        try:
            r = urllib.request.Request(E + path, headers={"user-agent": "oracle-ledger/0.1"})
            return json.load(urllib.request.urlopen(r, timeout=60))
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(2 * (i + 1))
def logs(addr, refresh=False):
    f = os.path.join(HERE, "cache", f"{addr.lower()}.jsonl")
    if os.path.exists(f) and not refresh:
        return [json.loads(l) for l in open(f)]
    out, params = [], ""
    while True:
        d = get(f"/addresses/{addr}/logs{params}")
        for l in d["items"]:
            dec = l.get("decoded") or {}
            out.append({"block": l["block_number"], "tx": l["transaction_hash"], "idx": l["index"],
                        "event": (dec.get("method_call") or "?").split("(")[0],
                        "args": {p["name"]: p["value"] for p in dec.get("parameters", [])}})
        np = d.get("next_page_params")
        if not np: break
        params = "?" + "&".join(f"{k}={v}" for k, v in np.items())
        time.sleep(0.2)
    with open(f, "w") as fh:
        for o in out: fh.write(json.dumps(o) + "\n")
    return out
if __name__ == "__main__":
    for a in sys.argv[1:]:
        L = logs(a, refresh=True); print(a, len(L))
