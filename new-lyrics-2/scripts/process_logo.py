import os, io, base64
from PIL import Image
import numpy as np

src_path = r'C:\Users\rudra\.gemini\antigravity-ide\brain\77ce9fc2-fee5-4943-bd8e-68d4f493f3b7\.user_uploaded\media_1789583411148.png'
im = Image.open(src_path)
arr = np.array(im)

alpha = arr[:, :, 3].copy()
# Clean noise
alpha[alpha <= 3] = 0

mask = alpha > 10
ys, xs = np.where(mask)
crop_box = (int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1))
print('Exact crop box:', crop_box, 'Dimensions:', crop_box[2] - crop_box[0], crop_box[3] - crop_box[1])

alpha_cropped = alpha[crop_box[1]:crop_box[3], crop_box[0]:crop_box[2]]
h, w = alpha_cropped.shape

# 1. White Transparent Logo (Solid White #FFFFFF with alpha channel)
white_arr = np.zeros((h, w, 4), dtype=np.uint8)
white_arr[:, :, 0] = 255
white_arr[:, :, 1] = 255
white_arr[:, :, 2] = 255
white_arr[:, :, 3] = alpha_cropped
white_im = Image.fromarray(white_arr)
white_im.save('public/yt_music_logo_white.png')

# 2. Black Transparent Logo (Solid Black #000000 with alpha channel)
black_arr = np.zeros((h, w, 4), dtype=np.uint8)
black_arr[:, :, 0] = 0
black_arr[:, :, 1] = 0
black_arr[:, :, 2] = 0
black_arr[:, :, 3] = alpha_cropped
black_im = Image.fromarray(black_arr)
black_im.save('public/yt_music_logo_black.png')

# 3. Grey Transparent Logo (#EBEBEB with alpha channel)
grey_arr = np.zeros((h, w, 4), dtype=np.uint8)
grey_arr[:, :, 0] = 235
grey_arr[:, :, 1] = 235
grey_arr[:, :, 2] = 235
grey_arr[:, :, 3] = (alpha_cropped.astype(float) * 0.92).astype(np.uint8)
grey_im = Image.fromarray(grey_arr)
grey_im.save('public/yt_music_logo_grey.png')

def to_b64(img):
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')

b64_white = to_b64(white_im)
b64_black = to_b64(black_im)

svg_white = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <image width="{w}" height="{h}" xlink:href="data:image/png;base64,{b64_white}" />
</svg>'''

svg_black = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <image width="{w}" height="{h}" xlink:href="data:image/png;base64,{b64_black}" />
</svg>'''

with open('public/yt_music_logo_white.svg', 'w', encoding='utf-8') as f:
    f.write(svg_white)

with open('public/yt_music_logo_black.svg', 'w', encoding='utf-8') as f:
    f.write(svg_black)

print('Generated 908x166 transparent PNGs and SVGs directly from the uploaded asset!')
