from typing import Dict, List, Tuple, Union, Any

import numpy as np
from numpy.typing import NDArray
from cv2.typing import MatLike

# Image
# Image = NDArray[np.int8]
Pixel = Tuple[int, int, int]

type GrayImage = NDArray[np.int8]
type ColorImage = MatLike
type Image = GrayImage | ColorImage
GrayPixel = int

# Recognizer
type Range = tuple[int, int]
type Coordinate = tuple[int, int]
type Scope = tuple[Coordinate, Coordinate]
# Slice = Tuple[Range, Range]
type Slice = slice | tuple[slice, slice]
# Rectangle = Tuple[Coordinate, Coordinate, Coordinate, Coordinate]
Rectangle = NDArray
Location = Union[Rectangle, Scope, Coordinate]

# Matcher
Hash = List[int]
Score = Tuple[float, float, float, float]

# Operation Plan
OpePlan = Tuple[str, int]

# BaseConstruct Plan
BasePlan = Dict[str, List[str]]

# Parameter
ParamArgs = List[str]
