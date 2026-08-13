import math
import pytest
from backend.app.services.pgvector_service import (
    PGVECTOR_DIMENSION,
    vector_to_literal,
)
def test_vector_literal_accepts_768_dimensions():
    vector = [
        0.0
        for _ in range(
            PGVECTOR_DIMENSION
        )
    ]
    literal = vector_to_literal(
        vector
    )
    assert literal.startswith("[")
    assert literal.endswith("]")
    assert literal.count(",") == (
        PGVECTOR_DIMENSION - 1
    )
def test_vector_literal_rejects_wrong_dimension():
    with pytest.raises(ValueError):
        vector_to_literal(
            [0.0, 1.0, 2.0]
        )
def test_vector_literal_rejects_non_finite_value():
    vector = [
        0.0
        for _ in range(
            PGVECTOR_DIMENSION
        )
    ]
    vector[20] = math.inf
    with pytest.raises(ValueError):
        vector_to_literal(
            vector
        )
