"""检查 CSV 的列数、表头和空值；不修改输入文件。"""
import argparse
import csv
import json
import sys
from collections import Counter

VERSION = "0.1.0"


def positive_int(value):
    number = int(value)
    if number < 1:
        raise ValueError("必须为大于或等于 1 的整数")
    return number


def inspect_csv(path, blank_limit=1, encoding="utf-8-sig", delimiter=",", max_details=100):
    blank_limit = positive_int(blank_limit)
    max_details = positive_int(max_details)
    if len(delimiter) != 1 or delimiter in '\r\n"\0':
        raise ValueError("分隔符必须是单个字符，不能是换行、双引号或空字符")
    with open(path, encoding=encoding, newline="") as source:
        reader = csv.reader(source, delimiter=delimiter, strict=True)
        header = next(reader, None)
        if not header:
            raise ValueError("第一条 CSV 记录必须是非空表头")
        counts = Counter(header)
        blank_headers = [i + 1 for i, name in enumerate(header) if not name.strip()]
        duplicate_headers = [name for name in counts if counts[name] > 1]
        empty_counts = [0] * len(header)
        total = valid = mismatches = 0
        details = []
        while True:
            start_line = reader.line_num + 1
            row = next(reader, None)
            if row is None:
                break
            total += 1
            if len(row) != len(header):
                mismatches += 1
                if len(details) < max_details:
                    details.append({"record": total + 1, "start_line": start_line,
                                    "end_line": reader.line_num, "actual_columns": len(row)})
                continue
            valid += 1
            for i, value in enumerate(row):
                empty_counts[i] += int(not value.strip())
    columns = [{"position": i + 1, "name": name, "blank_cells": empty_counts[i],
                "alert": empty_counts[i] >= blank_limit} for i, name in enumerate(header)]
    return {"tool": "RowWidthBeacon", "version": VERSION, "expected_columns": len(header),
            "data_records": total, "matching_width_records": valid,
            "width_mismatch_count": mismatches, "width_mismatches": details,
            "details_truncated": mismatches > len(details),
            "blank_header_positions": blank_headers, "duplicate_headers": duplicate_headers,
            "blank_limit": blank_limit, "columns": columns,
            "has_findings": bool(mismatches or blank_headers or duplicate_headers
                                 or any(c["alert"] for c in columns))}


def format_report(report):
    lines = [f"RowWidthBeacon {VERSION}",
             f"Expected columns: {report['expected_columns']}",
             f"Data records: {report['data_records']}",
             f"Matching-width records: {report['matching_width_records']}",
             f"Width mismatches: {report['width_mismatch_count']}",
             f"Blank limit: {report['blank_limit']}",
             "Blank counts use matching-width records only."]
    for col in report["columns"]:
        state = "ALERT" if col["alert"] else "OK"
        lines.append(f"Column {col['position']} {json.dumps(col['name'], ensure_ascii=False)}: "
                     f"blank={col['blank_cells']} {state}")
    if report["blank_header_positions"]:
        lines.append(f"Blank headers at columns: {report['blank_header_positions']}")
    if report["duplicate_headers"]:
        lines.append("Duplicate headers: " + json.dumps(report["duplicate_headers"], ensure_ascii=False))
    for row in report["width_mismatches"]:
        lines.append(f"Record {row['record']}, lines {row['start_line']}-{row['end_line']}: "
                     f"actual columns={row['actual_columns']}")
    if report["details_truncated"]:
        lines.append("More mismatch details omitted; total counts are complete.")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", help="含表头的 CSV 文件")
    parser.add_argument("--rowwidthbeacon-blank-limit", type=positive_int, default=1,
                        help="同一列空值数量达到该整数时提示，默认 1；仅统计列数正常记录")
    parser.add_argument("--encoding", default="utf-8-sig")
    parser.add_argument("--delimiter", default=",", help="单字符分隔符，默认逗号")
    parser.add_argument("--max-details", type=positive_int, default=100)
    parser.add_argument("--json", action="store_true", help="向终端输出 JSON")
    parser.add_argument("--gui", action="store_true", help="打开本地窗口")
    parser.add_argument("--version", action="version", version=f"RowWidthBeacon {VERSION}")
    args = parser.parse_args(argv)
    if args.gui:
        from tool_window import run_window
        run_window("RowWidthBeacon", "空值提醒数量（整数，至少 1）", "1", inspect_csv, format_report)
        return 0
    if not args.file:
        parser.error("需要提供 CSV 文件路径，或使用 --gui")
    try:
        report = inspect_csv(args.file, args.rowwidthbeacon_blank_limit, args.encoding,
                             args.delimiter, args.max_details)
    except (OSError, UnicodeError, LookupError, ValueError, csv.Error) as error:
        print(f"RowWidthBeacon: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else format_report(report))
    return 1 if report["has_findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
