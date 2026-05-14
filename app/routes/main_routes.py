
from flask import (
    Blueprint,
    render_template,
    request,
    jsonify
)

from app.services.bg_remover import remove_background_service

from app.models import ImageHistory

main = Blueprint('main', __name__)


# =========================
# Home Route
# =========================

@main.route('/')
def home():

    return render_template('index.html')


# =========================
# Remove Background API
# =========================

@main.route('/remove-bg', methods=['POST'])
def remove_bg():

    if 'image' not in request.files:

        return jsonify({
            'error': 'No image uploaded'
        }), 400

    file = request.files['image']

    result = remove_background_service(file)

    return jsonify(result)


# =========================
# History API
# =========================

@main.route('/history')
def history():

    images = ImageHistory.query.order_by(
        ImageHistory.created_at.desc()
    ).all()

    data = []

    for image in images:

        data.append({

            'id': image.id,

            'image_url': image.image_url,

            'created_at': image.created_at.strftime(
                '%Y-%m-%d %H:%M'
            )

        })

    return jsonify(data)
