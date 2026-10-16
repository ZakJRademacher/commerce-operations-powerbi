"""Author the editable native Power BI project. No third-party visuals required."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PBI = ROOT / "powerbi"
REPORT = PBI / "Commerce.Report"
MODEL = PBI / "Commerce.SemanticModel"
BASE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"


def put(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")


def literal(value):
    if isinstance(value, bool):
        value = str(value).lower()
    elif isinstance(value, (int, float)):
        value = str(value) + "D"
    else:
        value = "'" + value.replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": value}}}


def color(value):
    return {"solid": {"color": literal(value)}}


MEASURES = {
    "Orders": {
        "Orders": ("COUNTROWS(Orders)", "#,0", "One row per source order; all statuses retained."),
        "Delivered Orders": ('CALCULATE([Orders], Orders[Status] = "Delivered")', "#,0", "Source status Delivered, including those missing timing."),
        "Delivered Merchandise BRL": ('DIVIDE(CALCULATE(SUM(Orders[Merchandise Cents]), Orders[Status] = "Delivered"), 100)', '"R$ "#,0.00', "Delivered order item prices, excludes freight. Not profit or recognized revenue."),
        "Eligible Deliveries": ("SUM(Orders[Delivery Eligible])", "#,0", "Delivered status and valid actual/estimated timing; delivery not before purchase."),
        "Late Deliveries": ("SUM(Orders[Late])", "#,0", "Eligible deliveries whose actual calendar date exceeds estimated calendar date."),
        "On Time Rate": ("DIVIDE([Eligible Deliveries] - [Late Deliveries], [Eligible Deliveries])", "0.0%", "Eligible denominator; blank where none are eligible."),
        "Late Rate Trend": ("IF([Eligible Deliveries] >= 100, [Late Rate])", "0.0%", "Monthly trend suppressed where fewer than 100 eligible deliveries; totals elsewhere remain unchanged."),
        "Late Rate": ("DIVIDE([Late Deliveries], [Eligible Deliveries])", "0.0%", "Late eligible deliveries divided by eligible deliveries."),
        "Median Delivery Days": ('CALCULATE(MEDIAN(Orders[Delivery Days]), Orders[Delivery Eligible] = 1)', '0.0" days"', "Median calendar days purchase to delivery for eligible orders."),
        "Average Late Days": ('CALCULATE(AVERAGE(Orders[Late Days]), Orders[Late] = 1)', '0.0" days"', "Mean lateness among late orders only."),
        "Timing Exclusions": ("[Delivered Orders] - [Eligible Deliveries]", "#,0", "Delivered orders excluded from timing calculations."),
    },
    "Items": {
        "Item Lines": ("COUNTROWS(Items)", "#,0", "One row per source item; each row represents one ordered unit."),
        "Delivered Item Lines": ('CALCULATE([Item Lines], Items[Status] = "Delivered")', "#,0", "Source item rows whose order status is delivered."),
        "Category Merchandise BRL": ('DIVIDE(CALCULATE(SUM(Items[Price Cents]), Items[Status] = "Delivered"), 100)', '"R$ "#,0.00', "Delivered item prices; responds to category filters."),
        "Delivered Freight BRL": ('DIVIDE(CALCULATE(SUM(Items[Freight Cents]), Items[Status] = "Delivered"), 100)', '"R$ "#,0.00', "Source item-level freight charges for delivered orders."),
        "Freight to Merchandise": ("DIVIDE([Delivered Freight BRL], [Category Merchandise BRL])", "0.0%", "Freight divided by merchandise; not margin and not share of gross checkout."),
        "Uncategorized Lines": ('CALCULATE([Item Lines], Items[Category Mapping] = "Missing source category")', "#,0", "Item rows with missing source product category."),
    },
    "Refresh": {
        "Snapshot Orders": ("SUM('Refresh'[Source Orders])", "#,0", "Full unfiltered snapshot order count."),
        "Snapshot Items": ("SUM('Refresh'[Source Items])", "#,0", "Full unfiltered snapshot item count."),
        "Orders With Exceptions": ("SUM('Refresh'[Source Orders With Exceptions])", "#,0", "Distinct orders with one or more exception events."),
        "Exception Events": ("SUM('Refresh'[Source Exception Events])", "#,0", "Events can overlap; do not add them as distinct affected orders."),
    },
    "Quality": {"Flagged Rows": ("IF(ISINSCOPE(Quality[Check]), SUM(Quality[Rows]))", "#,0", "Row count for the selected quality check; grains can differ and overlap.")},
}


def build_model():
    processed = ROOT / "data/processed"
    pointer = json.loads((processed / "latest.json").read_text(encoding="utf-8"))
    snapshot = processed / "snapshots" / pointer["snapshot"]
    tables = []
    m_queries = {}
    for name in ("Orders", "Items", "Dates", "States", "Categories", "Quality", "Refresh"):
        with (snapshot / f"{name}.csv").open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        columns, conversions = [], []
        for col in rows[0]:
            is_date = col in {"Date", "Purchase Date", "Delivered Date", "Estimated Date"}
            is_int = col.endswith(" Cents") or col in {"Item Number", "Item Count", "Delivery Eligible", "Late", "Delivery Days", "Late Days", "Year", "Rows", "Source Orders", "Source Items", "Exception Events", "Orders With Exceptions"}
            dtype = "dateTime" if is_date else "int64" if is_int else "string"
            entry = {"name": "Source " + col if col in MEASURES.get(name, {}) else col, "dataType": dtype, "sourceColumn": col, "summarizeBy": "none"}
            if is_date:
                entry.update(formatString="yyyy-MM-dd", annotations=[{"name": "UnderlyingDateTimeDataType", "value": "Date"}])
            if is_int and name in ("Orders", "Items"):
                entry["isHidden"] = True
            columns.append(entry)
            conversions.append('{"' + col + '", ' + ("type date" if is_date else "Int64.Type" if is_int else "type text") + '}')
        query = [
            "let",
            '    Pointer = Json.Document(File.Contents(DataRoot & "/latest.json")),',
            '    Contract = if Pointer[contract_version] = 1 then Pointer[snapshot] else error "Unsupported data contract",',
            f'    Source = Csv.Document(File.Contents(DataRoot & "/snapshots/" & Contract & "/{name}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
            '    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
            '    Typed = Table.TransformColumnTypes(Headers, {' + ", ".join(conversions) + '}, "en-US")',
            "in", "    Typed",
        ]
        m_queries[name] = "\n".join(query)
        tables.append({"name": name, "columns": columns,
            "measures": [{"name": n, "expression": expr, "formatString": fmt, "description": desc} for n, (expr, fmt, desc) in MEASURES.get(name, {}).items()],
            "partitions": [{"name": name, "mode": "import", "source": {"type": "m", "expression": query}}]})
    relationships = []
    for fact in ("Orders", "Items"):
        for dim, key, fact_key in (("Dates", "Date", "Purchase Date"), ("States", "State", "State")):
            relationships.append({"name": f"{fact}_{dim}", "fromTable": fact, "fromColumn": fact_key, "toTable": dim, "toColumn": key, "crossFilteringBehavior": "oneDirection"})
    relationships.append({"name": "Items_Categories", "fromTable": "Items", "fromColumn": "Category", "toTable": "Categories", "toColumn": "Category", "crossFilteringBehavior": "oneDirection"})
    model = {"name": "Commerce", "compatibilityLevel": 1600, "model": {
        "culture": "en-US", "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "expressions": [{"name": "DataRoot", "kind": "m", "expression": '"' + processed.as_posix() + '" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}],
        "tables": tables, "relationships": relationships,
        "annotations": [{"name": "PBI_QueryOrder", "value": json.dumps(["DataRoot"] + list(m_queries))}],
    }}
    put(MODEL / "model.bim", model)
    put(MODEL / "definition.pbism", {"version": "1.0"})
    (PBI / "power-query.m").write_text("// DataRoot: set to your local data/processed directory\n\n" + "\n\n".join("// " + n + "\n" + q for n, q in m_queries.items()) + "\n", encoding="utf-8")
    (PBI / "measures.dax").write_text("\n\n".join("// " + desc + "\n" + n + " =\n" + expr for measures in MEASURES.values() for n, (expr, _, desc) in measures.items()) + "\n", encoding="utf-8")


def projection(table, field, measure=False):
    return {"field": {"Measure" if measure else "Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": field}}, "queryRef": f"{table}.{field}", "nativeQueryRef": field}


def visual(page, name, kind, x, y, w, h, title=None, roles=None, objects=None, sort=None):
    v = {"visualType": kind, "drillFilterOtherVisuals": True}
    if roles:
        v["query"] = {"queryState": {role: {"projections": [projection(*p) for p in fields]} for role, fields in roles.items()}}
        if sort:
            v["query"]["sortDefinition"] = {"sort": [{"field": projection(*sort[:3])["field"], "direction": sort[3]}], "isDefaultSort": False}
    v["visualContainerObjects"] = {
        "background": [{"properties": {"show": literal(True), "color": color("#FFFFFF"), "transparency": literal(0)}}],
        "border": [{"properties": {"show": literal(False)}}],
        "title": [{"properties": {"show": literal(bool(title)), "text": literal(title or ""), "fontColor": color("#172E46"), "fontSize": literal(13), "bold": literal(True), "fontFamily": literal("Segoe UI")}}],
    }
    if objects:
        v["objects"] = objects
    put(REPORT / f"definition/pages/{page}/visuals/{name}/visual.json", {"$schema": BASE + "visualContainer/2.0.0/schema.json", "name": name, "position": {"x": x, "y": y, "width": w, "height": h, "z": 0, "tabOrder": y * 10 + x}, "visual": v})


def text(page, name, content, x, y, w, h, size=12, ink="#566A7B"):
    visual(page, name, "textbox", x, y, w, h, objects={"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": content, "textStyle": {"fontFamily": "Segoe UI", "fontSize": str(size) + "pt", "color": ink}}]}]}}]})


def card(page, name, table, metric, x):
    visual(page, name, "card", x, 190, 292, 120, title=metric, roles={"Values": [(table, metric, True)]}, objects={
        "labels": [{"properties": {"color": color("#127C80"), "fontSize": literal(26), "labelDisplayUnits": literal(1), "precision": literal(0 if metric in {"Orders", "Eligible Deliveries", "Late Deliveries", "Delivered Item Lines", "Snapshot Orders", "Snapshot Items", "Orders With Exceptions", "Exception Events"} else 1)}}],
        "categoryLabels": [{"properties": {"show": literal(False)}}],
    })


def slicer(page, name, table, field, x, w):
    visual(page, name, "slicer", x, 105, w, 65, title=field + " | All by default", roles={"Values": [(table, field)]}, objects={
        "data": [{"properties": {"mode": literal("Dropdown")}}],
        "header": [{"properties": {"show": literal(False)}}],
        "selection": [{"properties": {"singleSelect": literal(False), "selectAllCheckboxEnabled": literal(True)}}],
    })


def build_report():
    put(PBI / "Commerce.pbip", {"version": "1.0", "artifacts": [{"report": {"path": "Commerce.Report"}}]})
    put(REPORT / "definition.pbir", {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json", "version": "4.0", "datasetReference": {"byPath": {"path": "../Commerce.SemanticModel"}}})
    put(REPORT / "definition/version.json", {"$schema": BASE + "versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    # Native theme is a registered resource; no visual plug-ins or network credentials.
    put(REPORT / "StaticResources/RegisteredResources/CommerceTheme.json", {
        "name": "Commerce Operations", "dataColors": ["#127C80", "#E09B41", "#486886", "#B64A55", "#93BABA", "#7D739F"],
        "background": "#FFFFFF", "foreground": "#172E46", "tableAccent": "#127C80",
        "textClasses": {"title": {"fontFace": "Segoe UI", "fontSize": 13, "color": "#172E46"}, "label": {"fontFace": "Segoe UI", "fontSize": 11, "color": "#566A7B"}, "callout": {"fontFace": "Segoe UI", "color": "#127C80"}},
    })
    put(REPORT / "definition/report.json", {"$schema": BASE + "report/3.0.0/schema.json", "themeCollection": {"customTheme": {"name": "CommerceTheme", "reportVersionAtImport": {"visual": "1.8.0", "page": "2.0.0", "report": "3.0.0"}, "type": "RegisteredResources"}}, "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources", "items": [{"name": "CommerceTheme", "path": "CommerceTheme.json", "type": "CustomTheme"}]}]})
    # Preserve a built-in base theme as Desktop does; the custom palette overlays it.
    report_path = REPORT / "definition/report.json"
    definition = json.loads(report_path.read_text(encoding="utf-8"))
    definition["themeCollection"]["baseTheme"] = {"name": "CY24SU02", "reportVersionAtImport": {"visual": "1.8.89", "report": "2.0.89", "page": "1.3.89"}, "type": "SharedResources"}
    definition["themeCollection"]["customTheme"]["reportVersionAtImport"] = {"visual": "1.8.101", "report": "2.0.101", "page": "1.3.101"}
    definition["resourcePackages"].insert(0, {"name": "SharedResources", "type": "SharedResources", "items": [{"name": "CY24SU02", "path": "BaseThemes/CY24SU02.json", "type": "BaseTheme"}]})
    put(report_path, definition)
    pages = {"overview": ("01  Overview", "ORDER & DELIVERY OPERATIONS", "Start here: choose a purchase month or state. Click a chart to explore its contribution."),
        "delivery": ("02  Delivery", "WHERE DOES DELIVERY NEED REVIEW?", "Prioritize by late-order volume, then compare rates. Timing uses actual versus estimated calendar dates."),
        "products": ("03  Products", "WHAT DRIVES MERCHANDISE & FREIGHT?", "Category filters apply to item metrics on this page. All amounts are Brazilian reais; freight is not profit."),
        "quality": ("04  Quality & Refresh", "TRUST THE NUMBERS", "Full-snapshot checks are intentionally unfiltered. Exception events overlap; affected-order counts are distinct.")}
    put(REPORT / "definition/pages/pages.json", {"$schema": BASE + "pagesMetadata/1.0.0/schema.json", "pageOrder": list(pages), "activePageName": "overview"})
    for page, (display, title, subtitle) in pages.items():
        put(REPORT / f"definition/pages/{page}/page.json", {"$schema": BASE + "page/2.0.0/schema.json", "name": page, "displayName": display, "displayOption": "FitToPage", "height": 900, "width": 1280, "objects": {"background": [{"properties": {"color": color("#F2F5F8"), "transparency": literal(0)}}]}})
        text(page, "title", title, 24, 16, 1228, 55, 22, "#172E46")
        text(page, "instructions", subtitle, 24, 62, 1228, 35, 11)
        text(page, "footer", "OLIST / Historical portfolio analysis • purchases 2016–2018 • CC BY-NC-SA 4.0 • Zak Rademacher", 24, 860, 1230, 35, 10)
        if page != "quality":
            slicer(page, "month", "Dates", "Month", 24, 390)
            slicer(page, "state", "States", "State", 430, 250)
    for x, metric in zip((24, 336, 648, 960), ("Orders", "Delivered Merchandise BRL", "On Time Rate", "Median Delivery Days")):
        card("overview", "kpi" + str(x), "Orders", metric, x)
    visual("overview", "trend", "lineChart", 24, 334, 792, 390, "Orders by purchase month | includes all statuses", {"Category": [("Dates", "Month")], "Y": [("Orders", "Orders", True)]}, sort=("Dates", "Month", False, "Ascending"))
    visual("overview", "status", "clusteredBarChart", 840, 334, 412, 390, "Order status", {"Category": [("Orders", "Status")], "Y": [("Orders", "Orders", True)]}, sort=("Orders", "Orders", True, "Descending"))
    text("overview", "guide", "READ THIS FIRST\nDelivered merchandise excludes freight and canceled orders. On-time rate excludes delivered orders with invalid timing. The last purchase months are partial historical periods; this is not a current operating backlog. Use the tabs below for delivery, products, and quality.", 24, 746, 1228, 100, 12)
    for x, metric in zip((24, 336, 648, 960), ("Eligible Deliveries", "Late Deliveries", "On Time Rate", "Average Late Days")):
        card("delivery", "kpi" + str(x), "Orders", metric, x)
    visual("delivery", "states", "clusteredBarChart", 24, 334, 594, 310, "Late deliveries by state | volume", {"Category": [("States", "State")], "Y": [("Orders", "Late Deliveries", True)]}, sort=("Orders", "Late Deliveries", True, "Descending"))
    visual("delivery", "lateTrend", "lineChart", 642, 334, 610, 310, "Late rate by month | 100+ eligible deliveries", {"Category": [("Dates", "Month")], "Y": [("Orders", "Late Rate Trend", True)]}, sort=("Dates", "Month", False, "Ascending"))
    visual("delivery", "stateReview", "tableEx", 24, 662, 1228, 190, "State review | inspect volume alongside rate", {"Values": [("States", "State"), ("Orders", "Eligible Deliveries", True), ("Orders", "Late Deliveries", True), ("Orders", "Late Rate", True), ("Orders", "Median Delivery Days", True)]}, sort=("Orders", "Late Deliveries", True, "Descending"))
    slicer("products", "category", "Categories", "Category", 696, 556)
    for x, metric in zip((24, 336, 648, 960), ("Category Merchandise BRL", "Delivered Item Lines", "Delivered Freight BRL", "Freight to Merchandise")):
        card("products", "kpi" + str(x), "Items", metric, x)
    visual("products", "categoryGroups", "clusteredBarChart", 24, 334, 680, 460, "Top 10 snapshot categories + other | delivered merchandise", {"Category": [("Items", "Category Group")], "Y": [("Items", "Category Merchandise BRL", True)]}, sort=("Items", "Category Merchandise BRL", True, "Descending"))
    visual("products", "categoryDetail", "tableEx", 728, 334, 524, 460, "Category detail | scroll for all categories", {"Values": [("Categories", "Category"), ("Items", "Category Merchandise BRL", True), ("Items", "Freight to Merchandise", True)]}, sort=("Items", "Category Merchandise BRL", True, "Descending"))
    text("products", "scope", "The top-10 grouping is fixed for the full source snapshot. Slicers recalculate values, not membership. Uncategorized and untranslated source labels stay visible in category detail.", 24, 810, 1228, 45, 11)
    text("quality", "refreshGuide", "REFRESH: replace the six source CSVs → run python src/pipeline.py → Power BI Home > Refresh. A failed validation keeps the previous snapshot pointer. No live Kaggle feed or unattended schedule is configured.", 24, 108, 1228, 65, 12)
    for x, metric in zip((24, 336, 648, 960), ("Snapshot Orders", "Snapshot Items", "Orders With Exceptions", "Exception Events")):
        card("quality", "kpi" + str(x), "Refresh", metric, x)
    visual("quality", "checks", "tableEx", 24, 334, 760, 330, "Quality checks | order and item grains are labeled", {"Values": [("Quality", "Check"), ("Quality", "Flagged Rows", True)]}, sort=("Quality", "Flagged Rows", True, "Descending"))
    visual("quality", "snapshot", "tableEx", 808, 334, 444, 160, "Imported snapshot", {"Values": [("Refresh", "Snapshot"), ("Refresh", "Built UTC")]})
    text("quality", "rules", "METRIC CONTRACT\n• Orders: one row per order.\n• Items: one row per order item.\n• Payments aggregate before joining.\n• Late = actual date > estimated date.\n• Missing dates are never imputed.\n• Category filters affect Items only.", 808, 512, 444, 190, 12)
    text("quality", "limitations", "SOURCE & LIMITS\nOlist Brazilian E-Commerce Public Dataset via Kaggle. Historical 2016–2018 records, shared under CC BY-NC-SA 4.0. Merchandise is not profit. Payment differences are flagged, not forced to zero. No delivery cause, staffing benefit, or current backlog is inferred. Read the handoff guide for source attribution, refresh setup, definitions, and exception-level CSVs.", 24, 724, 1228, 126, 12)


if __name__ == "__main__":
    build_model()
    build_report()
    print(PBI / "Commerce.pbip")
