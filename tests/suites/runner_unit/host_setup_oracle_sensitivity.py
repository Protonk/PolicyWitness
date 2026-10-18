"""Characterize three blind spots in the unchanged host-setup oracle.

The original recipe/checker runs in full against disposable source roots. Only
those roots contain the deliberate host mutations and supplemental observations.
Passing means the old oracle accepted an independently observed counterexample;
it does not certify product safety or repair that oracle.
"""
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
VARIANTS = ("baseline", "wrong_ready_direction", "wrong_shm_argv", "partial_unmap")


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob("*")) if p.is_file()}


def replace_once(path, before, after, manifest, purpose):
    original = path.read_text()
    assert original.count(before) == 1, (str(path), purpose, "anchor changed; review instrumentation")
    prior = digest(path)
    path.write_text(original.replace(before, after, 1))
    manifest.append(dict(path=str(path), purpose=purpose, occurrences=1,
                         before=before, after=after, source_sha256=prior, result_sha256=digest(path)))


# This observer records facts the old fstat-only checker does not inspect. It
# opens no extra endpoint before taking the descriptor observations. Its JSON
# fields are additive; the legacy receipt and assertions remain unchanged.
OBSERVER_STRING_HELPER = r'''
static void oracle_json_string(FILE *out, const char *value) {
    fputc('"', out);
    for (const unsigned char *p = (const unsigned char *)value; *p; ++p) {
        if (*p == '"' || *p == '\\') { fputc('\\', out); fputc(*p, out); }
        else if (*p < 32) fprintf(out, "\\u%04x", (unsigned)*p);
        else fputc(*p, out);
    }
    fputc('"', out);
}
'''


