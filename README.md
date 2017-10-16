# WATERMARK

Утилита для проставления текстовых водяных знаков

```{r, engine='bash'}
$ python watermark.py --help
usage: watermark.py [-h] -i INPUT -o OUTPUT -t TEXT --font FONT
                    [--quality QUALITY] [--compress] [--angle ANGLE]
                    [--text_opacity TEXT_OPACITY] [--fill_color FILL_COLOR]
                    [--fontsize FONTSIZE] [--padding PADDING]
                    [--space_interval SPACE_INTERVAL]

Create image with text watermark

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input file or directory
  -o OUTPUT, --output OUTPUT
                        Output file or directory
  -t TEXT, --text TEXT  Text for watermark
  --font FONT           Font filename
  --quality QUALITY     JPEG compression quality
  --compress            Whether enable JPEG compression. For TIFF only
  --angle ANGLE         Text angle
  --text_opacity TEXT_OPACITY
                        Text opacity
  --fill_color FILL_COLOR
                        Fill color. RGB digit
  --fontsize FONTSIZE   Font size
  --padding PADDING     Text padding
  --space_interval SPACE_INTERVAL
                        Text interval
```