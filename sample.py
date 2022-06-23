# Workaround for issue #378. A pure Python generator.
import math

import numpy as np

# import rasterio._loading
# with rasterio._loading.add_gdal_dll_directories():
from rasterio.enums import MaskFlags, Resampling
from rasterio.windows import Window
from rasterio.transform import rowcol
from rasterio.transform import xy as transform_xy

from itertools import zip_longest
from scipy.interpolate import RegularGridInterpolator


def _grouper(iterable, n, fillvalue=None):
    "Collect data into non-overlapping fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    # from itertools recipes
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def sample_gen(dataset, xy, indexes=None, masked=False):
    """Sample pixels from a dataset
    Parameters
    ----------
    dataset : rasterio Dataset
        Opened in "r" mode.
    xy : iterable
        Pairs of x, y coordinates in the dataset's reference system.
    indexes : int or list of int
        Indexes of dataset bands to sample.
    masked : bool, default: False
        Whether to mask samples that fall outside the extent of the
        dataset.
    Yields
    ------
    array
        A array of length equal to the number of specified indexes
        containing the dataset values for the bands corresponding to
        those indexes.
    """
    dt = dataset.transform
    read = dataset.read
    height = dataset.height
    width = dataset.width

    if indexes is None:
        indexes = dataset.indexes
    elif isinstance(indexes, int):
        indexes = [indexes]

    nodata = np.full(len(indexes), (dataset.nodata or 0), dtype=dataset.dtypes[0])
    if masked:
        # Masks for masked arrays are inverted (False means valid)
        mask = [MaskFlags.all_valid not in dataset.mask_flag_enums[i - 1] for i in indexes]
        nodata = np.ma.array(nodata, mask=mask)

    for (xp, yp) in xy:
        # dt.is_rectilinear
        if dt.a > 0 or dt.d > 0:
            dx_step = 1
        else:
            dx_step = -1
        if dt.b > 0 or dt.e > 0:
            dy_step = 1
        else:
            dy_step = -1
        row_off, col_off = rowcol(dt, xp, yp, np.round)
        if row_off < 0 or col_off < 0 or row_off >= height or col_off >= width:
            yield nodata
        else:
            window = Window(col_off + ((dx_step-1)/2) - 1, row_off + ((dy_step-1)/2), 2, 2)
            data = read(indexes, window=window, masked=masked)
            # watch out, transform_xy requires rows then cols instead of Window
            x, y = transform_xy(dt, rows=[row_off, row_off + dy_step], cols=[col_off - 1, col_off + dx_step - 1], offset='center')
            # x, y = transform_xy(dt, rows=[row_off - 1, row_off, row_off + 1], cols=[col_off - 1, col_off, col_off + 1],
            #                     offset='center')
            # locs = (x[::dx_step], y[::dy_step])
            locs = (x, y)
            # Locs should have the same shape as data, when data is partly outside window
            _, n, m = data.shape
            locs_corrected = locs[1][:n], locs[0][:m]
            result = []
            for band in range(len(indexes)):
                # use bounds_error=False to avoid floating point mess
                # fill_value only needed at the edge
                interpolator = RegularGridInterpolator(locs_corrected, data[band, ::1, ::1], bounds_error=False, fill_value=np.nan) #data[band, ::1, ::1].mean()
                result.append(float(interpolator((yp, xp), method='linear')))
            yield result