# Static C storage retains exact VM ranges, not residency observations. Each
# mach_vm_region answer can describe a containing or subsequent range; the scan
# counts only intersection with the requested span and releases object-name
# rights. The positive pre-unmap and negative full-unmap controls use this same
# observer. Cleanup touches only a re-confirmed suffix of the acquired mapping.
MAPPING_SHIM = r'''
#include <errno.h>
#include <stdint.h>
#include <unistd.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
#include <mach/vm_region.h>
#define ORACLE_MAX_QUERIES 64
#define ORACLE_QUERY_WORDS 14
static int64_t oracle_words[14] = {0, 0, 0, 0, 0, 0, 0, -777, -777, 0, -777, -777, 0, 0};
/* Per scan: start, bytes, complete, mapped bytes, query count. */
static int64_t oracle_scans[4][5];
static int64_t oracle_queries[ORACLE_MAX_QUERIES][ORACLE_QUERY_WORDS];
static mach_vm_address_t oracle_mapping;
static mach_vm_size_t oracle_extent, oracle_prefix;

static void oracle_scan(int stage, mach_vm_address_t start, mach_vm_size_t length) {
    int64_t *scan = oracle_scans[stage];
    scan[0] = (int64_t)start; scan[1] = (int64_t)length;
    if (!length || start > UINT64_MAX - length) return;
    mach_vm_address_t cursor = start, end = start + length;
    while (cursor < end) {
        if (oracle_words[12] >= ORACLE_MAX_QUERIES) { oracle_words[13] = 1; return; }
        int64_t *row = oracle_queries[oracle_words[12]++];
        scan[4] += 1;
        mach_vm_address_t region = cursor;
        mach_vm_size_t size = 0;
        vm_region_basic_info_data_64_t info = {0};
        mach_msg_type_number_t count = VM_REGION_BASIC_INFO_COUNT_64;
        mach_port_t object = MACH_PORT_NULL;
        kern_return_t kr = mach_vm_region(mach_task_self(), &region, &size,
            VM_REGION_BASIC_INFO_64, (vm_region_info_t)&info, &count, &object);
        int valid_object = MACH_PORT_VALID(object);
        kern_return_t deallocation = valid_object ? mach_port_deallocate(mach_task_self(), object) : KERN_SUCCESS;
        row[0] = stage; row[1] = (int64_t)cursor; row[2] = kr;
        row[3] = (int64_t)region; row[4] = (int64_t)size; row[5] = count;
        row[6] = object; row[7] = valid_object; row[8] = valid_object; row[9] = deallocation;
        row[10] = info.protection; row[11] = info.max_protection;
        row[12] = info.shared; row[13] = (int64_t)info.offset;
        if (deallocation != KERN_SUCCESS) return;
        if (kr == KERN_INVALID_ADDRESS) { scan[2] = 1; return; }
        if (kr != KERN_SUCCESS || count != VM_REGION_BASIC_INFO_COUNT_64 || size == 0 || region > UINT64_MAX - size) return;
        if (region >= end) { scan[2] = 1; return; } /* the next region is outside the requested span */
        mach_vm_address_t region_end = region + size;
        if (region_end <= cursor) return;
        mach_vm_address_t overlap_start = region > cursor ? region : cursor;
        mach_vm_address_t overlap_end = region_end < end ? region_end : end;
        scan[3] += (int64_t)(overlap_end - overlap_start);
        cursor = overlap_end;
    }
    scan[2] = 1;
}

int pw_setup_oracle_unmap(void *address, size_t acquired, size_t requested) {
    int entry_errno = errno;
    long page = sysconf(_SC_PAGESIZE);
    oracle_words[0] += 1;
    oracle_words[1] = (int64_t)(uintptr_t)address;
    oracle_words[2] = (int64_t)acquired;
    oracle_words[3] = (int64_t)requested;
    oracle_words[4] = page;
    int can_observe = page > 0 && acquired > 0 && requested > 0
        && acquired <= SIZE_MAX - (size_t)page && requested <= SIZE_MAX - (size_t)page;
    if (can_observe) {
        size_t size = (size_t)page;
        oracle_extent = ((acquired + size - 1) / size) * size;
        oracle_prefix = ((requested + size - 1) / size) * size;
        oracle_mapping = (mach_vm_address_t)(uintptr_t)address;
        oracle_words[5] = (int64_t)oracle_extent; oracle_words[6] = (int64_t)oracle_prefix;
        oracle_scan(0, oracle_mapping, oracle_extent); /* positive observer control before native cleanup */
    }
    errno = entry_errno;
    int rc = munmap(address, requested);
    int native_errno = errno;
    oracle_words[7] = rc; oracle_words[8] = rc == -1 ? native_errno : 0;
    if (can_observe) oracle_scan(1, oracle_mapping, oracle_extent);
    errno = native_errno;
    return rc;
}
void pw_setup_oracle_cleanup_suffix(void) {
    if (oracle_words[0] != 1 || oracle_words[7] != 0 || oracle_prefix >= oracle_extent
        || oracle_scans[0][2] != 1 || oracle_scans[0][3] != (int64_t)oracle_extent
        || oracle_scans[1][2] != 1 || oracle_scans[1][3] != (int64_t)(oracle_extent - oracle_prefix)) return;
    mach_vm_address_t suffix = oracle_mapping + oracle_prefix;
    mach_vm_size_t bytes = oracle_extent - oracle_prefix;
    oracle_scan(2, suffix, bytes); /* re-confirm the entire still-owned suffix before fixture cleanup */
    if (oracle_scans[2][2] != 1 || oracle_scans[2][3] != (int64_t)bytes) return;
    oracle_words[9] = 1;
    errno = 0;
    int rc = munmap((void *)(uintptr_t)suffix, (size_t)bytes);
    oracle_words[10] = rc; oracle_words[11] = rc == -1 ? errno : 0;
    oracle_scan(3, suffix, bytes);
}
int64_t pw_setup_oracle_word(int32_t index) {
    return index >= 0 && index < 14 ? oracle_words[index] : -888;
}
int64_t pw_setup_oracle_scan_word(int32_t stage, int32_t index) {
    return stage >= 0 && stage < 4 && index >= 0 && index < 5 ? oracle_scans[stage][index] : -888;
}
int64_t pw_setup_oracle_query_word(int32_t row, int32_t index) {
    return row >= 0 && row < oracle_words[12] && index >= 0 && index < ORACLE_QUERY_WORDS ? oracle_queries[row][index] : -888;
}
'''

