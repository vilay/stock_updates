import numpy as np
from numba import njit

class Indicators:
    @staticmethod
    def cmma(bar_data, lookback):
        @njit
        def vec_cmma(values):
            n = len(values)
            out = np.array([np.nan for _ in range(n)])
            for i in range(lookback, n):
                ma = 0
                for j in range(i - lookback, i):
                    ma += values[j]
                ma /= lookback
                out[i] = values[i] - ma
            return out

        return vec_cmma(bar_data.close)
