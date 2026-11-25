"""Turn one OCI Document Understanding analysis into an invoice intake decision."""
import argparse
import json
import math
from html import escape
from pathlib import Path

from policy import select


def get_key(data, rest_key, cli_key):
    return data.get(rest_key, data.get(cli_key))


def solve(document, brief):
    config = brief["settings"]
    required = config["required_fields"]
    threshold = config["min_confidence"]
    if (not isinstance(required, list) or not required or
            any(not isinstance(key, str) or not key.strip() for key in required) or
            len(set(required)) != len(required)):
        raise ValueError("required_fields must list distinct field names")
    if type(threshold) not in (int, float) or not 0 < threshold <= 1:
        raise ValueError("min_confidence must be greater than zero and at most one")

    analysis = document.get("data", document)
    pages = analysis.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("expected an OCI analysis with at least one page")
    evidence = {key: [] for key in required}
    issues = []
    if analysis.get("errors"):
        issues.append("Document analysis reported an error")
    for number, page in enumerate(pages, 1):
        if page.get("errors"):
            issues.append(f"Page {number} analysis reported an error")
        for field in get_key(page, "documentFields", "document-fields") or []:
            if get_key(field, "fieldType", "field-type") != "KEY_VALUE":
                continue
            label = get_key(field, "fieldLabel", "field-label") or {}
            key = label.get("name")
            value = get_key(field, "fieldValue", "field-value") or {}
            text = value.get("text")
            if key not in evidence or not isinstance(text, str) or not text.strip():
                continue
            score = label.get("confidence")
            if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
                score = 0
            evidence[key].append({"text": text.strip(), "confidence": score,
                                  "page": get_key(page, "pageNumber", "page-number") or number})

    for key, readings in evidence.items():
        chosen, reason = select(readings)
        if reason is None and chosen["confidence"] < threshold:
            reason = "low confidence"
        if reason:
            issues.append(f"{key}: {reason}")
    return {"route": "Needs review" if issues else "Ready for entry",
            "issues": issues, "evidence": evidence}


def render(brief, documents):
    rows = []
    review_count = 0
    for path in documents:
        result = solve(json.loads(path.read_text()), brief)
        review_count += int(bool(result["issues"]))
        details = []
        for key, readings in result["evidence"].items():
            values = [f'{escape(item["text"])} (p. {escape(str(item["page"]))}, {item["confidence"]:.0%})'
                      for item in readings]
            details.append(f'<strong>{escape(key)}</strong> &nbsp;{" · ".join(values) or "Missing"}')
        reason = "<br>".join(escape(item) for item in result["issues"]) or "Required fields passed"
        kind = "review" if result["issues"] else "ready"
        rows.append(f'<tr><th scope="row">{escape(path.stem)}</th><td class="{kind}">{result["route"]}</td>'
                    f'<td>{reason}</td><td>{"<br>".join(details)}</td></tr>')
    template = Path(__file__).with_name("report.html").read_text()
    from string import Template
    return Template(template).substitute(customer=escape(brief["customer"]), rows="\n".join(rows),
                                         review=review_count, total=len(documents))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("documents", nargs="*", type=Path, help="OCI CLI or REST response JSON files")
    parser.add_argument("--out", type=Path, default=Path("output/review.html"))
    args = parser.parse_args()
    home = Path(__file__).resolve().parent
    docs = args.documents or sorted((home / "samples").glob("*.json"))
    if not docs:
        parser.error("supply at least one analysis response")
    report = render(json.loads((home / "brief.json").read_text()), docs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(args.out.resolve())