MAPPING_SWIFT = '''
// Supplemental observer only; the legacy setupMaps bookkeeping is unchanged.
@_silgen_name("pw_setup_oracle_unmap")
func setupOracleUnmap(_ address: UnsafeMutableRawPointer, _ acquired: Int, _ requested: Int) -> Int32
@_silgen_name("pw_setup_oracle_cleanup_suffix")
func setupOracleCleanupSuffix()
@_silgen_name("pw_setup_oracle_word")
func setupOracleWord(_ index: Int32) -> Int64
@_silgen_name("pw_setup_oracle_scan_word")
func setupOracleScanWord(_ stage: Int32, _ index: Int32) -> Int64
@_silgen_name("pw_setup_oracle_query_word")
func setupOracleQueryWord(_ row: Int32, _ index: Int32) -> Int64
var setupOracleAddress: UnsafeMutableRawPointer?
var setupOracleLength = 0
'''


def add_observers(fixture, manifest):
    observer = fixture / "observer.c"
    replace_once(observer, "#include <fcntl.h>\n", "#include <fcntl.h>\n#include <errno.h>\n",
                 manifest, "retain errno for independent F_GETFL observations")
    replace_once(observer, "int main(int argc, char **argv) {", OBSERVER_STRING_HELPER + "\nint main(int argc, char **argv) {",
                 manifest, "encode actual argv without using the host's argument expectations")
    replace_once(observer, "    int results[4];\n", "    int results[4], flags[4], flag_errors[4];\n",
                 manifest, "automatic storage for independent descriptor access modes")
    replace_once(observer, '    FILE *out = fopen(RECEIPT_PATH, "w");', '''    for (int i = 0; i < 4; ++i) {
        errno = 0;
        flags[i] = fcntl(fds[i], F_GETFL);
        flag_errors[i] = flags[i] == -1 ? errno : 0;
    }
    FILE *out = fopen(RECEIPT_PATH, "w");''', manifest, "observe access modes before opening the receipt")
    replace_once(observer, '        if (!results[i]) fprintf(out,', r'''        fprintf(out, ",\"oracle_fcntl_rc\":%d,\"oracle_fcntl_errno\":%d,\"oracle_access_mode\":%d",
            flags[i], flag_errors[i], flags[i] < 0 ? -1 : flags[i] & O_ACCMODE);
        if (!results[i]) fprintf(out,''', manifest, "append access-mode observations without changing legacy fields")
    replace_once(observer, r'    fprintf(out, "]}\n");', r'''    fprintf(out, "],\"oracle_argv\":[");
    for (int i = 0; i < argc; ++i) {
        if (i) fputc(',', out);
        oracle_json_string(out, argv[i]);
    }
    fprintf(out, "]}\n");''', manifest, "append the child's actual argument vector")

    shim = fixture / "shim.c"
    prior = digest(shim)
    with shim.open("a") as stream:
        stream.write(MAPPING_SHIM)
    manifest.append(dict(path=str(shim), purpose="native mapping observation and independent suffix cleanup",
                         source_sha256=prior, result_sha256=digest(shim)))
    swift = fixture / "SetupControls.swift"
    replace_once(swift, 'var setupCase = ""', MAPPING_SWIFT + '\nvar setupCase = ""', manifest,
                 "record one original mapping extent separately from legacy counters")
    replace_once(swift, "    if let result, result != MAP_FAILED { setupMaps.insert(UInt(bitPattern: result)) }",
                 """    if let result, result != MAP_FAILED {
        setupMaps.insert(UInt(bitPattern: result))
        setupOracleAddress = result; setupOracleLength = length
    }""", manifest, "retain acquired mapping address and extent")
    replace_once(swift, "    let rc = Darwin.munmap(address, length)\n", """    let rc = address == setupOracleAddress
        ? setupOracleUnmap(address, setupOracleLength, length)
        : Darwin.munmap(address, length)
""", manifest, "scan the complete acquired range immediately before/after the real native unmap")
    replace_once(swift, "    let fdsClosed = setupFDs.allSatisfy", """    let oracleLegacyMapsBeforeCleanup = setupMaps.count
    setupOracleCleanupSuffix() // fixture-owned; does not alter legacy counters/events
    let fdsClosed = setupFDs.allSatisfy""", manifest, "snapshot legacy accounting before independent suffix cleanup")
    replace_once(swift, "    try data.write(to: URL(fileURLWithPath: output))", """    try data.write(to: URL(fileURLWithPath: output))
    let oracle: [String: Any] = [
        "legacy_maps_before_fixture_cleanup": oracleLegacyMapsBeforeCleanup,
        "mapping_words": (0..<14).map { setupOracleWord(Int32($0)) },
        "mapping_scans": (0..<4).map { stage in (0..<5).map { setupOracleScanWord(Int32(stage), Int32($0)) } },
        "mapping_queries": (0..<Int(setupOracleWord(12))).map { row in
            (0..<14).map { setupOracleQueryWord(Int32(row), Int32($0)) }
        }
    ]
    let oracleData = try JSONSerialization.data(withJSONObject: oracle, options: [.prettyPrinted, .sortedKeys])
    try oracleData.write(to: URL(fileURLWithPath: output + ".oracle.json"))""", manifest,
                 "retain a separate independent receipt without rewriting the legacy receipt")


