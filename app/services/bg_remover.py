
import base64
import io

from PIL import Image

from rembg import remove


def remove_background_service(file):

    input_image = Image.open(file.stream)

    output_image = remove(input_image)

    buffer = io.BytesIO()

    output_image.save(buffer, format='PNG')

    img_base64 = base64.b64encode(
        buffer.getvalue()
    ).decode('utf-8')

    return {
        'success': True,
        'image': f'data:image/png;base64,{img_base64}'
    }