import numpy as np


def box_area(arr: np.array):
    # arr: np.array([[x1, y1, x2, y2]])
    width = arr[:, 2] - arr[:, 0]
    height = arr[:, 3] - arr[:, 1]
    return width * height


def _box_inter_union(arr1, arr2):
    # arr1 of [N, 4]
    # arr2 of [N, 4]
    area1 = box_area(arr1)
    area2 = box_area(arr2)

    # Intersection
    top_left = np.maximum(arr1[:, :2], arr2[:, :2])  # [[x, y]]
    bottom_right = np.minimum(arr1[:, 2:], arr2[:, 2:])  # [[x, y]]
    wh = bottom_right - top_left
    # clip: if boxes not overlap then make it zero
    intersection = wh[:, 0].clip(0) * wh[:, 1].clip(0)

    # union
    union = area1 + area2 - intersection
    return intersection, union


def box_iou(arr1, arr2):
    # arr1[N, 4]
    # arr2[N, 4]
    # N = number of bounding boxes
    # assert (arr1[:, 2:] > arr[:, :2]).all()
    # assert (arr2[:, 2:] > arr[:, :2]).all()
    inter, union = _box_inter_union(arr1, arr2)
    iou = inter / union
    return iou


def calculate_bounding_boxes(roi: np.array):
    import cv2
    import numpy as np

    _, markers = cv2.connectedComponents(np.expand_dims(roi.astype(np.uint8), axis=2), connectivity=8)

    markers = np.squeeze(markers)

    bounding_boxes = []

    for label in range(1, int(np.max(markers)) + 1):
        locations = np.transpose(np.nonzero(markers == label))

        min_x, max_x, min_y, max_y = np.min(locations[:, 1]), np.max(locations[:, 1]), np.min(locations[:, 0]), np.max(
            locations[:, 0])

        bounding_boxes.append((min_x, max_x, min_y, max_y))

    return bounding_boxes
