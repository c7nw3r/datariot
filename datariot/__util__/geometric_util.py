import cv2
import numpy as np


def calculate_bounding_boxes(roi: np.array):
    _, markers = cv2.connectedComponents(np.expand_dims(roi.astype(np.uint8), axis=2), connectivity=8)
    markers = np.squeeze(markers)
    bounding_boxes = []
    # np.savetxt("roi.txt", roi)

    for label in range(1, int(np.max(markers)) + 1):
        locations = np.transpose(np.nonzero(markers == label))

        min_x, max_x, min_y, max_y = (
            np.min(locations[:, 1]),
            np.max(locations[:, 1]),
            np.min(locations[:, 0]),
            np.max(locations[:, 0])
        )

        bounding_boxes.append((min_x, max_x, min_y, max_y))

    return bounding_boxes
