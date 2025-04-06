import cv2 as cv
import numpy as np
import os

# === 카메라 내부 파라미터 ===
K = np.array([
    [1972.3442, 0, 1042.9267],
    [0, 1920.0901, 296.8256],
    [0, 0, 1]
], dtype=np.float32)

# === 왜곡 계수 ===
dist_coeff = np.array([
    -0.167291,   # k1
    0.543998,    # k2
    0.0,         # p1 (tangential)
    0.0,         # p2 (tangential)
    0.0          # k3
], dtype=np.float32)

# === 비디오 파일 경로 설정 ===
video_path = os.path.join(os.path.dirname(__file__), 'chessboard.mp4')

# === 동영상 열기 ===
video = cv.VideoCapture(video_path)
if not video.isOpened():
    raise IOError(f"Cannot open video file: {video_path}")

# === 왜곡 보정용 맵 변수 ===
map1, map2 = None, None
show_rectify = True

print("🎥 Press 'r' to toggle between original and rectified view.")
print("❌ Press ESC to exit.")

while True:
    ret, frame = video.read()
    if not ret:
        break

    if show_rectify:
        if map1 is None or map2 is None:
            h, w = frame.shape[:2]
            # why K, K? because we keep same intrinsic after undistortion
            map1, map2 = cv.initUndistortRectifyMap(
                cameraMatrix=K,
                distCoeffs=dist_coeff,
                R=None,
                newCameraMatrix=K,
                size=(w, h),
                m1type=cv.CV_32FC1
            )
        undistorted = cv.remap(frame, map1, map2, interpolation=cv.INTER_LINEAR)
        display = undistorted.copy()
        info = "Rectified (Undistorted)"
    else:
        display = frame.copy()
        info = "Original"

    # === 텍스트 표시 ===
    cv.putText(display, info, (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv.imshow("Distortion Correction", display)

    key = cv.waitKey(1)
    if key == 27:  # ESC 종료
        break
    elif key == ord('r'):  # r 키: 원본/보정 토글
        show_rectify = not show_rectify

video.release()
cv.destroyAllWindows()
