"""
Promotion Effectiveness & Breakeven Analysis App

A Streamlit application for analyzing product promotion effectiveness
and calculating breakeven lift requirements.
"""
import streamlit as st
import pandas as pd

from calculations import (
    PromotionInputs,
    analyze_promotion,
    analyze_batch,
    results_to_dataframe
)
from data_handler import (
    parse_upload,
    validate_data,
    fill_defaults,
    get_sample_template,
    dataframe_to_csv,
    dataframe_to_excel
)
from visualizations import (
    create_breakeven_chart,
    create_sensitivity_chart,
    create_margin_comparison,
    create_scenario_table_data,
    create_batch_comparison_chart,
    create_margin_erosion_chart
)

# Page configuration
st.set_page_config(
    page_title="Promotion Effectiveness Analyzer",
    page_icon="📊",
    layout="wide"
)

st.title("Promotion Effectiveness & Breakeven Analyzer")
st.markdown("Analyze your product promotions to understand required sales lift and profitability impact.")

# Sidebar for input method selection
st.sidebar.header("Analysis Mode")
analysis_mode = st.sidebar.radio(
    "Choose input method:",
    ["Manual Entry", "Batch Upload"],
    help="Manual entry for single product analysis, batch upload for multiple products"
)


def display_metrics(results):
    """Display key metrics in a card layout."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Breakeven Lift Required",
            value=f"{results.breakeven_lift_pct * 100:.1f}%" if results.breakeven_lift_pct != float('inf') else "N/A",
            help="Percentage increase in units needed to maintain baseline profit"
        )

    with col2:
        st.metric(
            label="Standard Margin",
            value=f"${results.standard_margin:.2f}",
            help="Profit per unit at standard price"
        )

    with col3:
        st.metric(
            label="Promo Margin",
            value=f"${results.promo_margin:.2f}",
            delta=f"-{results.margin_erosion_pct * 100:.1f}%",
            delta_color="inverse",
            help="Profit per unit at promotional price"
        )

    with col4:
        st.metric(
            label="Breakeven Units",
            value=f"{results.breakeven_units:,.0f}" if results.breakeven_units != float('inf') else "N/A",
            delta=f"+{(results.breakeven_units - results.baseline_units):,.0f}" if results.breakeven_units != float('inf') else None,
            delta_color="off",
            help="Number of units needed during promotion to breakeven"
        )


def display_results(results):
    """Display full analysis results with charts."""
    st.subheader("Key Metrics")
    display_metrics(results)

    st.divider()

    # Charts section
    st.subheader("Visual Analysis")

    tab1, tab2, tab3 = st.tabs(["Breakeven Curve", "Profit Sensitivity", "Margin Comparison"])

    with tab1:
        fig = create_breakeven_chart(results)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("The breakeven point shows where promo profit equals baseline profit.")

    with tab2:
        fig = create_sensitivity_chart(results)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Blue bars indicate scenarios that meet or exceed baseline profit.")

    with tab3:
        fig = create_margin_comparison(results)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Scenario table
    st.subheader("What-If Scenarios")
    scenario_data = create_scenario_table_data(results)
    scenario_df = pd.DataFrame(scenario_data)

    # Style the dataframe
    def highlight_status(row):
        if row['Status'] == 'Profitable':
            return ['background-color: #d4edda'] * len(row)
        else:
            return ['background-color: #f8d7da'] * len(row)

    styled_df = scenario_df.style.apply(highlight_status, axis=1)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    st.divider()

    # Export section
    st.subheader("Export Results")
    col1, col2 = st.columns(2)

    with col1:
        export_data = {
            'Metric': [
                'Product Name', 'Standard Price', 'Promo Price',
                'Total Variable Costs', 'Standard Margin', 'Promo Margin',
                'Margin Erosion %', 'Breakeven Lift %', 'Baseline Units',
                'Breakeven Units', 'Baseline Profit'
            ],
            'Value': [
                results.product_name,
                f"${results.standard_price:.2f}",
                f"${results.promo_price:.2f}",
                f"${results.total_variable_costs:.2f}",
                f"${results.standard_margin:.2f}",
                f"${results.promo_margin:.2f}",
                f"{results.margin_erosion_pct * 100:.1f}%",
                f"{results.breakeven_lift_pct * 100:.1f}%" if results.breakeven_lift_pct != float('inf') else "N/A",
                f"{results.baseline_units:,.0f}",
                f"{results.breakeven_units:,.0f}" if results.breakeven_units != float('inf') else "N/A",
                f"${results.baseline_profit:,.2f}"
            ]
        }
        export_df = pd.DataFrame(export_data)
        csv_data = dataframe_to_csv(export_df)
        st.download_button(
            label="Download Results (CSV)",
            data=csv_data,
            file_name=f"promotion_analysis_{results.product_name}.csv",
            mime="text/csv"
        )

    with col2:
        excel_data = dataframe_to_excel(export_df)
        st.download_button(
            label="Download Results (Excel)",
            data=excel_data,
            file_name=f"promotion_analysis_{results.product_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# Manual Entry Mode
if analysis_mode == "Manual Entry":
    st.header("Single Product Analysis")

    with st.form("manual_entry_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Product Information")
            product_name = st.text_input(
                "Product Name",
                value="My Product",
                help="Name or identifier for this product"
            )
            standard_price = st.number_input(
                "Standard Price ($)",
                min_value=0.01,
                value=100.00,
                step=0.01,
                help="Regular selling price before promotion"
            )
            promo_price = st.number_input(
                "Promotional Price ($)",
                min_value=0.01,
                value=80.00,
                step=0.01,
                help="Discounted price during promotion"
            )
            baseline_units = st.number_input(
                "Baseline Units",
                min_value=1,
                value=100,
                step=1,
                help="Expected units sold at standard price (for comparison)"
            )

        with col2:
            st.subheader("Variable Costs")
            cogs = st.number_input(
                "Cost of Goods Sold ($)",
                min_value=0.00,
                value=50.00,
                step=0.01,
                help="Direct cost to produce/acquire each unit"
            )
            logistics_cost = st.number_input(
                "Logistics/Supply Chain ($)",
                min_value=0.00,
                value=5.00,
                step=0.01,
                help="Shipping, warehousing, and distribution costs per unit"
            )
            other_costs = st.number_input(
                "Other Variable Costs ($)",
                min_value=0.00,
                value=0.00,
                step=0.01,
                help="Any additional per-unit costs"
            )
            promo_terms = st.text_input(
                "Promotional Terms",
                placeholder="e.g., 20% off for 2 weeks",
                help="Description of the promotion (optional)"
            )

        submitted = st.form_submit_button("Analyze Promotion", type="primary")

    if submitted:
        # Validate inputs
        if promo_price >= standard_price:
            st.error("Promotional price must be less than standard price.")
        elif cogs + logistics_cost + other_costs >= promo_price:
            st.error("Total variable costs exceed promotional price. This promotion would have negative margin.")
        else:
            inputs = PromotionInputs(
                product_name=product_name,
                standard_price=standard_price,
                promo_price=promo_price,
                cogs=cogs,
                logistics_cost=logistics_cost,
                other_variable_costs=other_costs,
                promo_terms=promo_terms,
                baseline_units=baseline_units
            )
            results = analyze_promotion(inputs)
            display_results(results)


# Batch Upload Mode
else:
    st.header("Batch Analysis")

    # Template download
    st.subheader("Step 1: Download Template")
    template_df = get_sample_template()

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Download CSV Template",
            data=dataframe_to_csv(template_df),
            file_name="promotion_template.csv",
            mime="text/csv"
        )
    with col2:
        st.download_button(
            label="Download Excel Template",
            data=dataframe_to_excel(template_df),
            file_name="promotion_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.caption("Download the template, fill in your data, and upload below.")

    st.divider()

    # File upload
    st.subheader("Step 2: Upload Your Data")
    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload a file with columns: product_name, standard_price, promo_price, cogs (required), plus optional columns"
    )

    if uploaded_file is not None:
        # Parse file
        df, parse_error = parse_upload(uploaded_file)

        if parse_error:
            st.error(parse_error)
        else:
            # Show preview
            st.subheader("Data Preview")
            st.dataframe(df.head(), use_container_width=True)

            # Validate
            is_valid, errors = validate_data(df)

            if not is_valid:
                st.error("Validation errors found:")
                for error in errors:
                    st.error(f"- {error}")
            else:
                st.success(f"Data validated successfully! {len(df)} products found.")

                # Fill defaults and analyze
                df = fill_defaults(df)

                if st.button("Analyze All Products", type="primary"):
                    with st.spinner("Analyzing promotions..."):
                        results_list = analyze_batch(df)

                    st.divider()
                    st.subheader("Batch Results Summary")

                    # Summary table
                    summary_df = results_to_dataframe(results_list)
                    st.dataframe(summary_df, use_container_width=True, hide_index=True)

                    # Comparison charts
                    st.divider()
                    st.subheader("Comparative Analysis")

                    tab1, tab2 = st.tabs(["Breakeven Comparison", "Margin Erosion"])

                    with tab1:
                        fig = create_batch_comparison_chart(results_list)
                        st.plotly_chart(fig, use_container_width=True)
                        st.caption("Lower breakeven lift is better - promotions with <50% lift are typically achievable.")

                    with tab2:
                        fig = create_margin_erosion_chart(results_list)
                        st.plotly_chart(fig, use_container_width=True)

                    # Individual product drill-down
                    st.divider()
                    st.subheader("Individual Product Analysis")
                    selected_product = st.selectbox(
                        "Select a product for detailed analysis:",
                        options=[r.product_name for r in results_list]
                    )

                    if selected_product:
                        selected_results = next(r for r in results_list if r.product_name == selected_product)
                        display_results(selected_results)

                    # Batch export
                    st.divider()
                    st.subheader("Export Batch Results")
                    col1, col2 = st.columns(2)

                    with col1:
                        csv_data = dataframe_to_csv(summary_df)
                        st.download_button(
                            label="Download All Results (CSV)",
                            data=csv_data,
                            file_name="batch_promotion_analysis.csv",
                            mime="text/csv"
                        )

                    with col2:
                        excel_data = dataframe_to_excel(summary_df)
                        st.download_button(
                            label="Download All Results (Excel)",
                            data=excel_data,
                            file_name="batch_promotion_analysis.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )


# Footer
st.divider()
st.markdown("""
---
**How to interpret results:**
- **Breakeven Lift %**: The percentage increase in units you need to sell during the promotion to maintain the same total profit as standard pricing.
  - Example: 100% lift means you need to sell double the units.
- **Margin Erosion**: How much profit per unit you lose by offering the promotional price.
- **Scenarios**: The what-if table shows profit outcomes at various lift levels.

**Rule of thumb**: Promotions requiring >100% lift are challenging to achieve profitably.
""")
