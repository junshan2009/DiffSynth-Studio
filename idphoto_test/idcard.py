# -*- coding: utf-8 -*-
"""
证件照单张出图（Z-Image 热服务客户端，真人感版）
模型由 server.py 常驻显存，本脚本只发请求、存图。

用法：
    conda activate aigc
    cd /home/bkg/pys/zimages
    python server.py --port 8129      # 另开窗口，等 ready
    python idcard.py                  # 出图到 out1/
"""

import base64
import io
import json
import os
import time
import urllib.request

from PIL import Image

SERVER = "http://127.0.0.1:8129"
OUT_DIR = "out1"

SEED = 2428
WIDTH, HEIGHT = 1024, 1408
CFG = 2          # 负向词要生效必须 >= 2
STEPS = 15

PROMPT = """证件照，正面免冠半身像，街边快照照相馆用机顶闪光灯直拍的证件照片，raw photo, unretouched, film grain。
人物端坐正对镜头，头颈正直不歪斜，双肩完全水平，双耳等高清晰可见，面部正对镜头，双眼平视镜头，表情平静自然放松，嘴唇自然闭合。
年轻亚洲女性，普通人的长相，自然的暖黄皮肤，不是冷白皮，脸颊鼻头有红润血色，肤色不均匀，额头略深。
皮肤真实粗糙：毛孔清晰可见，鼻头和鼻翼毛孔明显，T区出油有油光反光，脸颊有几颗淡淡的痘印和闭口，几颗小雀斑和一颗小痣，眼下有细纹和轻微黑眼圈，面部细小绒毛在光下可见，嘴唇有唇纹和轻微起皮。
skin pores, subtle blemishes, natural skin texture, slight oily shine, fine facial hair。
眉毛左右不对称，脸型轻微不对称，发际线有细碎绒毛。
黑色头发束起别在耳后，露出双耳，有少量碎发。
白色衬衫外穿深色西装外套，衣领平整，布料有真实织纹和轻微褶皱。
浅灰色背景。闪光灯直打，光线略硬，面部有真实的高光和轻微阴影，鼻下有淡影。
佳能单反85mm镜头，ISO 400，直出未修图，明显但自然的颗粒噪点。
构图到胸部以上，头顶留白。
hbch
"""

NEGATIVE_PROMPT = """磨皮，美颜，美妆滤镜，瓷娃娃皮肤，无瑕皮肤，皮肤过白，肤色惨白，过度美白，光滑无毛孔，塑料感，蜡像感，AI脸，3d render，CGI，过度锐化，过饱和，歪头，头部倾斜，侧脸，四分之三侧脸，高低肩，肩膀不对称，身体侧转，仰头，低头，模糊，畸形，画质差。"""

payload = {
    "prompt": PROMPT,
    "negative_prompt": NEGATIVE_PROMPT,
    "seed": SEED,
    "rand_device": "cuda",
    "width": WIDTH,
    "height": HEIGHT,
    "cfg_scale": CFG,
    "num_inference_steps": STEPS,
}
data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(SERVER + "/generate", data=data,
                             headers={"Content-Type": "application/json"},
                             method="POST")

t0 = time.time()
with urllib.request.urlopen(req, timeout=1800) as resp:
    result = json.loads(resp.read().decode("utf-8"))

image = Image.open(io.BytesIO(base64.b64decode(result["image_base64"]))).convert("RGB")

os.makedirs(OUT_DIR, exist_ok=True)
png_path = os.path.join(OUT_DIR, "idcard_%s_%s_%s.png" % (SEED, int(CFG * 10), STEPS))
txt_path = os.path.join(OUT_DIR, "idcard_%s_jiance.txt" % SEED)
image.save(png_path)
with open(txt_path, "w", encoding="utf-8") as f:
    f.write("Positive Prompt:\n")
    f.write(PROMPT)
    f.write("\n\nNegative Prompt:\n")
    f.write(NEGATIVE_PROMPT)

print("图片已保存：", os.path.abspath(png_path))
print("提示词已保存：", os.path.abspath(txt_path))
print("生成耗时: %.2f 秒" % (time.time() - t0))