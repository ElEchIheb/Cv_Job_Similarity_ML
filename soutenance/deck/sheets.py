import sys, glob
from PIL import Image
a, b = int(sys.argv[1]), int(sys.argv[2])
fs = [f'out/slides/slide_{i:02d}.png' for i in range(a, b + 1)]
W, H = 960, 540
for k in range(0, len(fs), 4):
    sheet = Image.new('RGB', (W * 2, H * 2), '#000')
    for j, f in enumerate(fs[k:k + 4]):
        im = Image.open(f).convert('RGB').resize((W, H), Image.LANCZOS); sheet.paste(im, ((j % 2) * W, (j // 2) * H))
    sheet.save(f'out/sheet_{a + k:02d}.jpg', quality=88); print(f'out/sheet_{a + k:02d}.jpg')
