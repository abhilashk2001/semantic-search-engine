"""Behavioral tests for distance metrics: closer pairs yield smaller values."""

import numpy as np

from engine import distance


def test_cosine_ignores_magnitude():
    a = np.array([1.0, 0.0], dtype=np.float32)
    b = np.array([10.0, 0.0], dtype=np.float32)  # same direction, larger magnitude
    ua = distance.prepare_vector("cosine", a)
    ub = distance.prepare_vector("cosine", b)
    # Identical direction -> distance ~0 regardless of magnitude.
    assert distance.cosine_distance(ua, ub) == 0.0


def test_cosine_orders_by_angle():
    q = distance.prepare_vector("cosine", np.array([1.0, 0.0], dtype=np.float32))
    near = distance.prepare_vector("cosine", np.array([1.0, 0.1], dtype=np.float32))
    far = distance.prepare_vector("cosine", np.array([0.0, 1.0], dtype=np.float32))
    assert distance.cosine_distance(q, near) < distance.cosine_distance(q, far)


def test_euclidean_orders_by_distance():
    q = np.array([0.0, 0.0], dtype=np.float32)
    near = np.array([1.0, 0.0], dtype=np.float32)
    far = np.array([5.0, 5.0], dtype=np.float32)
    assert distance.euclidean_distance(q, near) < distance.euclidean_distance(q, far)


def test_dot_smaller_is_closer():
    q = np.array([1.0, 0.0], dtype=np.float32)
    aligned = np.array([2.0, 0.0], dtype=np.float32)
    opposed = np.array([-2.0, 0.0], dtype=np.float32)
    assert distance.dot_distance(q, aligned) < distance.dot_distance(q, opposed)


def test_get_distance_rejects_unknown_metric():
    import pytest

    with pytest.raises(ValueError):
        distance.get_distance("manhattan")
