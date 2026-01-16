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
    promo_cost_per_unit: float = 0.0  # Additional per-unit cost during promotion (e.g., retailer subsidies)
    baseline_units: float = 100.0


@dataclass
class WeeklyData:
    """Weekly baseline and actual units data."""
    week_number: int
    baseline_units: float
    actual_units: float


@dataclass
class HistoricalInputs:
    """Input data for historical promotion grading."""
    product_name: str
    standard_price: float
    promo_price: float
    cogs: float
    logistics_cost: float = 0.0
    other_variable_costs: float = 0.0
    promo_cost_per_unit: float = 0.0  # Additional per-unit cost during promotion (e.g., retailer subsidies)
    weekly_data: list = None  # list[WeeklyData]


@dataclass
class WeeklyGrade:
    """Grading results for a single week."""
    week_number: int
    baseline_units: float
    actual_units: float
    actual_lift_pct: float
    breakeven_lift_pct: float
    lift_vs_breakeven: float  # positive = exceeded, negative = fell short
    actual_profit: float
    baseline_profit: float
    profit_vs_baseline: float
    grade_score: float  # 0-100 scale
    passed: bool


@dataclass
class HistoricalResults:
    """Full results from historical promotion grading."""
    # Promo details
    product_name: str
    standard_margin: float
    promo_margin: float
    breakeven_lift_pct: float

    # Weekly breakdown
    weekly_grades: list  # list[WeeklyGrade]

    # Cumulative totals
    total_baseline_units: float
    total_actual_units: float
    total_baseline_profit: float
    total_actual_profit: float
    overall_lift_pct: float
    overall_profit_vs_baseline: float
    overall_grade_score: float
    overall_passed: bool


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
    promo_total_costs = total_costs + inputs.promo_cost_per_unit
    promo_margin = inputs.promo_price - promo_total_costs
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
    # Promo margin includes additional promo-specific costs (e.g., retailer subsidies)
    promo_margin = calculate_margin(inputs.promo_price, inputs.cogs,
                                    inputs.logistics_cost,
                                    inputs.other_variable_costs + inputs.promo_cost_per_unit)

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
            promo_cost_per_unit=float(row.get('promo_cost_per_unit', 0)),
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


# ============================================================================
# Historical Promotion Grading Functions
# ============================================================================

def calculate_grade_score(actual_lift: float, breakeven_lift: float) -> float:
    """
    Calculate 0-100 score based on how actual lift compares to breakeven.

    Args:
        actual_lift: Actual lift achieved as decimal (e.g., 0.5 = 50%)
        breakeven_lift: Required breakeven lift as decimal

    Returns:
        Score from 0-100 (capped at 100)
    """
    if breakeven_lift <= 0:
        return 100.0 if actual_lift >= 0 else 0.0

    score = (actual_lift / breakeven_lift) * 100
    return min(100.0, max(0.0, score))


def get_grade_color(score: float) -> str:
    """
    Get color based on grade score.

    Args:
        score: Grade score 0-100

    Returns:
        Color string for visualization
    """
    if score >= 100:
        return '#2E86AB'  # Blue - exceeded
    elif score >= 75:
        return '#4CAF50'  # Green - good
    elif score >= 50:
        return '#F18F01'  # Orange - moderate
    else:
        return '#E94F37'  # Red - poor


