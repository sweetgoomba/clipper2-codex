"""Validation shared by gallery preparation and query comparison."""
import numpy as np


def embedding_failure(vector, dimension: int) -> str | None:
    if vector is None:
        return 'missing_embedding'
    if vector.shape != (dimension,):
        return 'dimension_mismatch'
    if not np.all(np.isfinite(vector)):
        return 'non_finite_embedding'
    norm = float(np.linalg.norm(vector))
    if norm <= 1e-8:
        return 'zero_embedding'
    if not np.isfinite(norm) or abs(norm - 1.0) > 1e-5:
        return 'not_normalized'
    return None