def prepare_variant(inputs, out, variant):
    root = out / "source"
    shutil.copytree(inputs / "root", root)
    manifest = []
    worker = root / "runner/Sources/PWRunnerCore/CWorker.swift"
    edits = {
        "wrong_ready_direction": (
            "    posix_spawn_file_actions_adddup2(&fa, readyPipe[1], 4)\n",
            "    posix_spawn_file_actions_adddup2(&fa, readyPipe[0], 4)\n"),
        "wrong_shm_argv": ('        "--shm-fd", "3",\n', '        "--shm-fd", "4",\n'),
        "partial_unmap": ("        _ = munmap(base, PWShmLayout.regionBytes)\n",
                          "        _ = munmap(base, Int(getpagesize()))\n"),
    }
    if variant in edits:
        replace_once(worker, *edits[variant], manifest, "deliberate host counterexample: " + variant)
    add_observers(root / "tests/fixtures/host_setup", manifest)
    save(out / "instrumentation.json", dict(variant=variant, edits=manifest, files=inventory(root)))
    return root


MAPPING_KEYS = ("capture_count", "mapping_address", "acquired_bytes", "unmap_bytes", "page_bytes",
                "rounded_extent", "rounded_prefix", "owner_unmap_rc", "owner_unmap_errno",
                "fixture_cleanup_attempted", "fixture_cleanup_rc", "fixture_cleanup_errno",
                "query_count", "query_overflow")
SCAN_KEYS = ("start", "bytes", "complete", "mapped_bytes", "query_count")
QUERY_KEYS = ("stage", "query_address", "native_kr", "region_address", "region_bytes", "info_count",
              "object_name", "object_name_valid", "deallocation_attempted", "deallocation_kr",
              "protection", "max_protection", "shared", "object_offset")