def calculate_weekly_grade(week: WeeklyData, standard_margin: float,
                           promo_margin: float, breakeven_lift: float) -> WeeklyGrade:
    """
    Grade a single week's performance against breakeven.

    Args:
        week: WeeklyData with baseline and actual units
        standard_margin: Per-unit margin at standard price
        promo_margin: Per-unit margin at promo price
        breakeven_lift: Required lift to breakeven as decimal

    Returns:
        WeeklyGrade with all calculated metrics
    """
    # Calculate actual lift
    if week.baseline_units > 0:
        actual_lift = (week.actual_units - week.baseline_units) / week.baseline_units
    else:
        actual_lift = 0.0

    # Calculate profits
    baseline_profit = week.baseline_units * standard_margin
    actual_profit = week.actual_units * promo_margin

    # Calculate grade
    grade_score = calculate_grade_score(actual_lift, breakeven_lift)
    passed = actual_lift >= breakeven_lift

    return WeeklyGrade(
        week_number=week.week_number,
        baseline_units=week.baseline_units,
        actual_units=week.actual_units,
        actual_lift_pct=actual_lift,
        breakeven_lift_pct=breakeven_lift,
        lift_vs_breakeven=actual_lift - breakeven_lift,
        actual_profit=actual_profit,
        baseline_profit=baseline_profit,
        profit_vs_baseline=actual_profit - baseline_profit,
        grade_score=grade_score,
        passed=passed
    )


def analyze_historical(inputs: HistoricalInputs) -> HistoricalResults:
    """
    Perform full historical promotion analysis with grading.

    Args:
        inputs: HistoricalInputs with promo details and weekly data

    Returns:
        HistoricalResults with weekly grades and cumulative totals
    """
    # Calculate margins
    total_costs = inputs.cogs + inputs.logistics_cost + inputs.other_variable_costs
    promo_total_costs = total_costs + inputs.promo_cost_per_unit
    standard_margin = inputs.standard_price - total_costs
    promo_margin = inputs.promo_price - promo_total_costs

    # Calculate breakeven lift
    if promo_margin > 0:
        breakeven_lift = (standard_margin / promo_margin) - 1
    else:
        breakeven_lift = float('inf')

    # Grade each week
    weekly_grades = []
    for week in inputs.weekly_data:
        grade = calculate_weekly_grade(week, standard_margin, promo_margin, breakeven_lift)
        weekly_grades.append(grade)

    # Calculate cumulative totals
    total_baseline_units = sum(w.baseline_units for w in inputs.weekly_data)
    total_actual_units = sum(w.actual_units for w in inputs.weekly_data)
    total_baseline_profit = sum(g.baseline_profit for g in weekly_grades)
    total_actual_profit = sum(g.actual_profit for g in weekly_grades)

    # Overall lift
    if total_baseline_units > 0:
        overall_lift = (total_actual_units - total_baseline_units) / total_baseline_units
    else:
        overall_lift = 0.0

    # Overall grade
    overall_grade_score = calculate_grade_score(overall_lift, breakeven_lift)
    overall_passed = overall_lift >= breakeven_lift

    return HistoricalResults(
        product_name=inputs.product_name,
        standard_margin=standard_margin,
        promo_margin=promo_margin,
        breakeven_lift_pct=breakeven_lift,
        weekly_grades=weekly_grades,
        total_baseline_units=total_baseline_units,
        total_actual_units=total_actual_units,
        total_baseline_profit=total_baseline_profit,
        total_actual_profit=total_actual_profit,
        overall_lift_pct=overall_lift,
        overall_profit_vs_baseline=total_actual_profit - total_baseline_profit,
        overall_grade_score=overall_grade_score,
        overall_passed=overall_passed
    )


def historical_results_to_dataframe(results: HistoricalResults) -> pd.DataFrame:
    """
    Convert weekly grades to a DataFrame for display.

    Args:
        results: HistoricalResults

    Returns:
        DataFrame with weekly breakdown
    """
    data = []
    for g in results.weekly_grades:
        data.append({
            'Week': g.week_number,
            'Baseline Units': g.baseline_units,
            'Actual Units': g.actual_units,
            'Actual Lift %': g.actual_lift_pct * 100,
            'Breakeven Lift %': g.breakeven_lift_pct * 100 if g.breakeven_lift_pct != float('inf') else None,
            'Baseline Profit': g.baseline_profit,
            'Actual Profit': g.actual_profit,
            'Profit vs Baseline': g.profit_vs_baseline,
            'Grade Score': g.grade_score,
            'Status': 'Pass' if g.passed else 'Fail'
        })

    return pd.DataFrame(data)
