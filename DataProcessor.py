import numpy as np
import iminuit


def get_linear_regression(VX: np.ndarray,
                          VY: np.ndarray,
                          XERR: np.ndarray,
                          YERR: np.ndarray,
                          slope: float,
                          intersect: float) -> tuple[float, float]:
    func = lambda a, b, x_ex: a * x_ex + b
    chi_sq = lambda a, b: ( (((func(a, b, VX) - VY) / YERR) ** 2 + (((VY - b) / a - VX) / XERR) ** 2).sum() )


    m = iminuit.Minuit(chi_sq, a = slope, b = intersect)
    m.migrad()
    slope, intersect = m.values
    
    return slope, intersect