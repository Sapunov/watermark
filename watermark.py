import argparse
import math

from PIL import Image, ImageDraw, ImageFont, TiffImagePlugin


# Для перевода процентов в значение от 0 до 255
OPACITY_COEF = 2.55

WHITE = 255
FULL_TRANSPARENT = 0


class UnsupportedFileExtension(Exception):

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
                    text_opacity=20, fill_color=200, fontsize=50,
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

    watermark_layer = Image.new("RGBA", (wrapper_w, wrapper_h), (WHITE, WHITE, WHITE, FULL_TRANSPARENT))
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
    try:
        quality = kwargs.pop("quality")
    except KeyError:
        quality = 100

    if original.format == "TIFF":
        with TiffImagePlugin.AppendingTiffWriter(output_file, True) as tif:
            for i in range(original.n_frames):
                original.seek(i)

                #
                # Вот тут можно компрессию если надо
                #
                out = watermark_image(original, text, font_file, **kwargs)

                out.save(tif)
                tif.newFrame()
    elif original.format in ("PNG", "JPG", "JPEG"):
        out = watermark_image(original, text, font_file, **kwargs)
        out.save(output_file, quality=quality)
    else:
        raise UnsupportedFileExtension(
            "Format {0} not supported".format(original.format))


def main():

    parser = argparse.ArgumentParser(description="Create image with text watermark")
    parser.add_argument("-i", "--input", help="Input file or directory", required=True, type=str)
    parser.add_argument("-o", "--output", help="Output file or directory", required=True, type=str)
    parser.add_argument("-t", "--text", help="Text for watermark", required=True, type=str)
    parser.add_argument("--font", help="Font filename", required=True, type=str)

    args = parser.parse_args()

    watermark_file(args.input, args.output, args.text, args.font)


if __name__ == "__main__":

    main()