def inspect_receipts(legacy, controls):
    observations = []
    for path in sorted(controls.glob("*.json")):
        receipt = json.loads(path.read_text())
        if not isinstance(receipt, dict) or "owner" not in receipt or "fault" not in receipt:
            continue
        row = dict(case=path.stem, receipt=str(path), legacy_accepted=False)
        try:
            row["legacy_verdict"] = legacy.check(receipt, receipt["owner"], receipt["fault"])
            row["legacy_accepted"] = True
        except Exception as error:
            row["legacy_error"] = repr(error)
        independent = json.loads(Path(str(path) + ".oracle.json").read_text())
        words = independent.pop("mapping_words")
        assert len(words) == len(MAPPING_KEYS), (path, words)
        independent.update(zip(MAPPING_KEYS, words))
        scans = independent.pop("mapping_scans")
        queries = independent.pop("mapping_queries")
        assert len(scans) == 4 and all(len(s) == len(SCAN_KEYS) for s in scans), (path, scans)
        assert len(queries) == independent["query_count"] and all(len(q) == len(QUERY_KEYS) for q in queries), (path, queries)
        independent["scans"] = [dict(zip(SCAN_KEYS, values)) for values in scans]
        independent["queries"] = [dict(zip(QUERY_KEYS, values)) for values in queries]
        row["mapping"] = independent
        row["owner"], row["fault"] = receipt["owner"], receipt["fault"]
        child = receipt["child"]
        if child:
            row["argv"] = child["oracle_argv"]
            row["fd_modes"] = {str(fd["fd"]): {key: value for key, value in fd.items() if key.startswith("oracle_")}
                               for fd in child["fds"]}
        observations.append(row)
    return observations


def assert_scan(mapped, stage, start, length, expected_mapped):
    """Reconstruct coverage from native ranges, including next-region answers."""
    scan = mapped["scans"][stage]
    queries = [q for q in mapped["queries"] if q["stage"] == stage]
    assert scan["start"] == start and scan["bytes"] == length and scan["complete"] == 1, scan
    assert queries and len(queries) == scan["query_count"], scan
    cursor, end, covered = start, start + length, 0
    for index, query in enumerate(queries):
        assert query["query_address"] == cursor, (scan, query)
        assert query["deallocation_attempted"] == query["object_name_valid"] and query["deallocation_kr"] == 0, query
        if query["native_kr"] == 1:  # KERN_INVALID_ADDRESS: no subsequent region.
            assert index == len(queries) - 1, queries
            cursor = end
            break
        assert query["native_kr"] == 0 and query["region_bytes"] > 0, query
        region, region_end = query["region_address"], query["region_address"] + query["region_bytes"]
        if region >= end:
            assert index == len(queries) - 1, queries
            cursor = end
            break
        assert region_end > cursor, query
        overlap_start, overlap_end = max(cursor, region), min(region_end, end)
        covered += overlap_end - overlap_start
        cursor = overlap_end
    assert cursor == end and covered == scan["mapped_bytes"] == expected_mapped, (scan, queries)


