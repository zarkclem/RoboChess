import pytest

from robochess_vision.grid_mapping import DegenerateQuadrilateralError, compute_grid

VALID_CORNERS = {
    "a1": (100.0, 500.0),
    "h1": (500.0, 500.0),
    "a8": (100.0, 100.0),
    "h8": (500.0, 100.0),
}


def test_compute_grid_returns_64_squares_with_unique_ids():
    squares = compute_grid(VALID_CORNERS)
    assert len(squares) == 64
    assert len({sq.id for sq in squares}) == 64


def test_compute_grid_covers_all_algebraic_ids():
    squares = compute_grid(VALID_CORNERS)
    ids = {sq.id for sq in squares}
    expected = {f"{file}{rank}" for file in "abcdefgh" for rank in range(1, 9)}
    assert ids == expected


def test_a1_square_sits_near_the_a1_corner():
    squares = {sq.id: sq for sq in compute_grid(VALID_CORNERS)}
    a1_region = squares["a1"].image_region
    centroid_x = sum(p[0] for p in a1_region) / 4
    centroid_y = sum(p[1] for p in a1_region) / 4
    assert 100.0 < centroid_x < 150.0
    assert 450.0 < centroid_y < 500.0


def test_depth_region_is_inside_image_region():
    squares = compute_grid(VALID_CORNERS)
    for sq in squares:
        img_xs = [p[0] for p in sq.image_region]
        img_ys = [p[1] for p in sq.image_region]
        depth_xs = [p[0] for p in sq.depth_region]
        depth_ys = [p[1] for p in sq.depth_region]
        assert min(img_xs) <= min(depth_xs) and max(depth_xs) <= max(img_xs)
        assert min(img_ys) <= min(depth_ys) and max(depth_ys) <= max(img_ys)


def test_missing_corner_raises_value_error():
    incomplete = {k: v for k, v in VALID_CORNERS.items() if k != "h8"}
    with pytest.raises(ValueError):
        compute_grid(incomplete)


def test_nearly_collinear_points_are_rejected():
    degenerate = {
        "a1": (100.0, 100.0),
        "h1": (101.0, 100.0),
        "a8": (100.0, 101.0),
        "h8": (101.0, 101.0),
    }
    with pytest.raises(DegenerateQuadrilateralError):
        compute_grid(degenerate)
