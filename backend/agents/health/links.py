"""Health houses on House Links — the same status, dasha and transit moment as Gochar and Forecast."""

from __future__ import annotations

from datetime import datetime

from agents.forecast_links import forecast_links

HEALTH_HOUSES = (1, 6, 8, 12)


def health_links(chart: dict) -> dict:
    """House Links rows for the 1st, 6th, 8th and 12th at the current local moment."""
    links = forecast_links(chart, None, None)
    rows = [r for r in links["houses"] if r["house"] in HEALTH_HOUSES]
    by_status = {
        key: [h for h in houses if h in HEALTH_HOUSES]
        for key, houses in links["by_status"].items()
    }
    return {
        "as_of": links["as_of"],
        "transit_date": links["transit_date"],
        "transit_moment": links["transit_moment"],
        "period": links["period"],
        "by_status": by_status,
        "houses": rows,
        "planets": links["planets"],
    }


def dasha_moment(links: dict) -> datetime:
    """Noon of the House Links date, the moment House Links reads the dasha at."""
    d = datetime.fromisoformat(links["as_of"])
    return datetime(d.year, d.month, d.day, 12, 0)


def links_context(links: dict) -> str:
    lines = ["Health houses on House Links (D1, same status as Gochar and Forecast):"]
    for row in links["houses"]:
        parts = [row["status"]["en"]]
        reasons = [r.get("en") for r in row["dasha"]["reasons"] if r.get("en")]
        if reasons:
            parts.append("dasha: " + "; ".join(reasons[:2]))
        if row["transit"]["lines"]:
            parts.append("transit: " + "; ".join(ln["en"] for ln in row["transit"]["lines"]))
        lines.append(f"  H{row['house']} {row['theme_en']} — " + " · ".join(parts))
    return "\n".join(lines)
