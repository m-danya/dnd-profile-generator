from flask import Flask, request, redirect, url_for, send_from_directory
from base64 import decode
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid
from PIL import Image
import json

UPLOAD_FOLDER = Path("uploads")  # TODO: move somewhere
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 Mb


def allowed_file(filename):
    if filename is None:
        return False
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def get_extension(filename):
    return filename.rsplit(".", 1)[1].lower()


def save_image_from_request(img):
    file = request.files.get(img, None)
    if not allowed_file(file.filename):
        return
    filepath = f"{str(uuid.uuid4())}.{get_extension(file.filename)}"
    filepath = UPLOAD_FOLDER / filepath
    file.save(filepath)
    return filepath


def cut_image_inplace(img_path: Path, params: dict):
    img = Image.open(img_path)
    scale = float(params["scale"])
    x = scale * params["crop"]["x"]
    y = scale * params["crop"]["y"]
    width = int(scale * params["crop"]["width"])
    height = int(scale * params["crop"]["height"])
    x_2 = x + width
    y_2 = y + height
    img = img.crop((x, y, x_2, y_2))

    params["width"] = width
    params["height"] = height

    img.save(img_path)
    img.close()


@app.route("/process", methods=["POST"])
def process():
    images_params = {
        "background_image": {
            "aspect": request.form.get("background_aspect"),
            "crop": json.loads(request.form.get("background_crop")),
            "scale": request.form.get("background_scale"),
        },
        "avatar_image": {
            "aspect": request.form.get("avatar_aspect"),
            "crop": json.loads(request.form.get("avatar_crop")),
            "scale": request.form.get("avatar_scale"),
        },
    }

    uploaded_images = {
        img_name: save_image_from_request("original_" + img_name)
        for img_name in images_params
    }
    for img_name in uploaded_images:
        cut_image_inplace(uploaded_images[img_name], images_params[img_name])
    printout_filename = make_the_printout(uploaded_images, images_params)
    clean_the_images(uploaded_images)
    return send_from_directory(UPLOAD_FOLDER, printout_filename)


def make_the_printout(images, images_params):
    bg_width = images_params["background_image"]["width"]
    bg_height = images_params["background_image"]["height"]
    white_height = bg_height // 2
    image_height = bg_height * 2 + white_height + int(bg_height * 0.2)
    printout = Image.new("RGBA", (bg_width, image_height), (255, 255, 255))
    with Image.open(images["background_image"]) as background:
        reversed_background = background.transpose(
            Image.Transpose.FLIP_TOP_BOTTOM
        )
        printout.paste(reversed_background, (0, 0))
        printout.paste(background, (0, bg_height))
        printout.paste(reversed_background, (0, 2 * bg_height + white_height))
    with Image.open(images["avatar_image"]) as avatar:
        # TODO: deal with transparency?
        avatar_size = int(bg_width // 4)
        avatar = avatar.resize((avatar_size, avatar_size))
        printout.paste(
            avatar,
            (
                bg_width - avatar_size // 10 - avatar_size,
                int(bg_height + avatar_size // 10),
            ),
        )

    filepath = f"{str(uuid.uuid4())}.png"
    filepath = UPLOAD_FOLDER / filepath
    printout.save(filepath, "PNG")
    return filepath.name


def clean_the_images(uploaded_images):
    # TODO: clean the images even if there were some errors during processing
    for img_name in uploaded_images:
        uploaded_images[img_name].unlink()  # remove the file


if __name__ == "__main__":
    app.run(debug=True, port=8000)
