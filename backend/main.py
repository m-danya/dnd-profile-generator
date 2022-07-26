from flask import Flask, request, redirect, url_for, send_from_directory
from base64 import decode
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid
from PIL import Image, ImageFont, ImageDraw
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
    # A4 at 300 DPI:
    paper_width = 2480
    paper_height = 3508
    bg_width = images_params["background_image"]["width"]
    bg_height = images_params["background_image"]["height"]
    with Image.open(images["background_image"]) as background:
        bg_width, bg_height = paper_width, round(
            bg_height * (paper_width / bg_width)
        )
        background = background.resize((bg_width, bg_height))
        background.save(images["background_image"])

    white_height = bg_height // 2
    image_height = bg_height * 2 + white_height + int(bg_height * 0.2)
    printout = Image.new("RGBA", (bg_width, image_height))
    with Image.open(images["background_image"]) as background:
        reversed_background = background.transpose(
            Image.Transpose.FLIP_TOP_BOTTOM
        )
        printout.paste(reversed_background, (0, 0))
        printout.paste(background, (0, bg_height))
        printout.paste(reversed_background, (0, 2 * bg_height + white_height))
    with Image.open("dark_mask.png") as dark_mask:
        dark_mask.resize((bg_width, bg_height))
        printout.paste(dark_mask, (0, bg_height), dark_mask)

    printout_draw = ImageDraw.Draw(printout)
    with Image.open(images["avatar_image"]) as avatar:
        # place the avatar image
        avatar_size = int(bg_width // 4)
        avatar = avatar.resize((avatar_size, avatar_size))
        radius = 30
        shift = 10
        avatar = add_corners(avatar, radius)

        left_top_x = bg_width - avatar_size // 8 - avatar_size
        left_top_y = bg_height + avatar_size // 8

        printout_draw.rounded_rectangle(
            (
                left_top_x - shift,
                left_top_y - shift,
                left_top_x + avatar_size + shift,
                left_top_y + avatar_size + shift,
            ),
            # outline="black",
            fill="orange",
            radius=radius,
            # width=10,
        )
        printout.paste(
            avatar,
            (
                left_top_x,
                left_top_y,
            ),
            avatar,  # use alpha channel as a mask
        )
    title_font = ImageFont.truetype("fonts/myriad-pro-semibold.ttf", 200)
    subtitle_font = ImageFont.truetype("fonts/myriad-pro-semibold.ttf", 80)
    stroke_width = 7
    printout_draw.text(
        (100, bg_height * 1.6),
        "Имя персонажа",
        (255, 255, 255),
        font=title_font,
        stroke_width=stroke_width,
        stroke_fill="black",
    )
    printout_draw.text(
        (100, bg_height * 1.77),
        "человек эльф | разбойник".upper(),
        (255, 255, 255),
        font=subtitle_font,
        stroke_width=stroke_width,
        stroke_fill="black",
    )
    filepath = f"{str(uuid.uuid4())}.png"
    filepath = UPLOAD_FOLDER / filepath
    printout.save(filepath, "PNG")
    return filepath.name


def clean_the_images(uploaded_images):
    # TODO: clean the images even if there were some errors during processing
    for img_name in uploaded_images:
        uploaded_images[img_name].unlink()  # remove the file


# from https://stackoverflow.com/questions/11287402/how-to-round-corner-a-logo-without-white-backgroundtransparent-on-it-using-pi
def add_corners(im, rad):
    circle = Image.new("L", (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new("L", im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im


if __name__ == "__main__":
    app.run(debug=True, port=8000)
