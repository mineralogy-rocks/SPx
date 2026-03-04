# -*- coding: UTF-8 -*-
import logging
from typing import Tuple, Dict, Any

import pandas as pd
import numpy as np
from scipy.optimize import minimize_scalar
from tqdm import tqdm

from src.config import settings


logger = logging.getLogger(__name__)


def _calculate_ssr(a1: float, data: pd.Series, endmembers_df: pd.DataFrame) -> float:
    """
    Calculates the sum of squared residuals for a given mixture coefficient 'a1'.
    This is the objective function to be minimized.

    Args:
        a1: The mixture coefficient for the first endmember (a float between 0 and 1).
        data: A pandas Series representing one row of sample data.
        endmembers_df: A pandas DataFrame containing the two endmembers.

    Returns:
        The calculated sum of squared residuals as a float.
    """
    # Ensure a1 is within the valid range [0, 1]
    a1 = np.clip(a1, 0, 1)
    a2 = 1.0 - a1

    endmember1_params = endmembers_df.iloc[0, 1:]
    endmember2_params = endmembers_df.iloc[1, 1:]
    data_params = data.iloc[1:]

    # Predict the mixture spectrum using the current coefficients
    predicted_params = endmember1_params * a1 + endmember2_params * a2

    # Calculate squared residuals, handling potential division by zero
    # The term `(data_params + predicted_params) / 2` is used for normalization
    # and to prevent instability when values are close to zero.
    epsilon = 1e-9  # A small number to prevent division by zero
    denominator = (data_params + predicted_params) / 2

    # Using np.where to avoid division by zero
    residuals = np.where(np.abs(denominator) > epsilon, (predicted_params - data_params) / denominator, 0)

    squared_residuals = np.square(residuals)

    return np.sum(squared_residuals)


def _find_optimal_mixture(data: pd.Series, endmembers_df: pd.DataFrame) -> Tuple[float, float, float, Dict[str, Any]]:
    """
    Finds the optimal mixture coefficients (a1, a2) for a single data row.

    It uses the `minimize_scalar` function from SciPy to find the value of 'a1'
    that minimizes the sum of squared residuals.

    Args:
        data: A pandas Series representing one row of sample data.
        endmembers_df: A pandas DataFrame containing the two endmembers.

    Returns:
        A tuple containing:
        - a1_optimal (float): The optimal coefficient for the first endmember.
        - a2_optimal (float): The optimal coefficient for the second endmember.
        - min_ssr (float): The minimum sum of squared residuals found.
        - predicted_mixture (dict): A dictionary of the predicted parameter values.
    """
    # We use a bounded optimization method as a1 must be between 0 and 1.
    result = minimize_scalar(
        _calculate_ssr,
        bounds=(0, 1),
        args=(data, endmembers_df),
        method="bounded"
    )

    a1_optimal = result.x
    a2_optimal = 1.0 - a1_optimal
    min_ssr = result.fun

    # Recalculate the final predicted mixture with the optimal coefficients
    endmember1_params = endmembers_df.iloc[0, 1:]
    endmember2_params = endmembers_df.iloc[1, 1:]
    predicted_params = endmember1_params * a1_optimal + endmember2_params * a2_optimal
    predicted_mixture = predicted_params.to_dict()

    return a1_optimal, a2_optimal, min_ssr, predicted_mixture


def run_prediction():
    logger.info("Starting endmember prediction processing")

    _endmembers = pd.read_excel(settings.ENDMEMBERS_PATH)
    if len(_endmembers) > 2:
        raise ValueError(f"Too many endmembers in the file. Should be only 2, got {len(_endmembers)}.")

    _path = settings.OUTPUT_PATH / "data" / "results.xlsx"

    if len(pd.ExcelFile(_path).sheet_names) < 2:
        raise ValueError(f"File {_path} doesn't have a second sheet necessary for calculations.")

    _df = pd.read_excel(_path, sheet_name=1)

    if len(_df.columns[1:]) != len(_endmembers.columns[1:]):
        raise ValueError(
            f"Number of parameters in {_path} doesn't match the number of parameters in the endmembers."
        )

    results = []
    for index, row in tqdm(_df.iterrows(), desc="Processing rows", unit="row", total=len(_df)):
        try:
            a1, a2, ssr, mixture = _find_optimal_mixture(row, _endmembers)
            row_id = row.iloc[0]

            _loc_results = {
                "id": row_id,
                "a1": a1,
                "a2": a2,
                "ssr": ssr,
                **{f"{k}": v for k, v in mixture.items()},
            }
            results.append(_loc_results)

        except Exception as e:
            logger.error(f"Failed to process row {index}. Error: {e}", exc_info=True)

    results = pd.DataFrame(results)
    results.to_excel(settings.OUTPUT_PATH / "data" / "results_predicted.xlsx", index=False)

    logger.info("Prediction completed successfully")


def main():
    import coloredlogs

    if not settings.is_configured:
        settings.configure_from_env()

    coloredlogs.install(level='INFO', fmt='%(asctime)s %(levelname)s %(message)s')

    try:
        run_prediction()
    except Exception as e:
        logger.error(f"An error occurred during prediction: {str(e)}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    main()
