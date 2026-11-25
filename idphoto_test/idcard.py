# -*- coding: utf-8 -*-
"""
证件照单张出图（Z-Image 热服务客户端）
=====================================
默认参数与 out1/test_4_idphoto_cfg2.png 完全一致：
    seed=2428, 1024x1408, cfg_scale=2, steps=15

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

PROMPT = """证件照，正面免冠半身人像，标准二寸证件照，人物端坐，身体正对镜头。
头颈正直，头部没有任何倾斜和歪斜，鼻尖朝向正前方，两只耳朵在同一高度，双肩完全水平，左右对称，面部完整正对镜头。
年轻亚洲女性，表情平静自然，嘴唇自然闭合，双眼平视镜头，眼睛看向正前方镜头，不向左也不向右。
黑色头发整齐梳起，头发别在耳后，两侧耳朵清晰可见，没有散落的碎发，不佩戴饰品。
身穿白色衬衫和深色西装外套，衣领平整对称。
均匀柔和的证件照布光，正面打光，面部受光均匀，没有明显阴影。
真实皮肤质感，可见细腻毛孔与自然肤色，单反相机拍摄，照片级真实，非AI塑料感。
纯浅灰色背景，纯色、平整、无渐变。头顶留白，锁骨以下自然裁切。
hbch
"""

NEGATIVE_PROMPT = """歪头，头部倾斜，侧脸，四分之三侧脸，身体侧转，耸肩，高低肩，肩膀不对称，仰头，低头，扭曲的脖子，AI脸，塑料感，蜡像感，过度磨皮，过饱和，3d render，CGI，模糊，畸形，画质差。"""


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
    args = ap.parse_args()

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
    image, resp = generate(args.server, PROMPT, NEGATIVE_PROMPT, args.seed,
                           args.width, args.height, args.cfg, args.steps, args.timeout)
    secs = time.time() - t0

    png_path = os.path.join(args.out, "idcard_%s_%s_%s.png"
                            % (args.seed, str(int(args.cfg * 10)), args.steps))
    txt_path = os.path.join(args.out, "idcard_%s_jiance.txt" % args.seed)
    image.save(png_path)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("Positive Prompt:\n")
        f.write(PROMPT)
        f.write("\n\nNegative Prompt:\n")
        f.write(NEGATIVE_PROMPT)
        f.write("\n\nseed=%s  %dx%d  cfg=%s  steps=%s\n"
                % (args.seed, args.width, args.height, args.cfg, args.steps))

    print("[idcard] %.1fs -> %s" % (secs, png_path))
    print("[idcard] 提示词 -> %s" % txt_path)


if __name__ == "__main__":
    main()