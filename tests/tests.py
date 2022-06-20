import numpy as np
import rasterio
from matplotlib import pyplot as plt

import sample

# path = "world.rgb.tif"
# coords = [[0, 0], [2, 4], [2, 4]]

# path = "test.tif"
# coords = [[429951.5, 6059757.1], [429951.5, 6059758.1], [429951.5, 6059759.1]]
# with rasterio.open(path) as f:
#     # values = list(f.sample(coords))
#     values = list(sample.sample_gen(f, coords))
#     print(values)


path = "test.tif"
x = np.linspace(429957, 429960, 500)
y = np.linspace(6059752, 6059748, 500)
coords = np.array([x, y]).T
with rasterio.open(path) as f:
    # values = list(f.sample(coords))
    values = list(sample.sample_gen(f, coords.tolist(), indexes=1))
    print(values)
    data = np.array(values).T[0]
    # plt.subplot()
    plt.plot(data)
    plt.show()