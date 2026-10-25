import cv2
import numpy as np
import base64
import os


class ImageProcessor:

    # ============================================
    # BASE64 METHODS (Keep for compatibility)
    # ============================================

    @staticmethod
    def decode_base64(base64_string):
        """Convert base64 string to OpenCV image"""
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        image_bytes = base64.b64decode(base64_string)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img

    @staticmethod
    def encode_base64(image):
        """Convert OpenCV image to base64 string"""
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8')

    # ============================================
    # IMREAD / IMWRITE (Your requested methods)
    # ============================================

    @staticmethod
    def imread(file_path):
        """Read image from a file path or raw bytes using OpenCV."""
        if isinstance(file_path, (bytes, bytearray)):
            image_bytes = bytes(file_path)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError('Could not decode image bytes.')
            return img

        img = cv2.imread(file_path)
        if img is None:
            raise ValueError(f"Could not read image: {file_path}")
        return img

    @staticmethod
    def imencode_bytes(image, extension='.jpg'):
        """Encode an OpenCV image to bytes without creating a temporary file."""
        _, buffer = cv2.imencode(extension, image)
        return buffer.tobytes()

    @staticmethod
    def imwrite(file_path, image):
        """Write image to file using cv2.imwrite"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        success = cv2.imwrite(file_path, image)
        if not success:
            raise ValueError(f"Could not write image to: {file_path}")
        return success


    @staticmethod
    def apply_filters(image, blur=False, kernel_size_blur=5,
                      gaussian_blur=False, kernel_size_gaussian=5,
                      sharpen=False, median_blur=False, kernel_size_median=5,
                      flip=False, flip_code=1,
                      rotate=False, angle=90, auto_crop=True,
                      resize=False, width=None, height=None,
                      brightness=False, brightness_value=30,
                      contrast=False, contrast_value=1.5,
                      grayscale=False, sepia=False,
                      gaussian_noise=False, sigma=20):
        """
        Apply filters to image based on parameters.
        """
        result = image.copy()
        applied_filters = []

        # 1. Blur
        if blur:
            if kernel_size_blur % 2 == 0:
                kernel_size_blur += 1
            result = cv2.blur(result, (kernel_size_blur, kernel_size_blur))
            applied_filters.append(f"Blur {kernel_size_blur}x{kernel_size_blur}")

        # 2. Gaussian Blur
        if gaussian_blur:
            if kernel_size_gaussian % 2 == 0:
                kernel_size_gaussian += 1
            result = cv2.GaussianBlur(result, (kernel_size_gaussian, kernel_size_gaussian), 0)
            applied_filters.append(f"Gaussian Blur {kernel_size_gaussian}x{kernel_size_gaussian}")

        # 3. Sharpen
        if sharpen:
            kernel_sharpen = np.array([
                [0, -1, 0],
                [-1, 5, -1],
                [0, -1, 0]
            ])
            result = cv2.filter2D(result, -1, kernel_sharpen)
            applied_filters.append("Sharpen")

        # 4. Median Blur
        if median_blur:
            if kernel_size_median % 2 == 0:
                kernel_size_median += 1
            result = cv2.medianBlur(result, kernel_size_median)
            applied_filters.append(f"Median Blur {kernel_size_median}x{kernel_size_median}")

        # 5. Flip
        if flip:
            result = cv2.flip(result, flip_code)
            flip_names = {0: "Vertical", 1: "Horizontal", -1: "Both"}
            applied_filters.append(f"Flip {flip_names.get(flip_code, 'Unknown')}")

        # 6. Rotation
        if rotate:
            h, w = result.shape[:2]
            center = (w / 2, h / 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

            if auto_crop:
                cos = np.abs(rotation_matrix[0, 0])
                sin = np.abs(rotation_matrix[0, 1])
                new_w = int((h * sin) + (w * cos))
                new_h = int((h * cos) + (w * sin))
                rotation_matrix[0, 2] += (new_w / 2) - center[0]
                rotation_matrix[1, 2] += (new_h / 2) - center[1]
                result = cv2.warpAffine(result, rotation_matrix, (new_w, new_h))
            else:
                result = cv2.warpAffine(result, rotation_matrix, (w, h))

            applied_filters.append(f"Rotate {angle}°")

        # 7. Resize
        if resize:
            if width and height:
                result = cv2.resize(result, (width, height))
                applied_filters.append(f"Resize {width}x{height}")
            else:
                applied_filters.append("Resize skipped - both width and height required")

        # 8. Brightness
        if brightness:
            result = cv2.convertScaleAbs(result, alpha=1, beta=brightness_value)
            applied_filters.append(f"Brightness {brightness_value}")

        # 9. Contrast
        if contrast:
            result = cv2.convertScaleAbs(result, alpha=contrast_value, beta=0)
            applied_filters.append(f"Contrast {contrast_value}")

        # 10. Grayscale
        if grayscale:
            gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
            result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            applied_filters.append("Grayscale")

        # 11. Gaussian Noise
        if gaussian_noise:
            noise = np.random.normal(0, sigma, result.shape).astype(np.uint8)
            result = cv2.add(result, noise)
            applied_filters.append(f"Noise {sigma}")

        return result, applied_filters