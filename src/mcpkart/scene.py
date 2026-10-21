"""Factual egocentric road drawings, with no predicted path or chosen control."""

from __future__ import annotations

import base64
import bisect
import io
import math
from functools import lru_cache

SIZE, SCALE = 384, 6
ORIGIN = (192, 288)


@lru_cache(maxsize=16)
def geometry(points: tuple) -> tuple:
    lengths, headings = [0.0], []
    for a, b in zip(points, points[1:] + points[:1]):
        lengths.append(lengths[-1] + math.dist(a, b))
    for i in range(len(points)):
        a, b = points[(i-1) % len(points)], points[(i+1) % len(points)]
        headings.append(math.atan2(b[1]-a[1], b[0]-a[0]))
    return lengths, headings


def scene_geometry(observation: dict, config: dict) -> dict:
    points = tuple(tuple(p) for p in config["track"]["points"])
    lengths, headings = geometry(points)
    kart = observation["kart"]
    cosine, sine = math.cos(kart["heading"]), math.sin(kart["heading"])

    def pixel(x, y):
        dx, dy = x-kart["x"], y-kart["y"]
        forward, left = dx*cosine+dy*sine, -dx*sine+dy*cosine
        return round(ORIGIN[0]-left*SCALE, 2), round(ORIGIN[1]-forward*SCALE, 2)

    centre, left_edge, right_edge = [], [], []
    half_width = config["track"]["width"]/2
    for i in range(37):
        distance = (observation["progress"]["track_distance"] - 8 + i*1.5) % lengths[-1]
        index = min(len(points)-1, bisect.bisect_right(lengths, distance)-1)
        fraction = (distance-lengths[index])/(lengths[index+1]-lengths[index])
        a, b = points[index], points[(index+1) % len(points)]
        x, y = a[0]+fraction*(b[0]-a[0]), a[1]+fraction*(b[1]-a[1])
        delta = (headings[(index+1) % len(points)]-headings[index]+math.pi) % (2*math.pi)-math.pi
        heading = headings[index]+fraction*delta
        nx, ny = -math.sin(heading)*half_width, math.cos(heading)*half_width
        centre.append(pixel(x,y))
        left_edge.append(pixel(x+nx,y+ny))
        right_edge.append(pixel(x-nx,y-ny))
    checkpoints = config["track"].get("checkpoints", [])
    index = observation["progress"]["checkpoint"]
    gate = checkpoints[index] if 0 <= index < len(checkpoints) else None
    candidate = observation.get("next_checkpoint", {})
    if gate is None and all(k in candidate for k in ("x", "y", "forward_heading")):
        gate = {"x":candidate["x"],"y":candidate["y"],"heading":candidate["forward_heading"]}
    gate_line = []
    if gate is not None:
        nx, ny = -math.sin(gate["heading"])*half_width, math.cos(gate["heading"])*half_width
        gate_line = [pixel(gate["x"]+nx,gate["y"]+ny), pixel(gate["x"]-nx,gate["y"]-ny)]
    velocity = (round(ORIGIN[0]-(-kart["vx"]*sine+kart["vy"]*cosine)*.5*SCALE,2),
                round(ORIGIN[1]-(kart["vx"]*cosine+kart["vy"]*sine)*.5*SCALE,2))
    return {"left":left_edge,"right":right_edge,"centre":centre,"gate":gate_line,
            "velocity":[ORIGIN,velocity],"kart":[(192,276),(184,299),(200,299)]}


def scene_svg(scene: dict) -> str:
    def coords(points):
        return " ".join(f"{x:g},{y:g}" for x,y in points)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" viewBox="0 0 {SIZE} {SIZE}">',
             '<rect width="384" height="384" fill="#193922"/>',
             f'<polygon points="{coords(scene["left"]+scene["right"][::-1])}" fill="#555555"/>']
    for side in ("left","right"):
        parts.append(f'<polyline points="{coords(scene[side])}" fill="none" stroke="white" stroke-width="3"/>')
    parts.extend([f'<polyline points="{coords(scene["centre"])}" fill="none" stroke="#bbbbbb" stroke-width="1" stroke-dasharray="7 7"/>',
                  f'<polyline points="{coords(scene["gate"])}" fill="none" stroke="#00eeee" stroke-width="4"/>',
                  f'<polyline points="{coords(scene["velocity"])}" fill="none" stroke="#0099ff" stroke-width="4"/>',
                  f'<polygon points="{coords(scene["kart"])}" fill="#ffff00"/>',
                  '<text x="10" y="18" fill="white" font-size="12">UP = NOSE; BLUE = VELOCITY; CYAN = NEXT GATE</text>',
                  '</svg>'])
    return "".join(parts)


def scene_png(scene: dict) -> bytes:
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (SIZE,SIZE), "#193922")
    draw = ImageDraw.Draw(image)
    draw.polygon(scene["left"]+scene["right"][::-1],fill="#555555")
    for side in ("left","right"):
        draw.line(scene[side],fill="white",width=3)
    for a,b in zip(scene["centre"][::2],scene["centre"][1::2]):
        draw.line([a,b],fill="#bbbbbb",width=1)
    if scene["gate"]:
        draw.line(scene["gate"],fill="#00eeee",width=4)
    draw.line(scene["velocity"],fill="#0099ff",width=4)
    draw.polygon(scene["kart"],fill="#ffff00")
    draw.text((8,8),"UP = NOSE; BLUE = VELOCITY; CYAN = NEXT GATE",fill="white")
    output = io.BytesIO()
    image.save(output,format="PNG")
    return output.getvalue()


def image_part(scene: dict) -> dict:
    encoded = base64.b64encode(scene_png(scene)).decode()
    return {"type":"image_url","image_url":{"url":"data:image/png;base64,"+encoded}}
