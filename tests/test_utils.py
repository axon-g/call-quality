import unittest
import numpy as np

from lib.utils import find_subarray_ix


class MyTestCase(unittest.TestCase):
    def test_subarray_ix_equal_sizes(self):
        n = 7
        m = 3
        sizes = [m] * n
        sizes_cumsum = np.cumsum(sizes)

        tot_off = 0
        for sub_arr_ix in range(n):
            for j in range(m):
                ix_pred = find_subarray_ix(tot_off, sizes_cumsum)
                self.assertEqual(sub_arr_ix, ix_pred)
                tot_off += 1




if __name__ == '__main__':
    unittest.main()
