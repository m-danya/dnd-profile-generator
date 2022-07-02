from flask import Flask, request, redirect, url_for
from base64 import decode
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid
from PIL import Image
import json

UPLOAD_FOLDER = Path('uploads')  # TODO: move somewhere
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 Mb


def allowed_file(filename):
    if filename is None:
        return False
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_extension(filename):
    return filename.rsplit('.', 1)[1].lower()


def save_image_from_request(img):
    file = request.files.get(img, None)
    if not allowed_file(file.filename):
        return
    filepath = f'{str(uuid.uuid4())}.{get_extension(file.filename)}'
    filepath = UPLOAD_FOLDER / filepath
    file.save(filepath)
    return filepath


def cut_image_inplace(img_path: Path, params: dict):
    print(img_path, params)
    img = Image.open(img_path)
    scale = float(params['scale'])
    x = scale * params['crop']['x']
    y = scale * params['crop']['y']
    width = scale * params['crop']['width']
    height = scale * params['crop']['height']
    x_2 = x + width
    y_2 = y + height

    img = img.crop((x, y, x_2, y_2))
    img.show()
    img.save(img_path)


@app.route("/process", methods=["POST"])
def process():
    images_params = {
        'original_background_image': {
            'aspect': request.form.get("background_aspect"),
            'crop': json.loads(request.form.get("background_crop")),
            'scale': request.form.get("background_scale"),

        },
        'original_avatar_image': {
            'aspect': request.form.get("avatar_aspect"),
            'crop': json.loads(request.form.get("avatar_crop")),
            'scale': request.form.get("avatar_scale"),
        }
    }

    uploaded_images = {
        img_name: save_image_from_request(img_name)
        for img_name in images_params
    }
    print(uploaded_images)
    for img_name in uploaded_images:
        cut_image_inplace(uploaded_images[img_name], images_params[img_name])
    return "ok"


if __name__ == "__main__":
    app.run(debug=True, port=8000)
