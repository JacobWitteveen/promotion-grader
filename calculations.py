"""
Core business logic for promotion effectiveness and breakeven analysis.
"""
from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass
class PromotionInputs:
    """Input data for a single promotion analysis."""
    product_name: str
    standard_price: float
    promo_price: float
    cogs: float
    logistics_cost: float = 0.0
    other_variable_costs: float = 0.0
    promo_terms: str = ""
    baseline_units: float = 100.0


@dataclass
class PromotionResults:
    """Results from promotion analysis."""
    product_name: str
    standard_price: float
    promo_price: float
    total_variable_costs: float
    standard_margin: float
    promo_margin: float
    margin_erosion_pct: float
    breakeven_lift_pct: float
    breakeven_units: float
    baseline_units: float
    baseline_profit: float
    scenarios: dict


def calculate_margin(price: float, cogs: float, logistics: float = 0.0,
                     other_costs: float = 0.0) -> float:
    """
    Calculate per-unit margin.

    Args:
        price: Selling price per unit
        cogs: Cost of goods sold per unit
        logistics: Logistics/supply chain cost per unit
        other_costs: Any other variable costs per unit

    Returns:
        Per-unit margin (profit)
    """
    total_costs = cogs + logistics + other_costs
    return price - total_costs


def calculate_breakeven_lift(standard_margin: float, promo_margin: float) -> Optional[float]:
    """
    Calculate the required lift percentage to breakeven on profit.

    Formula: (Standard Margin / Promo Margin) - 1

    Args:
        standard_margin: Margin at standard price
        promo_margin: Margin at promotional price

    Returns:
        Required lift as a decimal (e.g., 1.0 = 100% lift),
        or None if promo margin is zero/negative
    """
    if promo_margin <= 0:
        return None  # Cannot breakeven with zero or negative margin

    return (standard_margin / promo_margin) - 1


def calculate_breakeven_units(baseline_units: float, breakeven_lift: float) -> float:
    """
    Calculate the number of units needed to breakeven.

    Args:
        baseline_units: Expected units at standard price
        breakeven_lift: Required lift as decimal

    Returns:
        Number of units needed during promotion
    """
    return baseline_units * (1 + breakeven_lift)


def calculate_profit_at_lift(baseline_units: float, promo_margin: float,
                             lift_pct: float) -> float:
    """
    Calculate total profit at a given lift percentage.

    Args:
        baseline_units: Expected units at standard price
        promo_margin: Per-unit margin during promotion
        lift_pct: Sales lift as decimal (e.g., 0.5 = 50% lift)

    Returns:
        Total profit at the given lift level
    """
    units_sold = baseline_units * (1 + lift_pct)
    return units_sold * promo_margin


def calculate_margin_erosion(standard_margin: float, promo_margin: float) -> float:
    """
    Calculate the percentage margin erosion from standard to promo.

    Args:
        standard_margin: Margin at standard price
        promo_margin: Margin at promotional price

    Returns:
        Margin erosion as a decimal (e.g., 0.25 = 25% erosion)
    """
    if standard_margin == 0:
        return 0.0
    return (standard_margin - promo_margin) / standard_margin


def generate_scenario_analysis(inputs: PromotionInputs) -> dict:
    """
    Generate profit scenarios at various lift levels.

    Args:
        inputs: PromotionInputs dataclass

    Returns:
        Dictionary with lift percentages as keys and profit values
    """
    total_costs = inputs.cogs + inputs.logistics_cost + inputs.other_variable_costs
    promo_margin = inputs.promo_price - total_costs
    standard_margin = inputs.standard_price - total_costs
    baseline_profit = inputs.baseline_units * standard_margin

    lift_levels = [0, 0.25, 0.50, 0.75, 1.0, 1.25, 1.50, 2.0]
    scenarios = {}

    for lift in lift_levels:
        profit = calculate_profit_at_lift(inputs.baseline_units, promo_margin, lift)
        profit_vs_baseline = profit - baseline_profit
        scenarios[lift] = {
            'lift_pct': lift,
            'units_sold': inputs.baseline_units * (1 + lift),
            'total_profit': profit,
            'profit_vs_baseline': profit_vs_baseline,
            'profitable': profit >= baseline_profit
        }

    return scenarios


