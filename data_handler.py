"""
Data handling utilities for CSV/Excel file parsing and validation.
"""
import pandas as pd
from io import BytesIO
from typing import Tuple, Optional

REQUIRED_COLUMNS = ['product_name', 'standard_price', 'promo_price', 'cogs']
OPTIONAL_COLUMNS = ['logistics_cost', 'other_variable_costs', 'promo_terms', 'baseline_units']
ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


def parse_upload(uploaded_file) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Parse uploaded CSV or Excel file.

    Args:
        uploaded_file: Streamlit UploadedFile object

    Returns:
        Tuple of (DataFrame or None, error message or None)
    """
    try:
        file_name = uploaded_file.name.lower()

        if file_name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif file_name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            return None, "Unsupported file format. Please upload a CSV or Excel file."

        # Normalize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

        return df, None

    except Exception as e:
        return None, f"Error parsing file: {str(e)}"


def validate_data(df: pd.DataFrame) -> Tuple[bool, list[str]]:
    """
    Validate that DataFrame has required columns and valid data types.

    Args:
        df: DataFrame to validate

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Check required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")

    if errors:
        return False, errors

    # Check for numeric types in price/cost columns
    numeric_cols = ['standard_price', 'promo_price', 'cogs']
    if 'logistics_cost' in df.columns:
        numeric_cols.append('logistics_cost')
    if 'other_variable_costs' in df.columns:
        numeric_cols.append('other_variable_costs')
    if 'baseline_units' in df.columns:
        numeric_cols.append('baseline_units')

    for col in numeric_cols:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                if df[col].isna().any():
                    errors.append(f"Column '{col}' contains non-numeric values")
            except Exception:
                errors.append(f"Column '{col}' could not be converted to numeric")

    # Check for negative values in costs
    for col in ['standard_price', 'promo_price', 'cogs']:
        if col in df.columns and (df[col] < 0).any():
            errors.append(f"Column '{col}' contains negative values")

    # Check promo price is less than standard price
    if 'standard_price' in df.columns and 'promo_price' in df.columns:
        invalid_promos = df['promo_price'] > df['standard_price']
        if invalid_promos.any():
            count = invalid_promos.sum()
            errors.append(f"{count} row(s) have promo price greater than standard price")

    # Check for empty DataFrame
    if len(df) == 0:
        errors.append("File contains no data rows")

    return len(errors) == 0, errors


def fill_defaults(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill optional columns with default values if missing.

    Args:
        df: DataFrame to process

    Returns:
        DataFrame with defaults filled
    """
    df = df.copy()

    defaults = {
        'logistics_cost': 0.0,
        'other_variable_costs': 0.0,
        'promo_terms': '',
        'baseline_units': 100.0
    }

    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default
        else:
            df[col] = df[col].fillna(default)

    return df


def get_sample_template() -> pd.DataFrame:
    """
    Generate a sample template DataFrame for users to download.

    Returns:
        Sample DataFrame with example data
    """
    data = {
        'product_name': ['Widget A', 'Widget B', 'Premium Product'],
        'standard_price': [29.99, 49.99, 99.99],
        'promo_price': [24.99, 39.99, 79.99],
        'cogs': [12.00, 20.00, 40.00],
        'logistics_cost': [2.00, 3.00, 5.00],
        'other_variable_costs': [1.00, 2.00, 3.00],
        'promo_terms': ['20% off', '20% off', '20% off'],
        'baseline_units': [500, 300, 100]
    }
    return pd.DataFrame(data)


def dataframe_to_csv(df: pd.DataFrame) -> bytes:
    """
    Convert DataFrame to CSV bytes for download.

    Args:
        df: DataFrame to convert

    Returns:
        CSV as bytes
    """
    return df.to_csv(index=False).encode('utf-8')


def dataframe_to_excel(df: pd.DataFrame) -> bytes:
    """
    Convert DataFrame to Excel bytes for download.

    Args:
        df: DataFrame to convert

    Returns:
        Excel file as bytes
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Results')
    return output.getvalue()
