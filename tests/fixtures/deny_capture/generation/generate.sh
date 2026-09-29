#!/bin/bash
# Exact generation recipe for query_predicate.logarchive, as run on 2026-09-29
# from a macOS 26.6.2 host against an isolated macOS 14.8.7 guest over SSH.
# Root is needed only for `log collect`; run that step with an interactive
# sudo (or SUDO_ASKPASS) — never embed the guest password in this file.
#
# Inputs staged in the guest at /Users/admin/pwqp: pwqp-emit (built from
# ../emitter/pwqp_emit.c with
#   xcrun clang -Wall -Wextra -O2 -mmacosx-version-min=14.0 -o pwqp-emit pwqp_emit.c
# on the host) and corpus.lines (from `make_manifest.py corpus`).
set -euo pipefail
G="${GUEST:-admin@192.168.64.2}"
SSH="ssh -o BatchMode=yes $G"
# 1. Emit as the unprivileged admin user; record UTC bounds around emission.
$SSH 'set -e; cd /Users/admin/pwqp; mkdir -p record; chmod +x pwqp-emit
sw_vers > record/sw_vers.txt; uname -a > record/uname.txt
shasum -a 256 /usr/bin/log pwqp-emit corpus.lines > record/inputs.sha256
T0=$(date -u +%s); sleep 1
./pwqp-emit < corpus.lines > record/emitter.out
T1=$(date -u +%s); sleep 3
START=$(date -u -r $((T0-1)) "+%Y-%m-%d %H:%M:%S+0000"); END=$(date -u -r $((T1+3)) "+%Y-%m-%d %H:%M:%S+0000")
PID=$(sed -n "s/^emitting_pid=//p" record/emitter.out); N=$(sed -n "s/^emitted=//p" record/emitter.out)
printf "{\"emitting_pid\": %s, \"emitted\": %s, \"t0_unix\": %s, \"t1_unix\": %s, \"window\": {\"start\": \"%s\", \"end\": \"%s\"}, \"queries\": {}}\n" "$PID" "$N" "$T0" "$T1" "$START" "$END" > record/record.json'
# 2. Collect as root from the window start (interactive sudo).
START=$($SSH 'sed -n "s/.*\"start\": \"\([^\"]*\)\".*/\1/p" /Users/admin/pwqp/record/record.json')
$SSH -t "cd /Users/admin/pwqp && sudo sh -c 'rm -rf query_predicate.logarchive && log collect --start \"$START\" --output query_predicate.logarchive && chown -R admin:staff query_predicate.logarchive'"
# 3. Inspect unfiltered over the window, compare the rendered corpus with the declared corpus, dump the whole archive for review, hash every file.
$SSH 'set -e; cd /Users/admin/pwqp
START=$(sed -n "s/.*\"start\": \"\([^\"]*\)\".*/\1/p" record/record.json); END=$(sed -n "s/.*\"end\": \"\([^\"]*\)\".*/\1/p" record/record.json)
/usr/bin/log show --archive query_predicate.logarchive --start "$START" --end "$END" --style syslog --info --debug > record/unfiltered-window.txt
grep -o "PWQP:.*$" record/unfiltered-window.txt | LC_ALL=C sort > record/rendered.sorted; LC_ALL=C sort corpus.lines > record/corpus.sorted
cmp record/rendered.sorted record/corpus.sorted
echo "rendered corpus == declared corpus"
/usr/bin/log show --archive query_predicate.logarchive --style syslog --info --debug > record/full-archive.txt
(cd query_predicate.logarchive && find . -type f | LC_ALL=C sort | xargs shasum -a 256) > record/archive.sha256'
# 4. Transfer archive + record to the checkout, verify hashes, then:
#    make_manifest.py manifest record/record.json > query_predicate.json
#    tests/run.sh --case witness_contract/log_query_predicate_archive
# 5. Reduce to the files the declared corpus needs, then re-prove on every
#    verified reader (unfiltered corpus multiset, each production query, the
#    registered case and both mutation controls) before committing:
#      keep Info.plist Persist logdata.LiveData.tracev3 timesync <emitter uuidtext dir>
#    Record the unreduced hash list as generation/full-archive.SHA256SUMS and
#    retain the unreduced archive outside git.
