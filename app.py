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
    results_to_dataframe,
    HistoricalInputs,
    WeeklyData,
    analyze_historical,
    historical_results_to_dataframe,
    get_grade_color
)
from data_handler import (
    parse_upload,
    validate_data,
    fill_defaults,
    get_sample_template,
    dataframe_to_csv,
    dataframe_to_excel,
    get_historical_template,
    validate_historical_data,
    parse_historical_data
)
from visualizations import (
    create_breakeven_chart,
    create_sensitivity_chart,
    create_margin_comparison,
    create_scenario_table_data,
    create_batch_comparison_chart,
    create_margin_erosion_chart,
    create_weekly_scorecard,
    create_cumulative_chart,
    create_profit_waterfall,
    create_historical_batch_comparison
)

# Page configuration
st.set_page_config(
    page_title="Promotion Effectiveness Analyzer",
    page_icon="📊",
    layout="wide"
)

st.title("Promotion Effectiveness & Breakeven Analyzer")
st.markdown("Analyze your product promotions to understand required sales lift and profitability impact.")

# Main page navigation
analysis_mode = st.radio(
    "Choose analysis type:",
    ["Promo Grader", "Historical Grading"],
    horizontal=True,
    help="Promo Grader for breakeven analysis, Historical Grading to grade past promotions"
)
st.divider()


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