def analyze_promotion(inputs: PromotionInputs) -> PromotionResults:
    """
    Perform full promotion analysis.

    Args:
        inputs: PromotionInputs dataclass

    Returns:
        PromotionResults with all calculated metrics
    """
    total_costs = inputs.cogs + inputs.logistics_cost + inputs.other_variable_costs
    standard_margin = calculate_margin(inputs.standard_price, inputs.cogs,
                                       inputs.logistics_cost, inputs.other_variable_costs)
    promo_margin = calculate_margin(inputs.promo_price, inputs.cogs,
                                    inputs.logistics_cost, inputs.other_variable_costs)

    margin_erosion = calculate_margin_erosion(standard_margin, promo_margin)
    breakeven_lift = calculate_breakeven_lift(standard_margin, promo_margin)

    if breakeven_lift is not None:
        breakeven_units = calculate_breakeven_units(inputs.baseline_units, breakeven_lift)
    else:
        breakeven_units = float('inf')

    baseline_profit = inputs.baseline_units * standard_margin
    scenarios = generate_scenario_analysis(inputs)

    return PromotionResults(
        product_name=inputs.product_name,
        standard_price=inputs.standard_price,
        promo_price=inputs.promo_price,
        total_variable_costs=total_costs,
        standard_margin=standard_margin,
        promo_margin=promo_margin,
        margin_erosion_pct=margin_erosion,
        breakeven_lift_pct=breakeven_lift if breakeven_lift else float('inf'),
        breakeven_units=breakeven_units,
        baseline_units=inputs.baseline_units,
        baseline_profit=baseline_profit,
        scenarios=scenarios
    )


def analyze_batch(df: pd.DataFrame) -> list[PromotionResults]:
    """
    Analyze multiple promotions from a DataFrame.

    Expected columns:
        - product_name
        - standard_price
        - promo_price
        - cogs
        - logistics_cost (optional)
        - other_variable_costs (optional)
        - promo_terms (optional)
        - baseline_units (optional, defaults to 100)

    Args:
        df: DataFrame with promotion data

    Returns:
        List of PromotionResults
    """
    results = []

    for _, row in df.iterrows():
        inputs = PromotionInputs(
            product_name=str(row.get('product_name', 'Unknown')),
            standard_price=float(row['standard_price']),
            promo_price=float(row['promo_price']),
            cogs=float(row['cogs']),
            logistics_cost=float(row.get('logistics_cost', 0)),
            other_variable_costs=float(row.get('other_variable_costs', 0)),
            promo_terms=str(row.get('promo_terms', '')),
            baseline_units=float(row.get('baseline_units', 100))
        )
        results.append(analyze_promotion(inputs))

    return results


def results_to_dataframe(results: list[PromotionResults]) -> pd.DataFrame:
    """
    Convert list of results to a summary DataFrame.

    Args:
        results: List of PromotionResults

    Returns:
        Summary DataFrame
    """
    data = []
    for r in results:
        data.append({
            'Product': r.product_name,
            'Standard Price': r.standard_price,
            'Promo Price': r.promo_price,
            'Standard Margin': r.standard_margin,
            'Promo Margin': r.promo_margin,
            'Margin Erosion %': r.margin_erosion_pct * 100,
            'Breakeven Lift %': r.breakeven_lift_pct * 100 if r.breakeven_lift_pct != float('inf') else None,
            'Baseline Units': r.baseline_units,
            'Breakeven Units': r.breakeven_units if r.breakeven_units != float('inf') else None,
            'Baseline Profit': r.baseline_profit
        })

    return pd.DataFrame(data)
