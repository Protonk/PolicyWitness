"""Compare a compiled worker ABI layout harvest with its golden.

`runner_abi_layout` harvests every size, offset and constant from the ABI header
with a compiled printer. The golden under tests/fixtures/contract/ is the last
accepted layout harvest. The independently generated source identity is checked
separately; changing protocol code does not require acknowledging a new layout.
"""


def parse(text):
    values = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.strip().split("=", 1)
            values[key] = value
    return values


def compare(printer_text, golden_text):
    """Return (status, detail); status is ok, missing_golden or update."""
    if printer_text == golden_text:
        return "ok", ""
    if not golden_text.strip():
        return "missing_golden", "no ABI layout golden"
    now, old = parse(printer_text), parse(golden_text)
    changed = sorted(key for key in set(now) | set(old) if now.get(key) != old.get(key))
    if not changed:
        return "update", "harvest formatting changed; every value agrees"
    detail = ", ".join(changed)
    return "update", f"ABI layout changed ({detail})"
