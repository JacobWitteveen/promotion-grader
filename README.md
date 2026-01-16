# Promotion Effectiveness & Breakeven Analyzer

A Streamlit application for analyzing product promotion effectiveness and calculating breakeven lift requirements. Grade historical promotions and forecast profitability of future promotions.

## Features

### Promo Grader
Analyze promotion profitability by calculating the required sales lift to maintain baseline profit.

- **Manual Entry**: Analyze individual products with custom pricing and cost inputs
- **Batch Upload**: Analyze multiple products via CSV/Excel upload
- **Key Metrics**:
  - Breakeven lift percentage
  - Standard vs promo margin comparison
  - Margin erosion analysis
- **Visualizations**:
  - Breakeven curve (units vs profit)
  - Profit sensitivity by lift level
  - Margin comparison charts

### Historical Grading
Grade past promotions by comparing actual weekly performance against breakeven targets.

- **Manual Entry**: Enter weekly baseline and actual units for individual promotions
- **Batch Upload**: Upload historical data in relational format
- **Weekly Scorecard**: Color-coded performance vs breakeven threshold
- **Cumulative Analysis**: Track performance over the promotion period
- **Profit Waterfall**: Visualize profit contribution by week

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd promotion-grader
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Usage

### Promo Grader - Manual Entry
1. Select "Promo Grader" from the navigation
2. Choose "Manual Entry"
3. Enter product details:
   - Product name
   - Standard price and promotional price
   - COGS, logistics, and other variable costs
   - Promo cost per unit (e.g., retailer subsidies)
   - Baseline units (expected sales at standard price)
4. Click "Analyze Promotion" to view results

### Promo Grader - Batch Upload
1. Download the CSV or Excel template
2. Fill in your product data
3. Upload the file and click "Analyze All Products"

### Historical Grading - Manual Entry
1. Select "Historical Grading" from the navigation
2. Enter promotion details (pricing, costs)
3. Specify number of weeks
4. Enter baseline and actual units for each week
5. Click "Grade Promotion" to see the scorecard

### Historical Grading - Batch Upload
1. Download the historical template
2. Fill in data with one row per product-week combination
3. Upload and analyze

## Data Formats

### Promo Grader Template
| Column | Required | Description |
|--------|----------|-------------|
| product_name | Yes | Product identifier |
| standard_price | Yes | Regular selling price |
| promo_price | Yes | Promotional price |
| cogs | Yes | Cost of goods sold per unit |
| logistics_cost | No | Logistics/shipping cost per unit |
| other_variable_costs | No | Other variable costs per unit |
| promo_cost_per_unit | No | Retailer subsidies or promo-specific costs |
| baseline_units | No | Expected units at standard price (default: 100) |

### Historical Grading Template
| Column | Required | Description |
|--------|----------|-------------|
| product_name | Yes | Product identifier |
| standard_price | Yes | Regular selling price |
| promo_price | Yes | Promotional price |
| cogs | Yes | Cost of goods sold per unit |
| logistics_cost | No | Logistics/shipping cost per unit |
| other_variable_costs | No | Other variable costs per unit |
| promo_cost_per_unit | No | Retailer subsidies or promo-specific costs |
| week | Yes | Week number (1, 2, 3, etc.) |
| baseline_volume | Yes | Expected units for that week |
| promo_volume | Yes | Actual units sold during promo |

## Key Calculations

### Breakeven Lift
```
Breakeven Lift = (Standard Margin / Promo Margin) - 1
```
The percentage increase in units needed during the promotion to maintain the same profit as selling at standard price.

### Margins
```
Standard Margin = Standard Price - COGS - Logistics - Other Costs
Promo Margin = Promo Price - COGS - Logistics - Other Costs - Promo Cost Per Unit
```

### Grade Score (Historical)
```
Grade Score = min(100, (Actual Lift / Breakeven Lift) * 100)
```
- Score >= 100: Promotion exceeded breakeven (Pass)
- Score < 100: Promotion fell short of breakeven (Fail)

## Project Structure

```
promotion-grader/
├── app.py              # Main Streamlit application
├── calculations.py     # Core business logic and calculations
├── data_handler.py     # CSV/Excel parsing and validation
├── visualizations.py   # Plotly chart functions
├── requirements.txt    # Python dependencies
├── sample_data.csv     # Sample data template
└── README.md           # This file
```

## Dependencies

- streamlit
- pandas
- plotly
- openpyxl (for Excel support)

## License

MIT
