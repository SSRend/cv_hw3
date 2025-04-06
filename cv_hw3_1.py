import cv2 as cv
import numpy as np
import os
from typing import List, Tuple, Dict


def extract_chessboard_images(
    video_file: str,
    board_pattern: Tuple[int, int],
    max_frames: int = 30,
    visualize: bool = False
) -> List[Tuple[np.ndarray, np.ndarray]]:
    video = cv.VideoCapture(video_file)
    img_select = []

    if not video.isOpened():
        raise IOError(f"Cannot open video file: {video_file}")

    frame_idx = 0
    skip_interval = 5  # 중복 방지를 위해 프레임 간 간격 조절

    while len(img_select) < max_frames:
        ret, frame = video.read()
        if not ret:
            break

        if frame_idx % skip_interval != 0:
            frame_idx += 1
            continue

        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        found, corners = cv.findChessboardCornersSB(
            gray, board_pattern, flags=cv.CALIB_CB_NORMALIZE_IMAGE
        )

        if found:
            corners = cv.cornerSubPix(
                gray, corners, (11, 11), (-1, -1),
                criteria=(cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            )
            img_select.append((frame, corners))

            if visualize:
                debug_img = frame.copy()
                cv.drawChessboardCorners(debug_img, board_pattern, corners, found)
                cv.imshow('Detected Chessboard', debug_img)
                cv.waitKey(200)  # 잠깐 표시

        frame_idx += 1

    video.release()
    if visualize:
        cv.destroyAllWindows()
    return img_select


def calibrate_camera(
    chessboard_data: List[Tuple[np.ndarray, np.ndarray]],
    board_pattern: Tuple[int, int],
    board_cellsize: float
) -> Dict:
    if not chessboard_data:
        raise ValueError("No chessboard data provided for calibration.")

    objp = np.zeros((board_pattern[1] * board_pattern[0], 3), np.float32)
    objp[:, :2] = np.mgrid[0:board_pattern[0], 0:board_pattern[1]].T.reshape(-1, 2)
    objp *= board_cellsize

    obj_points = [objp for _ in chessboard_data]
    img_points = [corners for _, corners in chessboard_data]

    image_size = (chessboard_data[0][0].shape[1], chessboard_data[0][0].shape[0])

    calib_flags = (
        cv.CALIB_ZERO_TANGENT_DIST |
        cv.CALIB_FIX_K3 |
        cv.CALIB_FIX_K4 |
        cv.CALIB_FIX_K5 |
        cv.CALIB_FIX_K6
    )

    ret, K, dist, rvecs, tvecs = cv.calibrateCamera(
        obj_points, img_points, image_size, None, None, flags=calib_flags
    )

    fx, fy = K[0, 0], K[1, 1]
    cx, cy = K[0, 2], K[1, 2]
    rmse = ret

    np.set_printoptions(precision=6, suppress=True)

    print("\n=== Camera Intrinsic Parameters ===")
    print(f"fx: {fx:.4f}, fy: {fy:.4f}")
    print(f"cx: {cx:.4f}, cy: {cy:.4f}")
    print(f"Distortion Coefficients: {dist.ravel()}")
    print(f"Reprojection Error (RMSE): {rmse:.4f}")

    return {
        'fx': fx,
        'fy': fy,
        'cx': cx,
        'cy': cy,
        'dist_coeffs': dist.ravel(),
        'rmse': rmse,
        'K': K
    }


if __name__ == '__main__':
    video_path = os.path.join(os.path.dirname(__file__), 'chessboard.mp4')
    board_pattern = (10, 7)         # (cols, rows) 내부 코너 개수
    board_cellsize = 1.0            # 셀 간 거리 (단위: 임의)

    print("🔍 Extracting chessboard frames...")
    chessboard_data = extract_chessboard_images(video_path, board_pattern, visualize=True)

    if not chessboard_data:
        print("❌ No valid chessboard frames found.")
    else:
        print("📏 Performing camera calibration...")
        calibration_result = calibrate_camera(chessboard_data, board_pattern, board_cellsize)
