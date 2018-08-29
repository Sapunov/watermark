from tqdm import tqdm
import argparse
import math
import os

from PIL import Image, ImageDraw, ImageFont, TiffImagePlugin


# Для перевода процентов в значение от 0 до 255
OPACITY_COEF = 2.55

WHITE = 255
FULL_TRANSPARENT = 0

PNG = "PNG"
JPG = "JPG"
JPEG = "JPEG"
TIFF = "TIFF"
TIF = "TIF"
ALLOWED_FORMATS = tuple(item.lower() for item in (PNG, JPEG, JPG, TIFF, TIF))



class UnsupportedFileExtension(Exception):

    pass


class DirectoryMatching(Exception):

    pass


def calc_num_per_line(line_width, text_width):
    """Вычисляет количество текстов заданной длины в строке"""

    return int(math.ceil(line_width / text_width))


def get_center_box(outer_w, outer_h, inner_w, inner_h):
    """Вычисляет границы точно в центре"""

    x = int(outer_w / 2 - inner_w / 2)
    y = int(outer_h / 2 - inner_h / 2)

    return x, y, x + inner_w, y + inner_h


def cyclic_shift(string, n_chars=10, offset=0):
    """Циклический сдвиг строки"""

    offset_chars = (offset * n_chars) % len(string)

    return string[offset_chars:] + string[:offset_chars]


def watermark_image(image_obj, text, font_file, angle=45,
                    text_opacity=20, fill_color=220, fontsize=50,
                    padding=200, space_interval=10):

    image_obj = image_obj.convert("RGBA")

    wrapper_side = max(image_obj.size)

    font = ImageFont.truetype(font_file, fontsize)
    text_w, text_h = font.getsize(text)

    space = " " * space_interval

    linetext = space + space.join(text for _ in range(calc_num_per_line(wrapper_side, text_w)))
    line_w, line_h = font.getsize(linetext)

    line_h_with_padding = line_h + padding * 2

    num_of_lines = int(math.ceil(wrapper_side / line_h_with_padding))

    wrapper_w = line_w
    wrapper_h = line_h_with_padding * num_of_lines

    watermark_layer = Image.new(
        "RGBA", (wrapper_w, wrapper_h), (WHITE, WHITE, WHITE, FULL_TRANSPARENT))
    watermark_layer_draw = ImageDraw.Draw(watermark_layer)

    opacity = int(text_opacity * OPACITY_COEF)
    opacity = opacity if opacity <= 100 else opacity

    for i in range(num_of_lines):
        watermark_layer_draw.text(
            (0, i * line_h_with_padding),
            cyclic_shift(linetext, 10, i),
            font=font,
            fill=(fill_color, fill_color, fill_color, opacity)
        )

    watermark_layer = watermark_layer.rotate(angle)

    watermark_layer = watermark_layer.crop(
        get_center_box(
            wrapper_w, wrapper_h, image_obj.width, image_obj.height))

    return Image.alpha_composite(image_obj, watermark_layer).convert("RGB")


def watermark_file(input_file, output_file, text, font_file, **kwargs):

    original = Image.open(input_file)

    # Обработка параметров
    quality = kwargs.pop("quality")
    compress = kwargs.pop("compress")
    resize = kwargs.pop("resize")

    if original.format == TIFF:
        with TiffImagePlugin.AppendingTiffWriter(output_file, True) as tif:
            for i in range(original.n_frames):
                original.seek(i)

                out = watermark_image(original, text, font_file, **kwargs)

                compression = "jpeg" if compress else "None"

                if resize:
                    xs, ys = out.size
                    ratio = resize / xs
                    out.thumbnail((xs * ratio, ys * ratio), Image.ANTIALIAS)

                out.save(tif, compression=compression, quality=quality)
                tif.newFrame()
    elif original.format in (PNG, JPG, JPEG):
        out = watermark_image(original, text, font_file, **kwargs)
        out.save(output_file, quality=quality)
    else:
        raise UnsupportedFileExtension(
            "Format {0} not supported".format(original.format))


def replace_two_slash(name):

    return name.replace(os.path.sep + os.path.sep, os.path.sep)


def find_images_recursively(folder):

    images = []

    for directory, dirs, files in os.walk(folder):
        for filename in files:
            name, ext = os.path.splitext(filename)
            if ext[1:].lower() in ALLOWED_FORMATS:
                filename = os.path.join(directory, filename)
                images.append(filename)

    return images


def create_output_file(filename, input_folder, output_folder):

    input_folder = input_folder.rstrip(os.path.sep)
    filename = filename.replace(input_folder, "").strip(os.path.sep)

    target = os.path.join(output_folder, filename)

    # Воссоздадим иерархию папок как в источнике
    dest_folder, _ = os.path.split(target)
    os.makedirs(dest_folder, exist_ok=True)

    return target


def main():

    parser = argparse.ArgumentParser(description="Create image with text watermark")
    parser.add_argument("-i", "--input",
                        help="Input file or directory",
                        required=True,
                        type=str)
    parser.add_argument("-o", "--output",
                        help="Output file or directory",
                        required=True,
                        type=str)
    parser.add_argument("-t", "--text",
                        help="Text for watermark",
                        required=True,
                        type=str)
    parser.add_argument("--font",
                        help="Font filename",
                        required=True,
                        type=str)
    parser.add_argument("--quality",
                        help="JPEG compression quality",
                        type=int,
                        default=100)
    parser.add_argument("--compress",
                        help="Whether enable JPEG compression. For TIFF only",
                        action="store_true")
    parser.add_argument("--resize",
                        help="Resize and specify longest side",
                        type=int,
                        default=None)
    parser.add_argument("--angle", help="Text angle", type=int, default=45)
    parser.add_argument("--text_opacity", help="Text opacity", type=int, default=20)
    parser.add_argument("--fill_color", help="Fill color. RGB digit", type=int, default=220)
    parser.add_argument("--fontsize", help="Font size", type=int, default=50)
    parser.add_argument("--padding", help="Text padding", type=int, default=200)
    parser.add_argument("--space_interval", help="Text interval", type=int, default=10)

    args = parser.parse_args()

    args.input = replace_two_slash(args.input)
    args.output = replace_two_slash(args.output)

    if os.path.isdir(args.input):
        if not os.path.isdir(args.output):
            raise DirectoryMatching("If input is a directory output MUST be a directory")

        images_to_watermark = find_images_recursively(args.input)

        if input("There are {0} images to watermark. " \
                 "Do you want to continue?(y|N): ".format(
                     len(images_to_watermark))).lower() == "y":
            for i in tqdm(range(len(images_to_watermark))):
                watermark_file(
                    images_to_watermark[i],
                    create_output_file(images_to_watermark[i], args.input, args.output),
                    args.text,
                    args.font,
                    quality=args.quality,
                    compress=args.compress,
                    angle=args.angle,
                    text_opacity=args.text_opacity,
                    fill_color=args.fill_color,
                    fontsize=args.fontsize,
                    padding=args.padding,
                    space_interval=args.space_interval,
                    resize=args.resize)
    else:
        watermark_file(
            args.input,
            args.output,
            args.text,
            args.font,
            quality=args.quality,
            compress=args.compress,
            angle=args.angle,
            text_opacity=args.text_opacity,
            fill_color=args.fill_color,
            fontsize=args.fontsize,
            padding=args.padding,
            space_interval=args.space_interval)


if __name__ == "__main__":

    main()
