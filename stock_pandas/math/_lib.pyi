import numpy as np

def ewma(
    vals: np.ndarray,
    com: float,
    adjust: int,
    ignore_na: int,
    minp: int
) -> np.ndarray:
    ...
