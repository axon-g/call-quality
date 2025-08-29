"""
This script does something.
"""
import logging
import os
from typing import List




def find_subarray_ix(ix, offset_cumsum: List[int]) -> None:
    """
    Finds which sub-array a given index belongs to in a continuous array.

    :param ix:
    :param offset_cumsum:
    :return: -1 subarray
    """
    if ix < 0:
        return -1
    for i, off in enumerate(offset_cumsum):
        if off > ix:
            return i
    return -1

