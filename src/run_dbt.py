"""Build and verify the local Commerce SQL/dbt snapshot before publishing its pointer."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb

from pipeline import REQUIRED, SOURCES, STATES, transform

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "dbt"
CONTRACT = "commerce-dbt-v1"
# Export names preserve the existing Power BI contract. Native SQL uses snake_case.
EXPORTS = {
    "Orders": ("fct_orders", [
        ("order_id", "Order ID"), ("purchase_date", "Purchase Date"), ("state", "State"),
        ("status", "Status"), ("delivered_date", "Delivered Date"), ("estimated_date", "Estimated Date"),
        ("item_count", "Item Count"), ("merchandise_cents", "Merchandise Cents"),
        ("freight_cents", "Freight Cents"), ("payment_cents", "Payment Cents"),
        ("payment_difference_cents", "Payment Difference Cents"), ("delivery_eligible", "Delivery Eligible"),
        ("late", "Late"), ("delivery_days", "Delivery Days"), ("late_days", "Late Days"),
        ("delivery_band", "Delivery Band")]),
    "Items": ("fct_order_items", [
        ("order_id", "Order ID"), ("item_number", "Item Number"), ("product_id", "Product ID"),
        ("purchase_date", "Purchase Date"), ("state", "State"), ("status", "Status"),
        ("category", "Category"), ("category_mapping", "Category Mapping"),
        ("price_cents", "Price Cents"), ("freight_cents", "Freight Cents"), ("category_group", "Category Group")]),
    "Dates": ("dim_dates", [("date", "Date"), ("month", "Month"), ("year", "Year")]),
    "States": ("dim_states", [("state", "State")]),
    "Categories": ("dim_categories", [("category", "Category")]),
    "Exceptions": ("order_exceptions", [("order_id", "Order ID"), ("rule", "Rule"), ("detail", "Detail")]),
    "Quality": ("quality_checks", [("check_name", "Check"), ("rows", "Rows")]),
    "Refresh": ("refresh_metadata", [("snapshot", "Snapshot"), ("built_utc", "Built UTC"),
        ("source_orders", "Source Orders"), ("source_items", "Source Items"),
        ("exception_events", "Exception Events"), ("orders_with_exceptions", "Orders With Exceptions")]),
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize(value):
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def canonical(rows, columns):
    return Counter(tuple(normalize(row.get(column)) for column in columns) for row in rows)


def compare_rows(label, actual, expected, columns):
    left, right = canonical(actual, columns), canonical(expected, columns)
    if left != right:
        extra, missing = left - right, right - left
        # Diagnostic only; raw source records remain local and are not published.
        raise ValueError(f"{label} reconciliation failed: {sum(extra.values())} unexpected, "
                         f"{sum(missing.values())} missing rows; first difference "
                         f"{next(iter(extra or missing), None)}")
    return {"rows": len(actual), "columns_compared": len(columns), "all_values_match": True}


def source_info(raw):
    hashes = {}
    for name, (filename, _) in SOURCES.items():
        path = raw / filename
        with path.open(encoding="utf-8-sig", newline="") as stream:
            header = next(csv.reader(stream))
        if len(header) != len(set(header)) or not REQUIRED[name].issubset(header):
            raise ValueError(f"{filename}: duplicate or missing required columns")
        hashes[filename] = digest(path)
    return hashes


def transformation_hashes():
    paths = [p for p in PROJECT.rglob("*") if p.is_file()
             and p.suffix in {".sql", ".yml", ".txt"}
             and not {"target", "logs", "dbt_packages"}.intersection(p.parts)]
    paths += [Path(__file__), ROOT / "src/pipeline.py"]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(paths)}


def land_raw(connection, raw, hashes, snapshot, loaded_at):
    connection.execute("create schema raw")
    counts = {}
    for name, (filename, _) in SOURCES.items():
        columns = ", ".join('"' + c + '"' for c in sorted(REQUIRED[name]))
        connection.execute(f"""create table raw.{name} as
            select row_number() over ()::bigint as source_record_number, {columns}
            from read_csv(?, header=true, all_varchar=true, parallel=false,
                          strict_mode=true, null_padding=false)""", [str(raw / filename)])
        counts[name] = connection.execute(f"select count(*) from raw.{name}").fetchone()[0]
    if not counts["orders"]:
        raise ValueError("A Commerce snapshot must contain at least one order")
    connection.execute("""create table raw.ingestion_metadata (
        source_name varchar, source_filename varchar, source_sha256 varchar,
        source_rows bigint, snapshot_id varchar, loaded_at_utc varchar)""")
    connection.executemany("insert into raw.ingestion_metadata values (?, ?, ?, ?, ?, ?)", [
        (name, filename, hashes[filename], counts[name], snapshot, loaded_at)
        for name, (filename, _) in SOURCES.items()])
    return counts


def invoke_dbt(command, database, target, logs):
    cli = Path(sys.executable).parent / ("dbt.exe" if os.name == "nt" else "dbt")
    if not cli.is_file():
        raise RuntimeError("Run with the Python environment where dbt/requirements.txt is installed")
    env = dict(os.environ, COMMERCE_DUCKDB_PATH=str(database.resolve()).replace("\\", "/"),
               DBT_SEND_ANONYMOUS_USAGE_STATS="false", DBT_USE_COLORS="false",
               DBT_TARGET_PATH=str(target), DBT_LOG_PATH=str(logs))
    result = subprocess.run([str(cli), *command, "--project-dir", str(PROJECT),
                             "--profiles-dir", str(PROJECT)], env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    logs.mkdir(parents=True, exist_ok=True)
    (logs / (command[0] + "-console.txt")).write_text(result.stdout, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"dbt {' '.join(command)} failed:\n{result.stdout[-12000:]}")
    return result.stdout


def export_and_verify(connection, destination, raw):
    exported, checks = {}, {}
    for export, (model, mapping) in EXPORTS.items():
        query = 'select ' + ', '.join(f'"{a}" as "{b}"' for a, b in mapping)
        query += f' from analytics_marts."{model}" order by ' + ', '.join(str(i + 1) for i in range(len(mapping)))
        cursor = connection.execute(query)
        columns = [column[0] for column in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        exported[export] = rows
        with (destination / (export + ".csv")).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows({k: normalize(v) for k, v in row.items()} for row in rows)
    tables = {}
    for name, (filename, _) in SOURCES.items():
        with (raw / filename).open(encoding="utf-8-sig", newline="") as stream:
            tables[name] = [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(stream)]
    expected_orders, expected_items, expected_exceptions = transform(tables)
    for label, expected in [("Orders", expected_orders), ("Items", expected_items), ("Exceptions", expected_exceptions)]:
        checks[label] = compare_rows(label, exported[label], expected, [b for _, b in EXPORTS[label][1]])
    return exported, checks


def verify_demo(raw_hashes, exported):
    archive = ROOT / "sample-data.zip"
    expected_digest = (ROOT / "sample-data.sha256").read_text(encoding="utf-8").split()[0]
    if digest(archive) != expected_digest:
        raise ValueError("Published baseline archive checksum mismatch")
    checks = {}
    with zipfile.ZipFile(archive) as baseline:
        manifest_name = next(n for n in baseline.namelist() if n.endswith("/manifest.json"))
        manifest = json.loads(baseline.read(manifest_name))
        if raw_hashes != manifest["source_hashes"]:
            raise ValueError("--compare-demo requires the original six source-file hashes")
        prefix = manifest_name.rsplit("/", 1)[0]
        for label in EXPORTS:
            if label == "Refresh":
                continue  # Build timestamp and transformation fingerprint must change.
            text = baseline.read(prefix + "/" + label + ".csv").decode("utf-8-sig")
            expected = list(csv.DictReader(text.splitlines()))
            checks[label] = compare_rows("Published " + label, exported[label], expected,
                                        [b for _, b in EXPORTS[label][1]])
    return checks


def verify_snapshot(snapshot):
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["artifact_hashes"].items():
        if digest(snapshot / name) != expected:
            raise ValueError(f"Existing output changed: {name}; restore before publishing")
    return manifest


def build(raw, output, compare_demo=False, generate_docs=False, progress=None):
    say = progress or (lambda message: None)
    raw, output = Path(raw).resolve(), Path(output).resolve()
    hashes = source_info(raw)
    logic = transformation_hashes()
    snapshot = hashlib.sha256(json.dumps([CONTRACT, hashes, logic], sort_keys=True).encode()).hexdigest()[:20]
    destination = output / "snapshots" / snapshot
    output.mkdir(parents=True, exist_ok=True)
    attempt = uuid.uuid4().hex[:12]
    loaded_at = datetime.now(timezone.utc).isoformat()
    with tempfile.TemporaryDirectory(prefix="commerce-dbt-") as temporary:
        work = Path(temporary)
        candidate = work / "snapshot"
        candidate.mkdir()
        database = candidate / "commerce.duckdb"
        target, logs = work / "target", work / "logs"
        try:
            say('1/5 Landing six source tables and recording hashes...')
            frozen_raw = work / "raw"
            frozen_raw.mkdir()
            for filename, expected_hash in hashes.items():
                shutil.copy2(raw / filename, frozen_raw / filename)
                if digest(frozen_raw / filename) != expected_hash:
                    raise ValueError(f"Source changed while freezing inputs: {filename}")
            with duckdb.connect(str(database)) as connection:
                counts = land_raw(connection, frozen_raw, hashes, snapshot, loaded_at)
            say('2/5 Building SQL models and running dbt tests...')
            invoke_dbt(["build"], database, target, logs)
            say('3/5 Reconciling every order, item and exception field...')
            with duckdb.connect(str(database), read_only=True) as connection:
                exported, checks = export_and_verify(connection, candidate, frozen_raw)
            demo_checks = verify_demo(hashes, exported) if compare_demo else None
            if transformation_hashes() != logic:
                raise ValueError('Transformation files changed during the build; run again with stable source code')
            if generate_docs:
                say('4/5 Generating local model documentation and lineage...')
                invoke_dbt(["docs", "generate", "--static"], database, target, logs)
            for filename in ("manifest.json", "run_results.json", "catalog.json", "static_index.html"):
                if (target / filename).is_file():
                    (candidate / "dbt-artifacts").mkdir(exist_ok=True)
                    shutil.copy2(target / filename, candidate / "dbt-artifacts" / filename)
            result_data = json.loads((target / "run_results.json").read_text(encoding="utf-8"))
            orders, items = exported["Orders"], exported["Items"]
            manifest = {
                "contract_version": 1, "transformation_contract": CONTRACT, "snapshot": snapshot,
                "built_at_utc": loaded_at, "source_hashes": hashes, "transformation_hashes": logic,
                "source_rows": counts, "orders": len(orders), "items": len(items),
                "delivery_eligible": sum(o["Delivery Eligible"] for o in orders),
                "late_orders": sum(o["Late"] for o in orders),
                "delivered_merchandise_cents": sum(o["Merchandise Cents"] for o in orders if o["Status"] == "Delivered"),
                "all_merchandise_cents": sum(o["Merchandise Cents"] for o in orders),
                "payment_difference_orders": sum(o["Payment Difference Cents"] not in (None, 0) for o in orders),
                "exception_events": len(exported["Exceptions"]),
                "orders_with_exceptions": len({e["Order ID"] for e in exported["Exceptions"]}),
                "source_license": "CC BY-NC-SA 4.0", "reference_checks": checks,
                "published_baseline_checks": demo_checks,
                "versions": {p: importlib.metadata.version(p) for p in ("dbt-core", "dbt-duckdb", "duckdb")},
                "dbt_results": dict(Counter(r["status"] for r in result_data["results"])),
                "artifact_hashes": {p.relative_to(candidate).as_posix(): digest(p) for p in candidate.rglob("*") if p.is_file()},
            }
            (candidate / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            # Verify an existing immutable result before reuse. Every invocation still builds/tests anew.
            if destination.exists():
                prior = verify_snapshot(destination)
                if compare_demo and not prior.get("published_baseline_checks"):
                    raise ValueError("This result was not recorded with baseline comparison; use a separate output folder")
                if generate_docs and not (destination / "dbt-artifacts/static_index.html").exists():
                    raise ValueError("This result has no docs; use a separate output folder for --docs")
                manifest = prior
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                staged = destination.parent / (".pending-" + attempt)
                shutil.copytree(candidate, staged)
                verify_snapshot(staged)
                os.replace(staged, destination)
            say('5/5 Publishing the verified snapshot pointer...')
            # Existing Power BI data/processed/latest.json is never touched.
            pending = output / (attempt + ".pending.json")
            pending.write_text(json.dumps({"snapshot": snapshot, "contract_version": 1}) + "\n", encoding="utf-8")
            os.replace(pending, output / "latest.json")
            return manifest
        except Exception as exc:
            failure = output / "failures" / attempt
            failure.mkdir(parents=True, exist_ok=True)
            if logs.exists():
                shutil.copytree(logs, failure / "logs")
            if (target / "run_results.json").exists():
                shutil.copy2(target / "run_results.json", failure / "run_results.json")
            (failure / "failure.json").write_text(json.dumps({"attempt": attempt,
                "snapshot": snapshot, "error": str(exc), "previous_pointer_preserved": True}, indent=2), encoding="utf-8")
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=ROOT / "data/raw")
    parser.add_argument("--output", type=Path, default=ROOT / "data/dbt")
    parser.add_argument("--compare-demo", action="store_true")
    parser.add_argument("--docs", action="store_true", help="Generate a self-contained local lineage/documentation page")
    options = parser.parse_args()
    result = build(options.raw, options.output, options.compare_demo, options.docs, progress=print)
    print(json.dumps({k: result[k] for k in ("snapshot", "orders", "items", "delivery_eligible", "late_orders", "dbt_results")}, indent=2))
