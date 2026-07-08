#!/usr/bin/env python3
"""Cost projector for seat-based, usage-based, and hybrid SaaS pricing.

Takes a customer's prior usage over an observation window and projects their
cost under the pricing model you pick (seat / usage / hybrid) across run-rate
horizons (window actual + monthly / quarterly / annual), with optional seat
scaling and a price x usage sensitivity grid.

Stdlib only (no third-party deps), so it runs anywhere with Python 3.

Models (see knowledge/platform_credits.md for sourcing and formulas):
    seat:   monthly = seats * seat_price
    usage:  monthly = monthly_units * unit_price     # or /1000 * price_per_1k_units
    hybrid: monthly = seats * seat_price
                    + max(0, monthly_units - seats*included_per_seat) * overage_price
where monthly_units is the observed usage scaled to a 30-day month.

Rate configuration (no values are hardcoded; supply your own):
    seat    -> SEAT_PRICE, SEATS, TARGET_SEATS
    usage   -> USAGE_UNIT_PRICE (or PRICE_PER_1K_UNITS), USAGE_UNIT_NAME
    hybrid  -> SEAT_PRICE, SEATS, INCLUDED_UNITS_PER_SEAT, OVERAGE_UNIT_PRICE
    grids   -> PRICE_GRID, USAGE_GRID (comma-separated; collapse to the base
               value when unset)
Each env var can be overridden per run with the matching CLI flag. Set these to
your negotiated rates; the script ships with no rate values.

Examples
--------
Seat-based (25 seats @ $30/seat/mo):
    python3 project_credits.py --pricing-model seat --seats 25 --seat-price 30

Usage-based from a 7-day window of 10,000 units @ $0.02/unit:
    python3 project_credits.py --pricing-model usage --usage 10000 \
        --window-days 7 --unit-price 0.02

Hybrid (bundled allowance + overage):
    python3 project_credits.py --pricing-model hybrid --usage 500000 \
        --window-days 30 --seats 25 --seat-price 30 \
        --included-per-seat 10000 --overage-price 0.01

Scale a 14-seat POC to 100 seats:
    python3 project_credits.py --pricing-model seat --seats 14 \
        --seat-price 30 --target-seats 100

Verify the model arithmetic against synthetic fixtures:
    python3 project_credits.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HORIZONS = [("Monthly", 30), ("Quarterly", 90), ("Annual", 365)]
MONTH_DAYS = 30.0


def _env_float(name: str):
    raw = os.environ.get(name)
    return float(raw) if raw else None


def _env_float_list(name: str):
    raw = os.environ.get(name)
    if not raw:
        return None
    values = [float(part) for part in raw.split(",") if part.strip()]
    return values or None


# Rate configuration (all optional; supplied via env or CLI). No rates ship in
# the repo, so every default below is None unless the environment sets it.
DEFAULT_SEAT_PRICE = _env_float("SEAT_PRICE")
DEFAULT_SEATS = _env_float("SEATS")
DEFAULT_TARGET_SEATS = _env_float("TARGET_SEATS")
DEFAULT_UNIT_PRICE = _env_float("USAGE_UNIT_PRICE")
DEFAULT_PRICE_PER_1K = _env_float("PRICE_PER_1K_UNITS")
DEFAULT_INCLUDED_PER_SEAT = _env_float("INCLUDED_UNITS_PER_SEAT")
DEFAULT_OVERAGE_PRICE = _env_float("OVERAGE_UNIT_PRICE")
DEFAULT_UNIT_NAME = os.environ.get("USAGE_UNIT_NAME") or "units"

# Sensitivity axes (comma-separated env vars). When unset, each grid collapses
# to the single configured base value, so nothing is hardcoded.
GRID_PRICES = _env_float_list("PRICE_GRID")
GRID_USAGE = _env_float_list("USAGE_GRID")


def scale(value: float, window_days: float, days: float) -> float:
    """Linear run-rate scaling from the observed window to `days`."""
    return value / window_days * days if window_days else 0.0


def unit_cost(units: float, unit_price, price_per_1k) -> float:
    """Cost of `units` at either a per-unit or per-1,000-unit price."""
    if unit_price is not None:
        return units * unit_price
    if price_per_1k is not None:
        return units / 1000.0 * price_per_1k
    return 0.0


def monthly_cost(model: str, monthly_units: float, seats: float, rates: dict) -> float:
    """Monthly cost for a model given monthly usage and seat count."""
    if model == "seat":
        return seats * (rates["seat_price"] or 0.0)
    if model == "usage":
        return unit_cost(monthly_units, rates["unit_price"], rates["price_per_1k"])
    if model == "hybrid":
        included = seats * (rates["included_per_seat"] or 0.0)
        overage = max(0.0, monthly_units - included)
        return seats * (rates["seat_price"] or 0.0) + overage * (rates["overage_price"] or 0.0)
    raise ValueError(f"unknown pricing model: {model}")


def horizon_rows(base_monthly: float, window_days: float) -> list:
    """Cost at the observed window plus monthly / quarterly / annual run-rates."""
    rows = [{
        "label": f"{window_days:g}-day actual",
        "days": window_days,
        "cost": base_monthly * window_days / MONTH_DAYS,
    }]
    for label, days in HORIZONS:
        rows.append({"label": label, "days": days, "cost": base_monthly * days / MONTH_DAYS})
    return rows


def build_report(args) -> dict:
    rates = {
        "seat_price": args.seat_price,
        "unit_price": args.unit_price,
        "price_per_1k": args.price_per_1k_units,
        "included_per_seat": args.included_per_seat,
        "overage_price": args.overage_price,
    }
    seats = args.seats or 0.0

    # Convert observed usage to billable units if a conversion ratio is given.
    raw_units = args.usage or 0.0
    billable_units = raw_units / args.conversion_ratio if args.conversion_ratio else raw_units
    monthly_units = scale(billable_units, args.window_days, MONTH_DAYS)

    base_monthly = monthly_cost(args.pricing_model, monthly_units, seats, rates)
    rows = horizon_rows(base_monthly, args.window_days)

    # Sensitivity grid. Price axis reprices the primary lever; volume axis is
    # usage (usage/hybrid) or seat count (seat). Collapses to base when unset.
    if args.pricing_model == "seat":
        price_axis = GRID_PRICES or [rates["seat_price"]]
        volume_axis = GRID_USAGE or [seats]
        grid = [
            {
                "price": p,
                "volume": v,
                "monthly_cost": monthly_cost("seat", 0.0, v or 0.0, {**rates, "seat_price": p}),
            }
            for p in price_axis for v in volume_axis
        ]
    else:
        base_price = rates["unit_price"] if rates["unit_price"] is not None else rates["price_per_1k"]
        price_axis = GRID_PRICES or [base_price]
        volume_axis = GRID_USAGE or [raw_units]
        grid = []
        for p in price_axis:
            for v in volume_axis:
                v_billable = v / args.conversion_ratio if args.conversion_ratio else v
                v_monthly = scale(v_billable or 0.0, args.window_days, MONTH_DAYS)
                if args.pricing_model == "usage":
                    gr = {**rates, "unit_price": p, "price_per_1k": None}
                else:  # hybrid: the grid price reprices the overage rate
                    gr = {**rates, "overage_price": p}
                grid.append({
                    "price": p,
                    "volume": v,
                    "monthly_cost": monthly_cost(args.pricing_model, v_monthly, seats, gr),
                })

    report = {
        "inputs": {
            "pricing_model": args.pricing_model,
            "window_days": args.window_days,
            "usage_units": raw_units,
            "billable_units": billable_units,
            "conversion_ratio": args.conversion_ratio,
            "seats": seats,
            "unit_name": args.unit_name,
            "rates": rates,
        },
        "monthly_cost": base_monthly,
        "annual_cost": base_monthly * 12.0,
        "horizons": rows,
        "grid": grid,
        "self_hosted": bool(args.self_hosted),
    }

    # Optional seat scaling: recompute at the target seat count.
    if args.target_seats and seats:
        factor = args.target_seats / seats
        if args.pricing_model == "usage":
            scaled_monthly = base_monthly * factor  # usage assumed to scale with headcount
        else:
            scaled_units = monthly_units * factor
            scaled_monthly = monthly_cost(args.pricing_model, scaled_units, args.target_seats, rates)
        report["seat_projection"] = {
            "from_seats": seats,
            "target_seats": args.target_seats,
            "monthly_cost": scaled_monthly,
            "annual_cost": scaled_monthly * 12.0,
        }

    return report


def fmt_money(v: float) -> str:
    return f"${v:,.2f}"


def render_text(report: dict) -> str:
    i = report["inputs"]
    model = i["pricing_model"]
    lines: list[str] = []
    lines.append(f"COST PROJECTION - {model} pricing")
    if model == "seat":
        lines.append(f"{i['seats']:g} seats @ {fmt_money(i['rates']['seat_price'] or 0.0)}/seat/mo")
    elif model == "usage":
        price = i["rates"]["unit_price"]
        if price is not None:
            price_str = f"{fmt_money(price)}/{i['unit_name']}"
        else:
            price_str = f"{fmt_money(i['rates']['price_per_1k'] or 0.0)}/1K {i['unit_name']}"
        conv = f" (conv ratio {i['conversion_ratio']:g})" if i["conversion_ratio"] else ""
        lines.append(
            f"{i['usage_units']:,.0f} {i['unit_name']} / {i['window_days']:g} days{conv} @ {price_str}"
        )
    else:  # hybrid
        r = i["rates"]
        lines.append(
            f"{i['usage_units']:,.0f} {i['unit_name']} / {i['window_days']:g} days | "
            f"{i['seats']:g} seats @ {fmt_money(r['seat_price'] or 0.0)}/seat + "
            f"overage {fmt_money(r['overage_price'] or 0.0)}/{i['unit_name']} "
            f"over {r['included_per_seat'] or 0:g}/seat"
        )
    lines.append(
        f"-> monthly run-rate: {fmt_money(report['monthly_cost'])}/mo "
        f"({fmt_money(report['annual_cost'])}/yr)"
    )
    lines.append("")

    lab_w, col_w = 18, 16
    lines.append("Horizon".ljust(lab_w) + "Cost".rjust(col_w))
    lines.append("-" * (lab_w + col_w))
    for row in report["horizons"]:
        lines.append(row["label"].ljust(lab_w) + fmt_money(row["cost"]).rjust(col_w))

    if len(report["grid"]) > 1:
        lines.append("")
        lines.append("Sensitivity (monthly cost by price x volume):")
        for cell in report["grid"]:
            price = cell["price"] if cell["price"] is not None else 0.0
            lines.append(
                f"  price {price:g} x volume {cell['volume'] or 0:,.0f}"
                f" -> {fmt_money(cell['monthly_cost'])}/mo"
            )

    if "seat_projection" in report:
        s = report["seat_projection"]
        lines.append("")
        lines.append(
            f"Seats {s['from_seats']:g}->{s['target_seats']:g}: "
            f"{fmt_money(s['monthly_cost'])}/mo ({fmt_money(s['annual_cost'])}/yr)"
        )

    if report["self_hosted"]:
        lines.append("")
        lines.append(
            "Self-hosted / BYOC: customer supplies compute, so billed "
            "infrastructure = $0. Figures above are the avoided cost."
        )

    lines.append("")
    lines.append("Directional; usage-derived costs carry ~+/-30-50% without full history.")
    lines.append("Full detail: re-run with --json.")
    return "\n".join(lines)


def run_self_test() -> int:
    """Assert the model arithmetic holds for synthetic fixtures.

    The rates below are arbitrary test values (not real pricing), chosen to make
    the expected outputs easy to verify by hand.
    """
    def mk(**kw):
        base = dict(
            pricing_model="seat", usage=0.0, window_days=7.0, seats=0.0,
            target_seats=0.0, seat_price=None, unit_price=None,
            price_per_1k_units=None, included_per_seat=None, overage_price=None,
            conversion_ratio=None, unit_name="units", self_hosted=False,
        )
        base.update(kw)
        return argparse.Namespace(**base)

    checks = []
    # Seat: 10 seats @ $30 -> $300/mo, $3,600/yr.
    r = build_report(mk(pricing_model="seat", seats=10.0, seat_price=30.0))
    checks.append(("seat monthly", r["monthly_cost"], 300.0, 0.01))
    checks.append(("seat annual", r["annual_cost"], 3600.0, 0.01))
    # Usage: 10,000 units / 7 days @ $0.02 -> 10000*30/7*0.02.
    r = build_report(mk(pricing_model="usage", usage=10000.0, window_days=7.0, unit_price=0.02))
    checks.append(("usage monthly", r["monthly_cost"], 10000.0 * 30.0 / 7.0 * 0.02, 0.01))
    # Hybrid: 500k units/30d, 25 seats @ $30, incl 10k/seat, overage $0.01 ->
    #   included=250k, overage=250k -> 25*30 + 250000*0.01 = 3250.
    r = build_report(mk(pricing_model="hybrid", usage=500000.0, window_days=30.0,
                        seats=25.0, seat_price=30.0, included_per_seat=10000.0,
                        overage_price=0.01))
    checks.append(("hybrid monthly", r["monthly_cost"], 3250.0, 0.01))

    ok = True
    for name, got, want, tol in checks:
        passed = abs(got - want) <= tol
        ok = ok and passed
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}: got {got:.4f}, want ~{want:.4f}")
    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Project a customer's cost across seat, usage, and hybrid pricing models."
    )
    p.add_argument("--pricing-model", choices=["seat", "usage", "hybrid"],
                   help="Which pricing model to project.")
    p.add_argument("--usage", type=float, default=None,
                   help="Observed usage units over the window (usage/hybrid models).")
    p.add_argument("--window-days", type=float, default=7.0,
                   help="Length of the observation window in days (default 7).")
    p.add_argument("--seats", type=float, default=DEFAULT_SEATS,
                   help="Seat count (seat/hybrid). Falls back to the SEATS env var.")
    p.add_argument("--target-seats", type=float, default=DEFAULT_TARGET_SEATS or 0.0,
                   help="Target seat count for a scaling projection (or TARGET_SEATS env var).")
    p.add_argument("--seat-price", type=float, default=DEFAULT_SEAT_PRICE,
                   help="Price per seat per month (or SEAT_PRICE env var).")
    p.add_argument("--unit-price", type=float, default=DEFAULT_UNIT_PRICE,
                   help="Price per usage unit (or USAGE_UNIT_PRICE env var).")
    p.add_argument("--price-per-1k-units", type=float, default=DEFAULT_PRICE_PER_1K,
                   help="Price per 1,000 units, alternative to --unit-price (or PRICE_PER_1K_UNITS env var).")
    p.add_argument("--included-per-seat", type=float, default=DEFAULT_INCLUDED_PER_SEAT,
                   help="Units bundled per seat before overage, hybrid model (or INCLUDED_UNITS_PER_SEAT env var).")
    p.add_argument("--overage-price", type=float, default=DEFAULT_OVERAGE_PRICE,
                   help="Price per unit above the included allowance, hybrid model (or OVERAGE_UNIT_PRICE env var).")
    p.add_argument("--conversion-ratio", type=float, default=None,
                   help="Optional raw-usage-per-billable-unit ratio; billable = usage / ratio.")
    p.add_argument("--unit-name", default=DEFAULT_UNIT_NAME,
                   help="Human-readable unit name for output (or USAGE_UNIT_NAME env var).")
    p.add_argument("--self-hosted", action="store_true",
                   help="Note the customer self-hosts / BYOC (billed compute = $0).")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of a text report.")
    p.add_argument("--self-test", action="store_true",
                   help="Verify the model arithmetic against synthetic fixtures and exit.")
    return p.parse_args(argv)


def _require(cond, msg):
    if not cond:
        print(f"error: {msg}", file=sys.stderr)
        raise SystemExit(2)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.self_test:
        return run_self_test()

    _require(args.pricing_model,
             "--pricing-model is required (seat | usage | hybrid), or use --self-test")
    _require(args.window_days > 0, "--window-days must be > 0")

    if args.pricing_model == "seat":
        _require(args.seats and args.seats > 0,
                 "--seats is required for seat pricing (or set SEATS)")
        _require(args.seat_price is not None,
                 "--seat-price is required for seat pricing (or set SEAT_PRICE)")
    elif args.pricing_model == "usage":
        _require(args.usage is not None, "--usage is required for usage pricing")
        _require(args.unit_price is not None or args.price_per_1k_units is not None,
                 "--unit-price or --price-per-1k-units is required "
                 "(or set USAGE_UNIT_PRICE / PRICE_PER_1K_UNITS)")
    else:  # hybrid
        _require(args.usage is not None, "--usage is required for hybrid pricing")
        _require(args.seats and args.seats > 0,
                 "--seats is required for hybrid pricing (or set SEATS)")
        _require(args.seat_price is not None,
                 "--seat-price is required for hybrid pricing (or set SEAT_PRICE)")
        _require(args.included_per_seat is not None,
                 "--included-per-seat is required for hybrid pricing (or set INCLUDED_UNITS_PER_SEAT)")
        _require(args.overage_price is not None,
                 "--overage-price is required for hybrid pricing (or set OVERAGE_UNIT_PRICE)")

    if args.conversion_ratio is not None:
        _require(args.conversion_ratio > 0, "--conversion-ratio must be > 0")

    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
