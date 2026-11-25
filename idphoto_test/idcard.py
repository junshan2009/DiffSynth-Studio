# -*- coding: utf-8 -*-
"""
证件照单张出图（Z-Image 热服务客户端）
=====================================
默认参数与 out1/idcard_2428_20_15_real4.png（真人感优化版）完全一致：
    seed=2428, 1024x1408, cfg_scale=2, steps=15
真人感要点：暖黄肤色+毛孔/油光/泛红/痘印等具体皮肤细节+RAW直出颗粒感；
负向词压磨皮美颜，cfg 必须 >=2 负向词才生效。

模型由 server.py 常驻显存，本脚本只发请求、存图，不加载模型。

用法（服务端 zimages 目录下）：
    conda activate aigc
    cd /home/bkg/pys/zimages
    python server.py --port 8129      # 另开一个窗口，等它 ready
    python idcard.py                  # 默认参数，出图到 out1/
    python idcard.py --seed 3001 --out out1
    python idcard.py --width 1200 --height 1680 --cfg 1

输出：
    out1/idcard_{seed}_{cfg*10}_{steps}.png
    out1/idcard_{seed}_jiance.txt        正/负提示词
"""

import argparse
import base64
import io
import json
import os
import time
import urllib.error
import urllib.request

from PIL import Image

DEFAULT_SERVER = "http://127.0.0.1:8129"

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


def generate(server, prompt, negative_prompt, seed, width, height, cfg, steps, timeout):
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "seed": seed,
        "rand_device": "cuda",
        "width": width,
        "height": height,
        "cfg_scale": cfg,
        "num_inference_steps": steps,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        server.rstrip("/") + "/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read().decode("utf-8"))
    if not resp.get("ok"):
        raise RuntimeError("服务端返回失败: %s" % str(resp)[:500])
    return Image.open(io.BytesIO(base64.b64decode(resp["image_base64"]))).convert("RGB"), resp


def main():
    ap = argparse.ArgumentParser(description="证件照出图（复用 server.py 热模型）")
    ap.add_argument("--server", default=DEFAULT_SERVER)
    ap.add_argument("--out", default="out1")
    ap.add_argument("--seed", type=int, default=2428)
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=1408)
    ap.add_argument("--cfg", type=float, default=2)
    ap.add_argument("--steps", type=int, default=15)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--prompt-file", default=None, help="用文件内容覆盖正向提示词")
    ap.add_argument("--neg-file", default=None, help="用文件内容覆盖负向提示词")
    ap.add_argument("--tag", default=None, help="输出文件名后缀标记")
    args = ap.parse_args()

    prompt = PROMPT
    negative_prompt = NEGATIVE_PROMPT
    if args.prompt_file:
        prompt = open(args.prompt_file, encoding="utf-8").read().strip() + "\n"
    if args.neg_file:
        negative_prompt = open(args.neg_file, encoding="utf-8").read().strip()

    os.makedirs(args.out, exist_ok=True)

    # 先确认热服务在线，避免请求挂住
    try:
        with urllib.request.urlopen(args.server.rstrip("/") + "/health", timeout=10) as r:
            info = json.loads(r.read().decode("utf-8"))
        print("[idcard] server ready: lora=%s alpha=%s, gpu=%s"
              % (os.path.basename(info["base_lora"]["path"]), info["base_lora"]["alpha"],
                 (info.get("gpu") or {}).get("name")))
    except Exception as e:
        print("[idcard] 连不上服务端 %s ：%s" % (args.server, e))
        print("[idcard] 请先在 zimages 目录启动： python server.py --port 8129")
        raise SystemExit(1)

    t0 = time.time()
    image, resp = generate(args.server, prompt, negative_prompt, args.seed,
                           args.width, args.height, args.cfg, args.steps, args.timeout)
    secs = time.time() - t0

    tag = "_" + args.tag if args.tag else ""
    png_path = os.path.join(args.out, "idcard_%s_%s_%s%s.png"
                            % (args.seed, str(int(args.cfg * 10)), args.steps, tag))
    txt_path = os.path.join(args.out, "idcard_%s%s_jiance.txt" % (args.seed, tag))
    image.save(png_path)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("Positive Prompt:\n")
        f.write(prompt)
        f.write("\n\nNegative Prompt:\n")
        f.write(negative_prompt)
        f.write("\n\nseed=%s  %dx%d  cfg=%s  steps=%s\n"
                % (args.seed, args.width, args.height, args.cfg, args.steps))

    print("[idcard] %.1fs -> %s" % (secs, png_path))
    print("[idcard] 提示词 -> %s" % txt_path)


if __name__ == "__main__":
    main()