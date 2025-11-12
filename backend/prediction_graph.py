"""
Prediction and Visualization Module

Provides functions to make predictions on new data and generate 
professional visualizations of emission forecasts.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import joblib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import matplotlib
matplotlib.use('Agg')  # Headless backend for server environments

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_model(model_path: str = None) -> Dict:
    """Load the trained emission forecast model.

    Args:
        model_path: Path to the saved model file. If None, uses default path.

    Returns:
        Dictionary containing model and associated artifacts

    Raises:
        FileNotFoundError: If model file doesn't exist
    """
    if model_path is None:
        model_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'emission_forecast_model.pkl'
        )

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found at {model_path}. Please train the model first using training.py"
        )

    logger.info(f"Loading model from: {model_path}")
    model_artifact = joblib.load(model_path)
    logger.info(f"Model loaded: {model_artifact['model_name']}")

    return model_artifact


def prepare_input_data(data: pd.DataFrame, model_artifact: Dict) -> np.ndarray:
    """Prepare input data for prediction by applying the same preprocessing.

    Args:
        data: DataFrame with feature columns
        model_artifact: Model artifact containing scaler and imputer

    Returns:
        Preprocessed feature array ready for prediction
    """
    features = model_artifact['features']

    # Ensure all required features exist
    for col in features:
        if col not in data.columns:
            data[col] = 0.0
            logger.warning(
                f"Feature '{col}' not found in input data, filled with 0.0")

    # Extract features in correct order
    X = data[features].copy()

    # Apply same preprocessing as training
    imputer = model_artifact['imputer']
    scaler = model_artifact['scaler']

    X_imputed = imputer.transform(X)
    X_scaled = scaler.transform(X_imputed)

    return X_scaled


def predict_emissions(data: pd.DataFrame, model_path: str = None) -> np.ndarray:
    """Make emission predictions on new data.

    Args:
        data: DataFrame containing feature columns
        model_path: Path to saved model (optional)

    Returns:
        Array of predicted emissions in tCO2e
    """
    # Load model
    model_artifact = load_model(model_path)

    # Prepare data
    X_prepared = prepare_input_data(data, model_artifact)

    # Make predictions
    model = model_artifact['model']
    predictions = model.predict(X_prepared)

    logger.info(f"Generated {len(predictions)} predictions")

    return predictions


def plot_prediction_graph(
    dates: Union[List, pd.Series, np.ndarray],
    actual: Optional[Union[List, pd.Series, np.ndarray]] = None,
    predicted: Union[List, pd.Series, np.ndarray] = None,
    title: str = "Emission Forecast",
    output_path: str = None,
    train_test_split_idx: Optional[int] = None,
    show_metrics: bool = True,
    figsize: Tuple[int, int] = (16, 7),
    dpi: int = 200
) -> str:
    """Plot a professional prediction graph with actual vs predicted emissions.

    Args:
        dates: Array of dates for x-axis
        actual: Actual emission values (optional)
        predicted: Predicted emission values
        title: Graph title
        output_path: Path to save the plot. If None, saves to current directory
        train_test_split_idx: Index to mark train/test split (optional)
        show_metrics: Whether to display metrics text box
        figsize: Figure size as (width, height)
        dpi: Resolution in dots per inch

    Returns:
        Path to saved plot file
    """
    # Convert inputs to numpy arrays
    dates = np.array(dates)
    if predicted is not None:
        predicted = np.array(predicted)
    if actual is not None:
        actual = np.array(actual)

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot actual emissions if provided
    if actual is not None:
        ax.plot(dates, actual,
                label='Actual Emissions', linewidth=2.5, color='#1e88e5',
                alpha=0.9, marker='o', markersize=3,
                markevery=max(1, len(dates)//50))

    # Plot predictions
    if predicted is not None:
        ax.plot(dates, predicted,
                label='Model Predictions', linewidth=2.5,
                linestyle='--', color='#e53935', alpha=0.85,
                marker='s', markersize=3,
                markevery=max(1, len(dates)//50))

    # Add train/test split visualization
    if train_test_split_idx is not None:
        # Highlight train/test regions
        ax.axvspan(dates[0], dates[train_test_split_idx],
                   alpha=0.05, color='blue', label='Training Period')
        ax.axvspan(dates[train_test_split_idx], dates[-1],
                   alpha=0.05, color='green', label='Test Period')

        # Add vertical split line
        ax.axvline(x=dates[train_test_split_idx], color='#ff6f00',
                   linestyle='-.', linewidth=3,
                   label='Train/Test Split', alpha=0.8)

    # Calculate and display metrics if both actual and predicted are provided
    if actual is not None and predicted is not None and show_metrics:
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

        mae = mean_absolute_error(actual, predicted)
        rmse = np.sqrt(mean_squared_error(actual, predicted))
        r2 = r2_score(actual, predicted)
        mape = np.mean(np.abs((actual - predicted) /
                       np.clip(actual, 1e-10, None))) * 100

        metrics_text = f'MAE: {mae:.2f}\nRMSE: {rmse:.2f}\nR²: {r2:.4f}\nMAPE: {mape:.2f}%'
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
        ax.text(0.98, 0.97, metrics_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='top',
                horizontalalignment='right', bbox=props)

        title_with_metrics = f'{title}\n(R² = {r2:.4f}, MAPE = {mape:.2f}%)'
    else:
        title_with_metrics = title

    # Enhanced title and labels
    ax.set_title(title_with_metrics, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=13, fontweight='bold')
    ax.set_ylabel('Total Emissions (tCO2e)', fontsize=13, fontweight='bold')

    # Improved legend
    ax.legend(loc='upper left', framealpha=0.95, fontsize=11,
              shadow=True, fancybox=True, ncol=2)

    # Enhanced grid and styling
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    ax.set_facecolor('#fafafa')

    # Format axes
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)

    plt.tight_layout()

    # Save figure
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f'emission_prediction_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        )

    plt.savefig(output_path, dpi=dpi, facecolor='white', edgecolor='none')
    plt.close()

    logger.info(f"Prediction graph saved to: {output_path}")
    return output_path


def predict_and_plot(
    data: pd.DataFrame,
    date_column: str = 'date',
    actual_column: Optional[str] = None,
    model_path: str = None,
    output_path: str = None,
    title: str = "Carbon Emission Forecast",
    train_test_split_ratio: float = 0.8
) -> Tuple[np.ndarray, str]:
    """Complete workflow: predict emissions and generate visualization.

    Args:
        data: DataFrame with features and optionally actual emissions
        date_column: Name of date column
        actual_column: Name of actual emissions column (optional)
        model_path: Path to model file (optional)
        output_path: Path to save plot (optional)
        title: Graph title
        train_test_split_ratio: Ratio for train/test split visualization

    Returns:
        Tuple of (predictions array, path to saved plot)
    """
    # Make predictions
    predictions = predict_emissions(data, model_path)

    # Extract dates
    dates = pd.to_datetime(data[date_column])

    # Extract actual values if column provided
    actual = data[actual_column].values if actual_column and actual_column in data.columns else None

    # Calculate split index
    split_idx = int(
        len(data) * train_test_split_ratio) if train_test_split_ratio else None

    # Plot graph
    plot_path = plot_prediction_graph(
        dates=dates,
        actual=actual,
        predicted=predictions,
        title=title,
        output_path=output_path,
        train_test_split_idx=split_idx,
        show_metrics=(actual is not None)
    )

    return predictions, plot_path


def generate_future_predictions(
    base_data: pd.DataFrame,
    periods: int = 52,
    frequency: str = 'W',
    model_path: str = None,
    output_path: str = None
) -> Tuple[pd.DataFrame, str]:
    """Generate future emission predictions and visualize them.

    Args:
        base_data: Historical data to base predictions on
        periods: Number of future periods to predict
        frequency: Time frequency ('D' for daily, 'W' for weekly, 'M' for monthly)
        model_path: Path to model file (optional)
        output_path: Path to save plot (optional)

    Returns:
        Tuple of (predictions DataFrame, path to saved plot)
    """
    # Load model
    model_artifact = load_model(model_path)

    # Get last date from base data
    last_date = pd.to_datetime(base_data['date'].iloc[-1])

    # Generate future dates
    future_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=1 if frequency == 'D' else 7),
        periods=periods,
        freq=frequency
    )

    # Create future data frame by replicating last known values
    # In practice, you'd use more sophisticated forecasting methods
    future_data = pd.DataFrame()
    future_data['date'] = future_dates

    # Copy features from last observation (simplified approach)
    for feature in model_artifact['features']:
        if feature in base_data.columns:
            future_data[feature] = base_data[feature].iloc[-1]
        else:
            future_data[feature] = 0.0

    # Make predictions
    X_prepared = prepare_input_data(future_data, model_artifact)
    future_predictions = model_artifact['model'].predict(X_prepared)

    # Create results DataFrame
    results = pd.DataFrame({
        'date': future_dates,
        'predicted_emissions_tco2e': future_predictions
    })

    # Plot
    plot_path = plot_prediction_graph(
        dates=future_dates,
        actual=None,
        predicted=future_predictions,
        title=f"Future Emission Forecast ({periods} {frequency} periods)",
        output_path=output_path,
        show_metrics=False
    )

    logger.info(f"Generated {periods} future predictions")

    return results, plot_path


# ====================
# MAIN EXECUTION
# ====================

if __name__ == "__main__":
    """Example usage of prediction functions."""

    # Example 1: Load existing data and make predictions
    logger.info("Example: Loading data and making predictions...")

    csv_path = os.path.join(os.path.dirname(__file__),
                            'ecosphere_synthetic.csv')

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)

        # Convert date column
        if 'week_start_date' in df.columns:
            df['date'] = pd.to_datetime(df['week_start_date'])
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])

        # Make predictions and plot
        predictions, plot_path = predict_and_plot(
            data=df,
            date_column='date',
            actual_column='total_emissions_tco2e',
            title="Carbon Emission Forecast - Validation"
        )

        print(f"\n{'='*60}")
        print(f"Predictions generated: {len(predictions)}")
        print(f"Plot saved to: {plot_path}")
        print(f"Sample predictions (first 5): {predictions[:5]}")
        print(f"{'='*60}\n")

        # Example 2: Generate future predictions
        logger.info("Example: Generating future predictions...")

        future_df, future_plot = generate_future_predictions(
            base_data=df,
            periods=26,  # 26 weeks (6 months)
            frequency='W',
            output_path=os.path.join(os.path.dirname(
                __file__), 'future_forecast.png')
        )

        print(f"\n{'='*60}")
        print(f"Future predictions generated: {len(future_df)}")
        print(f"Future plot saved to: {future_plot}")
        print(f"\nFuture predictions (first 5):")
        print(future_df.head())
        print(f"{'='*60}\n")

    else:
        logger.warning(f"Dataset not found at {csv_path}")
        logger.info(
            "Please run training.py first to generate the dataset and model")
