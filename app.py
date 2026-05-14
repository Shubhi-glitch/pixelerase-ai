import os
import io
import base64
import numpy as np
from flask import Flask, request, jsonify, render_template
from PIL import Image
import cv2
import urllib.request

app = Flask(__name__)

# =========================
# Config
# =========================

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

UPLOAD_FOLDER = os.path.join('static', 'uploads')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    'u2net.onnx'
)

MODEL_URL = (
    "https://github.com/danielgatis/rembg/"
    "releases/download/v0.0.0/u2net.onnx"
)

ort_session = None


# =========================
# Load AI Model
# =========================

def load_model():

    global ort_session

    if ort_session is not None:
        return True

    if not os.path.exists(MODEL_PATH):
        return False

    try:

        import onnxruntime as ort

        ort_session = ort.InferenceSession(MODEL_PATH)

        print("✅ Model loaded successfully")

        return True

    except Exception as e:

        print(f"❌ Model load error: {e}")

        return False


# =========================
# Normalize Image
# =========================

def normalize(
    img,
    mean=(0.485, 0.456, 0.406),
    std=(0.229, 0.224, 0.225)
):

    img = img / np.max(img) if np.max(img) > 0 else img

    img = (img - mean) / std

    return img.astype(np.float32)


# =========================
# AI Background Removal
# =========================

def remove_bg_onnx(pil_image):

    orig_w, orig_h = pil_image.size

    img = pil_image.convert("RGB").resize(
        (320, 320),
        Image.LANCZOS
    )

    img_np = np.array(img).astype(np.float32) / 255.0

    img_np = normalize(img_np)

    img_np = img_np.transpose(2, 0, 1)

    img_np = np.expand_dims(img_np, axis=0)

    input_name = ort_session.get_inputs()[0].name

    outputs = ort_session.run(
        None,
        {input_name: img_np}
    )

    mask = outputs[0][0][0]

    mask = (
        (mask - mask.min()) /
        (mask.max() - mask.min() + 1e-8)
    )

    mask = (mask * 255).astype(np.uint8)

    mask_pil = Image.fromarray(mask).resize(
        (orig_w, orig_h),
        Image.LANCZOS
    )

    mask_np = np.array(mask_pil)

    # Smooth Edges
    mask_np = cv2.GaussianBlur(mask_np, (5, 5), 0)

    _, mask_np = cv2.threshold(
        mask_np,
        40,
        255,
        cv2.THRESH_BINARY
    )

    mask_np = cv2.GaussianBlur(mask_np, (3, 3), 0)

    orig_np = np.array(
        pil_image.convert("RGBA")
    )

    orig_np[:, :, 3] = mask_np

    return Image.fromarray(orig_np, 'RGBA')


# =========================
# Fallback Method
# =========================

def remove_bg_grabcut(pil_image):

    img_cv = cv2.cvtColor(
        np.array(pil_image.convert("RGB")),
        cv2.COLOR_RGB2BGR
    )

    h, w = img_cv.shape[:2]

    mask = np.zeros((h, w), np.uint8)

    bgd_model = np.zeros((1, 65), np.float64)

    fgd_model = np.zeros((1, 65), np.float64)

    margin_x = int(w * 0.05)

    margin_y = int(h * 0.05)

    rect = (
        margin_x,
        margin_y,
        w - 2 * margin_x,
        h - 2 * margin_y
    )

    cv2.grabCut(
        img_cv,
        mask,
        rect,
        bgd_model,
        fgd_model,
        5,
        cv2.GC_INIT_WITH_RECT
    )

    mask2 = np.where(
        (mask == 2) | (mask == 0),
        0,
        255
    ).astype('uint8')

    mask2 = cv2.GaussianBlur(mask2, (5, 5), 0)

    orig_rgba = np.array(
        pil_image.convert("RGBA")
    )

    orig_rgba[:, :, 3] = mask2

    return Image.fromarray(orig_rgba, 'RGBA')


# =========================
# Home Page
# =========================

@app.route('/')
def index():

    return render_template('index.html')


# =========================
# Download Model
# =========================

@app.route('/download-model', methods=['POST'])
def download_model():

    try:

        urllib.request.urlretrieve(
            MODEL_URL,
            MODEL_PATH
        )

        load_model()

        return jsonify({
            'success': True,
            'message': 'Model downloaded successfully!'
        })

    except Exception as e:

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# =========================
# Model Status
# =========================

@app.route('/model-status')
def model_status():

    exists = os.path.exists(MODEL_PATH)

    if exists and ort_session is None:
        load_model()

    return jsonify({
        'ready': exists and ort_session is not None
    })


# =========================
# Remove Background API
# =========================

@app.route('/remove-bg', methods=['POST'])
def remove_background():

    if 'image' not in request.files:

        return jsonify({
            'error': 'No image uploaded'
        }), 400

    file = request.files['image']

    if file.filename == '':

        return jsonify({
            'error': 'No file selected'
        }), 400

    allowed = {
        'png',
        'jpg',
        'jpeg',
        'webp',
        'bmp'
    }

    ext = (
        file.filename.rsplit('.', 1)[-1].lower()
        if '.' in file.filename else ''
    )

    if ext not in allowed:

        return jsonify({
            'error': 'Unsupported file type'
        }), 400

    try:

        img_bytes = file.read()

        pil_image = Image.open(
            io.BytesIO(img_bytes)
        )

        result = None

        # AI Method
        if ort_session is not None:

            result = remove_bg_onnx(pil_image)

        else:

            result = remove_bg_grabcut(pil_image)

        # Convert Result
        output = io.BytesIO()

        result.save(output, format='PNG')

        output.seek(0)

        img_base64 = base64.b64encode(
            output.getvalue()
        ).decode('utf-8')

        return jsonify({

            'success': True,

            'image': (
                f'data:image/png;base64,{img_base64}'
            ),

            'method': (
                'ai'
                if ort_session is not None
                else 'grabcut'
            )

        })

    except Exception as e:

        return jsonify({
            'error': str(e)
        }), 500


# =========================
# Run App
# =========================

if __name__ == '__main__':

    load_model()

    app.run(debug=True, port=5000)