def assert_observations(variant, rows, results):
    assert len(rows) == 22 and all(row["legacy_accepted"] for row in rows), rows
    assert len([r for r in results if "case" in r]) == 22, results
    assert len([r for r in results if "rejected_control" in r]) == 10, results
    for row in rows:
        mapped = row["mapping"]
        assert mapped["capture_count"] == 1 and mapped["page_bytes"] > 0, row
        assert mapped["legacy_maps_before_fixture_cleanup"] == 0, row
        assert mapped["owner_unmap_rc"] == 0 and mapped["owner_unmap_errno"] == 0, row
        assert mapped["query_overflow"] == 0 and 0 < mapped["query_count"] <= 64, row
        address, extent, prefix = mapped["mapping_address"], mapped["rounded_extent"], mapped["rounded_prefix"]
        assert extent >= mapped["acquired_bytes"] > 0 and extent % mapped["page_bytes"] == 0, row
        assert_scan(mapped, 0, address, extent, extent)  # positive control on the actual acquisition
        partial = variant == "partial_unmap" and row["owner"].startswith("worker")
        if partial:
            assert mapped["acquired_bytes"] > mapped["unmap_bytes"] == mapped["page_bytes"], row
            assert prefix == mapped["page_bytes"] < extent, row
            assert_scan(mapped, 1, address, extent, extent - prefix)
            assert_scan(mapped, 2, address + prefix, extent - prefix, extent - prefix)
            assert mapped["fixture_cleanup_attempted"] == 1 and mapped["fixture_cleanup_rc"] == 0, row
            assert mapped["fixture_cleanup_errno"] == 0, row
            assert_scan(mapped, 3, address + prefix, extent - prefix, 0)
        else:
            assert mapped["unmap_bytes"] == mapped["acquired_bytes"] and prefix == extent, row
            assert_scan(mapped, 1, address, extent, 0)  # negative control after full native unmap
            assert mapped["fixture_cleanup_attempted"] == 0, row
            assert all(s["query_count"] == 0 for s in mapped["scans"][2:]), row
        if row["fault"] == "baseline" and row["owner"].startswith("worker"):
            expected = ["pw-probe-runner", "--shm-fd", "4" if variant == "wrong_shm_argv" else "3",
                        "--ready-fd", "4", "--step-count", "0"]
            if row["owner"] == "worker_token":
                expected += ["--extension-fd", "5"]
            assert row["argv"] == expected, row
            ready = row["fd_modes"]["4"]
            assert ready["oracle_fcntl_rc"] >= 0 and ready["oracle_fcntl_errno"] == 0, row
            assert ready["oracle_access_mode"] == (os.O_RDONLY if variant == "wrong_ready_direction" else os.O_WRONLY), row


def main(out):
    if not __debug__:
        raise RuntimeError("Python assertions must remain enabled")
    out.mkdir(parents=True)
    inputs = out / "inputs"
    root = inputs / "root"
    shutil.copytree(ROOT / "runner/Sources", root / "runner/Sources")
    shutil.copyfile(ROOT / "runner/Package.swift", root / "runner/Package.swift")
    shutil.copytree(ROOT / "tests/fixtures/host_setup", root / "tests/fixtures/host_setup")
    recipe = inputs / "host_setup_controls.py"
    shutil.copyfile(ROOT / "tests/suites/runner_unit/host_setup_controls.py", recipe)
    shutil.copyfile(Path(__file__), inputs / Path(__file__).name)
    shutil.copyfile(Path(__file__).with_suffix(".sh"), inputs / Path(__file__).with_suffix(".sh").name)
    save(inputs / "inventory.json", inventory(inputs))
    spec = importlib.util.spec_from_file_location("preserved_host_setup_controls", recipe)
    legacy = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True  # Keep the preserved input snapshot source-only.
    spec.loader.exec_module(legacy)
    summaries = []
    for variant in VARIANTS:
        directory = out / variant
        directory.mkdir()
        summary = dict(variant=variant, recipe_sha256=digest(recipe), ok=False)
        try:
            source = prepare_variant(inputs, directory, variant)
            legacy.ROOT = source
            legacy.FIXTURE = source / "tests/fixtures/host_setup"
            controls = directory / "legacy-controls"
            try:
                with (directory / "recipe.log").open("w") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                    legacy.run(controls)
                summary["legacy_recipe_completed"] = True
            except Exception as error:
                summary["legacy_recipe_completed"] = False
                summary["legacy_recipe_error"] = repr(error)
            rows = inspect_receipts(legacy, controls)
            save(directory / "independent-observations.json", rows)
            summary["old_oracle_acceptance"] = {r["case"]: r["legacy_accepted"] for r in rows}
            assert summary["legacy_recipe_completed"], summary
            results = json.loads((controls / "results.json").read_text())
            assert_observations(variant, rows, results)
            summary["ok"] = True
        except Exception as error:
            summary["error"] = repr(error)
        summaries.append(summary)
        save(out / "results.json", summaries)
    assert all(row["ok"] for row in summaries), summaries
    print("Baseline and three independently observed counterexamples accepted by the unchanged setup oracle; characterization only.")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
