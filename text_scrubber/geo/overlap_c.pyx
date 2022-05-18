# cython: language_level=3

import cython
from libc.stdint cimport int32_t, int64_t

import numpy as np
cimport numpy as np


@cython.boundscheck(False)
@cython.wraparound(False)
def get_overlap(int32_t[:] query_vector, int32_t[:] candidates_data, int32_t[:] candidates_indptr,
                int32_t[:] candidates_indices) -> np.ndarray:
    """
    Calculates the overlap in character tokens between the query and all candidates

    :param query_vector: vector containing the query token counts
    :param candidates_data: vector containing the flattened candidate token counts
    :param candidates_indptr: vector containing the candidate data row boundaries
    :param candidates_indices: vector containing the candidate data column indices
    :return: vector of overlap counts
    """
    # Create container to hold the amount of overlap
    cdef int32_t n_candidates = candidates_indptr.shape[0] - 1
    overlap = np.zeros(n_candidates, dtype=np.int32)
    cdef int32_t[:] overlap_view = overlap

    # Determine overlap between query and candidates
    cdef int32_t data_idx, row_idx, col_idx, row_overlap
    for row_idx in range(n_candidates):
        row_overlap = 0
        for data_idx in range(candidates_indptr[row_idx], candidates_indptr[row_idx + 1]):
            col_idx = candidates_indices[data_idx]
            row_overlap += min(candidates_data[data_idx], query_vector[col_idx])
        overlap[row_idx] = row_overlap

    return overlap
