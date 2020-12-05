from typing import List, Any, Tuple
from pathlib import Path
import math

from PIL import Image
from imagenate.libs.enum import CustomEnum

# TODO: 可能ならライブラリのクラス使いたい
class Position:
    x: int = 0
    y: int = 0

    def reset(self):
        self.x = 0
        self.y = 0


class CelPosition(CustomEnum):
    """結合処理時の各セルの中で位置調整"""

    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"

    MIDDLE_LEFT = "middle_left"
    CENTER = "center"
    MIDDLE_RIGHT = "middle_right"

    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"

    @property
    def is_top(self):
        return self in [
            CelPosition.TOP_LEFT,
            CelPosition.TOP_CENTER,
            CelPosition.TOP_RIGHT,
        ]

    @property
    def is_middle(self):
        return self in [
            CelPosition.MIDDLE_LEFT,
            CelPosition.CENTER,
            CelPosition.MIDDLE_RIGHT,
        ]

    @property
    def is_bottom(self):
        return self in [
            CelPosition.BOTTOM_LEFT,
            CelPosition.BOTTOM_CENTER,
            CelPosition.BOTTOM_RIGHT,
        ]

    @property
    def is_left(self):
        return self in [
            CelPosition.TOP_LEFT,
            CelPosition.MIDDLE_LEFT,
            CelPosition.BOTTOM_LEFT,
        ]

    @property
    def is_center(self):
        return self in [
            CelPosition.TOP_CENTER,
            CelPosition.CENTER,
            CelPosition.BOTTOM_CENTER,
        ]

    @property
    def is_right(self):
        return self in [
            CelPosition.TOP_RIGHT,
            CelPosition.MIDDLE_RIGHT,
            CelPosition.BOTTOM_RIGHT,
        ]


def concat_image_by_path(pathes: List[str], **kwargs) -> Image:
    """パスをもとに画像を結合"""

    # パスがファイルであるかチェック
    for path in pathes:
        if not Path(path).is_file():
            print(f"{path} is not file")
            return None

    images: List[Image] = []
    for path in pathes:
        # if not image raise PIL.UnidentifiedImageError
        image = Image.open(path)
        images.append(image)

    return concat_image(images, **kwargs)


def _get_grids(images, row: int, col: int) -> List[List[Any]]:
    grid = []

    r = 0
    c = 0
    line = []

    # colが無限(=0)で、rowが指定されている場合等分して配置
    if row > 0 and col == 0:
        col = math.floor(len(images) / row)

    for image in images:
        line.append(image)
        c += 1

        if col <= c:
            grid.append(line)
            r += 1
            c = 0
            line = []
            if row <= r:
                break

    if line:
        grid.append(line)

    # TODO: ループして埋まるで配置？
    return grid


def _get_sizes(grid: List[List[Any]]) -> Tuple[List[int], List[int]]:
    """縦横格子状に並んでいるときの分割サイズを取得

    1行目は3列、２行目は２列などには未対応
    """
    widthes = [0] * len(grid)
    heights = [0] * len(grid[0])

    # 縦横の最大サイズを、行列のサイズとして取得
    for r in range(0, len(grid)):
        line = grid[r]
        for c in range(0, len(line)):
            cel = line[c]
            if heights[r] < cel.height:
                heights[r] = cel.height

            if widthes[c] < cel.width:
                widthes[c] = cel.width

    return widthes, heights


def _get_diff(cel_position: CelPosition, width: int, height: int, cel: Image):
    """セル内に収まらないときの調整料を取得"""
    diff = Position()

    if width > cel.width:
        if cel_position.is_center:
            diff.x = (width - cel.width) // 2
        elif cel_position.is_right:
            diff.x = width - cel.width

    if height > cel.height:
        if cel_position.is_middle:
            diff.y = (height - cel.height) // 2
        elif cel_position.is_bottom:
            diff.y = height - cel.height

    return diff


def concat_image(
    images,
    *,
    row: int = 0,
    col: int = 0,
    cel_position: CelPosition = CelPosition.CENTER,
) -> Image:
    """画像を結合したオブジェクトを返却"""

    # パラメータチェック
    if not images:
        return None
    if row <= 0 and col <= 0:
        return None

    # TODO: サイズ違いで正方形のグリッドに収まらない場合もある
    # TODO: 詰めて並べる分割
    # TODO: 拡大方法別の分割

    # グリッドに配置
    grid = _get_grids(images, row, col)
    # サイズの取得
    widthes, heights = _get_sizes(grid)
    # 貼り付け
    image = Image.new("RGB", (sum(widthes), sum(heights)))
    pos = Position()
    for r in range(0, len(grid)):
        line = grid[r]
        pos.x = 0
        height = heights[r]
        for c in range(0, len(line)):
            cel = line[c]
            width = widthes[c]

            diff = _get_diff(cel_position, width, height, cel)
            image.paste(cel, (pos.x + diff.x, pos.y + diff.y))
            pos.x += width
        pos.y += height

    return image
