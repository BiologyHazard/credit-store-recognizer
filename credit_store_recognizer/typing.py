from cv2.typing import MatLike

type GrayImage = MatLike
type ColorImage = MatLike
type Image = GrayImage | ColorImage

type Range = tuple[int, int]
type Coordinate = tuple[int, int]
type Scope = tuple[Coordinate, Coordinate]
type Slice = slice | tuple[slice, slice]
