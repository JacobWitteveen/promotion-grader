"""
Visualization functions for promotion analysis charts using Plotly.
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from calculations import PromotionResults


def create_breakeven_chart(results: PromotionResults) -> go.Figure:
    """
    Create a breakeven curve showing profit vs units for standard and promo pricing.

    Args:
        results: PromotionResults from analysis

    Returns:
        Plotly Figure
    """
    # Generate range of units from 0 to 2.5x baseline
    max_units = results.baseline_units * 2.5
    units = list(range(0, int(max_units) + 1, max(1, int(max_units // 50))))

    standard_profits = [u * results.standard_margin for u in units]
    promo_profits = [u * results.promo_margin for u in units]

    fig = go.Figure()

    # Standard pricing line
    fig.add_trace(go.Scatter(
        x=units,
        y=standard_profits,
        mode='lines',
        name='Standard Pricing',
        line=dict(color='#2E86AB', width=3)
    ))

    # Promo pricing line
    fig.add_trace(go.Scatter(
        x=units,
        y=promo_profits,
        mode='lines',
        name='Promo Pricing',
        line=dict(color='#E94F37', width=3)
    ))

    # Baseline units marker
    fig.add_trace(go.Scatter(
        x=[results.baseline_units],
        y=[results.baseline_profit],
        mode='markers',
        name='Baseline (Standard)',
        marker=dict(color='#2E86AB', size=12, symbol='circle')
    ))

    # Breakeven point marker
    if results.breakeven_units != float('inf'):
        breakeven_profit = results.breakeven_units * results.promo_margin
        fig.add_trace(go.Scatter(
            x=[results.breakeven_units],
            y=[breakeven_profit],
            mode='markers',
            name='Breakeven Point',
            marker=dict(color='#F18F01', size=14, symbol='star')
        ))

        # Add vertical line at breakeven
        fig.add_vline(
            x=results.breakeven_units,
            line_dash="dash",
            line_color="#F18F01",
            opacity=0.5
        )

    # Add horizontal line at baseline profit
    fig.add_hline(
        y=results.baseline_profit,
        line_dash="dot",
        line_color="gray",
        opacity=0.5,
        annotation_text="Baseline Profit"
    )

    fig.update_layout(
        title="Breakeven Analysis: Units vs Profit",
        xaxis_title="Units Sold",
        yaxis_title="Total Profit ($)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        template="plotly_white"
    )

    return fig


def create_sensitivity_chart(results: PromotionResults) -> go.Figure:
    """
    Create a sensitivity chart showing profit at different lift levels.

    Args:
        results: PromotionResults from analysis

    Returns:
        Plotly Figure
    """
    scenarios = results.scenarios

    lifts = [s['lift_pct'] * 100 for s in scenarios.values()]
    profits = [s['total_profit'] for s in scenarios.values()]
    profit_vs_baseline = [s['profit_vs_baseline'] for s in scenarios.values()]
    colors = ['#2E86AB' if s['profitable'] else '#E94F37' for s in scenarios.values()]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=lifts,
        y=profits,
        marker_color=colors,
        text=[f"${p:,.0f}" for p in profits],
        textposition='outside',
        name='Profit'
    ))

    # Add baseline profit reference line
    fig.add_hline(
        y=results.baseline_profit,
        line_dash="dash",
        line_color="#2E86AB",
        annotation_text=f"Baseline: ${results.baseline_profit:,.0f}"
    )

    # Add breakeven lift indicator
    if results.breakeven_lift_pct != float('inf'):
        fig.add_vline(
            x=results.breakeven_lift_pct * 100,
            line_dash="dash",
            line_color="#F18F01",
            annotation_text=f"Breakeven: {results.breakeven_lift_pct * 100:.0f}%"
        )

    fig.update_layout(
        title="Profit Sensitivity by Sales Lift",
        xaxis_title="Sales Lift (%)",
        yaxis_title="Total Profit ($)",
        template="plotly_white",
        showlegend=False
    )

    return fig


def create_margin_comparison(results: PromotionResults) -> go.Figure:
    """
    Create a bar chart comparing standard vs promo margins.

    Args:
        results: PromotionResults from analysis

    Returns:
        Plotly Figure
    """
    categories = ['Standard', 'Promo']
    margins = [results.standard_margin, results.promo_margin]
    colors = ['#2E86AB', '#E94F37']

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=categories,
        y=margins,
        marker_color=colors,
        text=[f"${m:.2f}" for m in margins],
        textposition='outside'
    ))

    # Add annotation for erosion
    erosion_text = f"Margin Erosion: {results.margin_erosion_pct * 100:.1f}%"
    fig.add_annotation(
        x=0.5,
        y=max(margins) * 1.15,
        text=erosion_text,
        showarrow=False,
        font=dict(size=14, color='#E94F37')
    )

    fig.update_layout(
        title="Per-Unit Margin Comparison",
        xaxis_title="Pricing",
        yaxis_title="Margin per Unit ($)",
        template="plotly_white",
        showlegend=False
    )

    return fig


def create_scenario_table_data(results: PromotionResults) -> list[dict]:
    """
    Generate data for the what-if scenario table.

    Args:
        results: PromotionResults from analysis

    Returns:
        List of dictionaries for table display
    """
    table_data = []

    for lift_pct, scenario in results.scenarios.items():
        table_data.append({
            'Lift %': f"{scenario['lift_pct'] * 100:.0f}%",
            'Units Sold': f"{scenario['units_sold']:,.0f}",
            'Total Profit': f"${scenario['total_profit']:,.2f}",
            'vs Baseline': f"${scenario['profit_vs_baseline']:+,.2f}",
            'Status': 'Profitable' if scenario['profitable'] else 'Below Baseline'
        })

    return table_data


def create_batch_comparison_chart(results_list: list[PromotionResults]) -> go.Figure:
    """
    Create a comparison chart for batch analysis showing breakeven lift by product.

    Args:
        results_list: List of PromotionResults

    Returns:
        Plotly Figure
    """
    products = [r.product_name for r in results_list]
    breakeven_lifts = [
        r.breakeven_lift_pct * 100 if r.breakeven_lift_pct != float('inf') else None
        for r in results_list
    ]

    # Color based on lift requirement (lower is better)
    colors = []
    for lift in breakeven_lifts:
        if lift is None:
            colors.append('#999999')  # Gray for impossible
        elif lift <= 50:
            colors.append('#2E86AB')  # Blue for good
        elif lift <= 100:
            colors.append('#F18F01')  # Orange for moderate
        else:
            colors.append('#E94F37')  # Red for challenging

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=products,
        y=breakeven_lifts,
        marker_color=colors,
        text=[f"{l:.0f}%" if l else "N/A" for l in breakeven_lifts],
        textposition='outside'
    ))

    # Add reference lines
    fig.add_hline(y=50, line_dash="dot", line_color="#2E86AB",
                  annotation_text="50% (Achievable)")
    fig.add_hline(y=100, line_dash="dot", line_color="#F18F01",
                  annotation_text="100% (Challenging)")

    fig.update_layout(
        title="Breakeven Lift Required by Product",
        xaxis_title="Product",
        yaxis_title="Required Lift (%)",
        template="plotly_white",
        showlegend=False
    )

    return fig


def create_margin_erosion_chart(results_list: list[PromotionResults]) -> go.Figure:
    """
    Create a chart showing margin erosion across products.

    Args:
        results_list: List of PromotionResults

    Returns:
        Plotly Figure
    """
    products = [r.product_name for r in results_list]
    erosions = [r.margin_erosion_pct * 100 for r in results_list]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=products,
        y=erosions,
        marker_color='#E94F37',
        text=[f"{e:.1f}%" for e in erosions],
        textposition='outside'
    ))

    fig.update_layout(
        title="Margin Erosion by Product",
        xaxis_title="Product",
        yaxis_title="Margin Erosion (%)",
        template="plotly_white",
        showlegend=False
    )

    return fig
