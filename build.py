"""Build the Oracle Ledger: one row per Delphi oracle decision, from chain events plus hash-checked metadata."""
import ast, csv, hashlib, json, os, time, urllib.request, collections, datetime
from fetch import logs, HERE
lit = lambda v: v if isinstance(v, list) else ast.literal_eval(v)
GEN = {  # generation -> (factory, relayer)
    "dpm-auto": ("0x9C73417f79a1361c6aF9Bd828343badEE1b84936", "0x6bBA6FC6550dFCD9D38a85C80C07f972652e0616"),
    "lmsr":     ("0x1819a2aeeb96da9ba1c5262a5c82b6f9c347f99c", "0x2c21571036426aB6e333a1f4abD4aa986e855ac2"),
}
MD = os.path.join(HERE, "cache", "metadata"); os.makedirs(MD, exist_ok=True)
def meta(url, want):
    f = os.path.join(MD, want[2:] + ".json")
    if not os.path.exists(f):
        b = urllib.request.urlopen(urllib.request.Request(url, headers={"user-agent": "oracle-ledger/0.1"}), timeout=30).read()
        open(f, "wb").write(b); time.sleep(0.05)
    b = open(f, "rb").read()
    return json.loads(b), "0x" + hashlib.sha256(b).hexdigest() == want.lower()
rows, markets = [], {}
for gen, (fac, rel) in GEN.items():
    for l in logs(fac):
        if l["event"] != "NewMarketProxy": continue
        url, h = lit(l["args"]["newMarketMetadata"])
        try: m, ok = meta(url, h)
        except Exception as e: m, ok = {}, None
        markets[l["args"]["newMarketProxy"].lower()] = (gen, m, ok, l["block"])
    ev = collections.defaultdict(dict)
    for l in logs(rel):
        if l["event"] in ("ResolutionRequested", "CallbackReceived", "ResolutionFailed"):
            ev[(l["args"]["marketProxy"].lower(), l["args"]["wtExecutionId"])][l["event"]] = l
    for (mp, wid), e in ev.items():
        g, m, ok, cb = markets.get(mp, (gen, {}, None, None))
        cbk, fail = e.get("CallbackReceived"), e.get("ResolutionFailed")
        rd = cbk["args"]["resultData"] if cbk else None
        outcome = None
        if rd and not fail:
            i = int(rd, 16); outs = m.get("outcomes") or []
            outcome = outs[i] if i < len(outs) else str(i)
        rows.append({
            "generation": gen, "market": mp, "execution_id": wid,
            "question": m.get("question", ""), "judge_model": (m.get("model") or {}).get("model_identifier", ""),
            "data_sources": " ".join(m.get("data_sources") or []), "mechanism": m.get("mechanism_type", ""),
            "rules_hash_ok": ok, "requested_block": e["ResolutionRequested"]["block"] if "ResolutionRequested" in e else "",
            "settled_block": cbk["block"] if cbk else "", "status": "failed" if fail else ("settled" if cbk else "pending"),
            "fail_reason": fail["args"]["reason"] if fail else "", "outcome": outcome or "",
            "transcripts": " ".join(lit(cbk["args"]["transcripts"])) if cbk else "",
            "receipt_public": "unknown", "tx": cbk["tx"] if cbk else "",
            "verification_status": "rules_verified" if ok else ("rules_mismatch" if ok is False else "rules_missing"),
        })
rows.sort(key=lambda r: (r["generation"], int(r["execution_id"])))
out = os.path.join(HERE, "data", "decisions.csv")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
S = collections.Counter((r["generation"], r["status"]) for r in rows)
summary = {"built_at": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
           "markets_by_generation": dict(collections.Counter(v[0] for v in markets.values())),
           "decisions": len(rows), "by_generation_status": {f"{a}/{b}": n for (a, b), n in sorted(S.items())},
           "rules_hash": dict(collections.Counter(str(v[2]) for v in markets.values())),
           "fail_reasons": dict(collections.Counter((r["generation"], r["fail_reason"]) for r in rows if r["fail_reason"]).most_common()),
           "judge_models": dict(collections.Counter(r["judge_model"] for r in rows))}
summary["fail_reasons"] = {f"{a}/reason={b}": n for (a, b), n in summary["fail_reasons"].items()}
json.dump(summary, open(os.path.join(HERE, "data", "summary.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(summary, indent=1, ensure_ascii=False))