# Promo Grader Mode
if analysis_mode == "Promo Grader":
    st.header("Promo Grader")

    # Sub-mode selection
    promo_mode = st.radio(
        "Choose input method:",
        ["Manual Entry", "Batch Upload"],
        horizontal=True
    )

    if promo_mode == "Manual Entry":
        st.subheader("Single Product Analysis")

        with st.form("manual_entry_form"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Product Information**")
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
                st.markdown("**Variable Costs**")
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
                promo_cost = st.number_input(
                    "Promo Cost per Unit ($)",
                    min_value=0.00,
                    value=0.00,
                    step=0.01,
                    help="Additional per-unit cost during promotion (e.g., retailer subsidies, placement fees)"
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
                    promo_cost_per_unit=promo_cost,
                    baseline_units=baseline_units
                )
                results = analyze_promotion(inputs)
                display_results(results)

    else:  # Batch Upload within Promo Grader
        st.subheader("Batch Analysis")

        # Template download
        st.markdown("**Step 1: Download Template**")
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


# Historical Grading Mode
elif analysis_mode == "Historical Grading":
    st.header("Historical Promotion Grading")
    st.markdown("Grade past promotions by comparing actual weekly performance against breakeven targets.")

    # Sub-mode selection
    historical_mode = st.radio(
        "Choose input method:",
        ["Manual Entry", "Batch Upload"],
        horizontal=True
    )

    if historical_mode == "Manual Entry":
        st.subheader("Promotion Details")

        with st.form("historical_manual_form"):
            col1, col2 = st.columns(2)

            with col1:
                product_name = st.text_input("Product Name", value="My Product")
                standard_price = st.number_input("Standard Price ($)", min_value=0.01, value=100.00, step=0.01)
                promo_price = st.number_input("Promotional Price ($)", min_value=0.01, value=80.00, step=0.01)

            with col2:
                cogs = st.number_input("Cost of Goods Sold ($)", min_value=0.00, value=50.00, step=0.01)
                logistics_cost = st.number_input("Logistics/Supply Chain ($)", min_value=0.00, value=5.00, step=0.01)
                other_costs = st.number_input("Other Variable Costs ($)", min_value=0.00, value=0.00, step=0.01)
                promo_cost = st.number_input(
                    "Promo Cost per Unit ($)",
                    min_value=0.00,
                    value=0.00,
                    step=0.01,
                    help="Additional per-unit cost during promotion (e.g., retailer subsidies)",
                    key="hist_promo_cost"
                )

            st.divider()
            st.subheader("Weekly Data")

            num_weeks = st.number_input("Number of Weeks", min_value=1, max_value=52, value=3, step=1)

            # Dynamic week inputs
            weekly_data_inputs = []
            cols = st.columns(3)

            for i in range(int(num_weeks)):
                col_idx = i % 3
                with cols[col_idx]:
                    st.markdown(f"**Week {i + 1}**")
                    baseline = st.number_input(
                        f"Baseline Units",
                        min_value=0,
                        value=100,
                        step=1,
                        key=f"baseline_{i}"
                    )
                    actual = st.number_input(
                        f"Actual Units",
                        min_value=0,
                        value=100,
                        step=1,
                        key=f"actual_{i}"
                    )
                    weekly_data_inputs.append((i + 1, baseline, actual))

            submitted = st.form_submit_button("Grade Promotion", type="primary")

        if submitted:
            # Validate inputs
            if promo_price >= standard_price:
                st.error("Promotional price must be less than standard price.")
            elif cogs + logistics_cost + other_costs >= promo_price:
                st.error("Total variable costs exceed promotional price.")
            else:
                # Build inputs
                weekly_data = [
                    WeeklyData(week_number=w[0], baseline_units=w[1], actual_units=w[2])
                    for w in weekly_data_inputs
                ]

                inputs = HistoricalInputs(
                    product_name=product_name,
                    standard_price=standard_price,
                    promo_price=promo_price,
                    cogs=cogs,
                    logistics_cost=logistics_cost,
                    other_variable_costs=other_costs,
                    promo_cost_per_unit=promo_cost,
                    weekly_data=weekly_data
                )

                results = analyze_historical(inputs)

                # Display results
                st.divider()

                # Overall result banner
                if results.overall_passed:
                    st.success(f"PASSED - Promotion met breakeven target! (Score: {results.overall_grade_score:.0f}%)")
                else:
                    st.error(f"FAILED - Promotion did not meet breakeven target (Score: {results.overall_grade_score:.0f}%)")

                # Summary metrics
                st.subheader("Summary Metrics")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Breakeven Lift Required",
                              f"{results.breakeven_lift_pct * 100:.1f}%" if results.breakeven_lift_pct != float('inf') else "N/A")
                with col2:
                    st.metric("Actual Overall Lift", f"{results.overall_lift_pct * 100:.1f}%")
                with col3:
                    st.metric("Total Actual Profit", f"${results.total_actual_profit:,.2f}")
                with col4:
                    delta_color = "normal" if results.overall_profit_vs_baseline >= 0 else "inverse"
                    st.metric("vs Baseline Profit",
                              f"${results.overall_profit_vs_baseline:+,.2f}",
                              delta=f"{(results.overall_profit_vs_baseline / results.total_baseline_profit * 100):+.1f}%" if results.total_baseline_profit else None,
                              delta_color=delta_color)

                st.divider()

                # Detailed analysis tabs
                st.subheader("Detailed Analysis")
                tab1, tab2, tab3, tab4 = st.tabs(["Weekly Scorecard", "Cumulative View", "Profit Analysis", "Data Table"])

                with tab1:
                    fig = create_weekly_scorecard(results)
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption("Bars show actual lift %. Vertical line = breakeven threshold. Colors indicate grade.")

                with tab2:
                    fig = create_cumulative_chart(results)
                    st.plotly_chart(fig, use_container_width=True)

                with tab3:
                    fig = create_profit_waterfall(results)
                    st.plotly_chart(fig, use_container_width=True)

                with tab4:
                    weekly_df = historical_results_to_dataframe(results)

                    def highlight_status(row):
                        if row['Status'] == 'Pass':
                            return ['background-color: #d4edda'] * len(row)
                        else:
                            return ['background-color: #f8d7da'] * len(row)

                    styled_df = weekly_df.style.apply(highlight_status, axis=1)
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)

                # Export
                st.divider()
                st.subheader("Export Results")
                col1, col2 = st.columns(2)

                with col1:
                    csv_data = dataframe_to_csv(weekly_df)
                    st.download_button(
                        label="Download Results (CSV)",
                        data=csv_data,
                        file_name=f"historical_grade_{results.product_name}.csv",
                        mime="text/csv"
                    )

                with col2:
                    excel_data = dataframe_to_excel(weekly_df)
                    st.download_button(
                        label="Download Results (Excel)",
                        data=excel_data,
                        file_name=f"historical_grade_{results.product_name}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    else:  # Batch Upload for Historical
        st.subheader("Step 1: Download Template")
        template_df = get_historical_template()

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download CSV Template",
                data=dataframe_to_csv(template_df),
                file_name="historical_template.csv",
                mime="text/csv"
            )
        with col2:
            st.download_button(
                label="Download Excel Template",
                data=dataframe_to_excel(template_df),
                file_name="historical_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.caption("One row per product-week. Add more rows for additional weeks or products.")

        st.divider()

        st.subheader("Step 2: Upload Your Data")
        uploaded_file = st.file_uploader(
            "Choose a CSV or Excel file",
            type=['csv', 'xlsx', 'xls'],
            key="historical_upload"
        )

        if uploaded_file is not None:
            df, parse_error = parse_upload(uploaded_file)

            if parse_error:
                st.error(parse_error)
            else:
                st.subheader("Data Preview")
                st.dataframe(df.head(), use_container_width=True)

                is_valid, errors = validate_historical_data(df)

                if not is_valid:
                    st.error("Validation errors found:")
                    for error in errors:
                        st.error(f"- {error}")
                else:
                    st.success(f"Data validated successfully! {len(df)} promotions found.")

                    if st.button("Grade All Promotions", type="primary"):
                        with st.spinner("Grading promotions..."):
                            inputs_list = parse_historical_data(df)
                            results_list = [analyze_historical(inp) for inp in inputs_list]

                        st.divider()
                        st.subheader("Batch Results Summary")

                        # Summary chart
                        fig = create_historical_batch_comparison(results_list)
                        st.plotly_chart(fig, use_container_width=True)

                        # Summary table
                        summary_data = []
                        for r in results_list:
                            summary_data.append({
                                'Product': r.product_name,
                                'Breakeven Lift %': f"{r.breakeven_lift_pct * 100:.1f}%" if r.breakeven_lift_pct != float('inf') else "N/A",
                                'Actual Lift %': f"{r.overall_lift_pct * 100:.1f}%",
                                'Grade Score': f"{r.overall_grade_score:.0f}%",
                                'Total Profit': f"${r.total_actual_profit:,.2f}",
                                'vs Baseline': f"${r.overall_profit_vs_baseline:+,.2f}",
                                'Status': 'PASS' if r.overall_passed else 'FAIL'
                            })
                        summary_df = pd.DataFrame(summary_data)

                        def highlight_status(row):
                            if row['Status'] == 'PASS':
                                return ['background-color: #d4edda'] * len(row)
                            else:
                                return ['background-color: #f8d7da'] * len(row)

                        styled_df = summary_df.style.apply(highlight_status, axis=1)
                        st.dataframe(styled_df, use_container_width=True, hide_index=True)

                        # Individual drill-down
                        st.divider()
                        st.subheader("Individual Product Analysis")
                        selected_product = st.selectbox(
                            "Select a product for detailed analysis:",
                            options=[r.product_name for r in results_list]
                        )

                        if selected_product:
                            selected_results = next(r for r in results_list if r.product_name == selected_product)

                            # Show pass/fail banner
                            if selected_results.overall_passed:
                                st.success(f"PASSED - Score: {selected_results.overall_grade_score:.0f}%")
                            else:
                                st.error(f"FAILED - Score: {selected_results.overall_grade_score:.0f}%")

                            # Tabs for details
                            tab1, tab2, tab3 = st.tabs(["Weekly Scorecard", "Cumulative View", "Profit Analysis"])

                            with tab1:
                                fig = create_weekly_scorecard(selected_results)
                                st.plotly_chart(fig, use_container_width=True)

                            with tab2:
                                fig = create_cumulative_chart(selected_results)
                                st.plotly_chart(fig, use_container_width=True)

                            with tab3:
                                fig = create_profit_waterfall(selected_results)
                                st.plotly_chart(fig, use_container_width=True)

                        # Export
                        st.divider()
                        st.subheader("Export Batch Results")
                        col1, col2 = st.columns(2)

                        with col1:
                            csv_data = dataframe_to_csv(summary_df)
                            st.download_button(
                                label="Download All Results (CSV)",
                                data=csv_data,
                                file_name="batch_historical_grades.csv",
                                mime="text/csv"
                            )

                        with col2:
                            excel_data = dataframe_to_excel(summary_df)
                            st.download_button(
                                label="Download All Results (Excel)",
                                data=excel_data,
                                file_name="batch_historical_grades.xlsx",
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
- **Grade Score**: For historical grading, shows what percentage of the breakeven target was achieved (100% = met target).

**Rule of thumb**: Promotions requiring >100% lift are challenging to achieve profitably.
""")
