"""Compare a compiled worker ABI layout harvest with its golden.

`runner_abi_layout` harvests every size, offset and constant from the ABI header
with a compiled printer. The golden under tests/fixtures/contract/ is the last
accepted harvest. Host and worker refuse a mismatched ABI number, so a layout
change under an unchanged number is a forgotten bump, not an additive change.
"""


def parse(text):
    values = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.strip().split("=", 1)
            values[key] = value
    return values


def compare(printer_text, golden_text):
    """Return (status, detail); status is ok, missing_golden, needs_bump or update."""
    if printer_text == golden_text:
        return "ok", ""
    if not golden_text.strip():
        return "missing_golden", "no ABI layout golden"
    now, old = parse(printer_text), parse(golden_text)
    changed = sorted(key for key in set(now) | set(old) if now.get(key) != old.get(key))
    if not changed:
        return "update", "harvest formatting changed; every value agrees"
    detail = ", ".join(changed)
    if now.get("PW_PROBE_RUNNER_ABI_VERSION") == old.get("PW_PROBE_RUNNER_ABI_VERSION"):
        return "needs_bump", f"ABI layout changed without a worker ABI bump ({detail})"
    return "update", f"ABI layout changed with a bump ({detail})"
