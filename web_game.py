# -*- coding: utf-8 -*-
import random
import textwrap
import math
import os
from flask import Flask, session, render_template_string, request, redirect, url_for

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 遊戲數據...
MORTAL_REALM_DATA = {"levels": list(range(1, 11)), "xp_per_level": 100, "xp_multiplier": 1.2, "lifespan_gain": 5}
CONSTITUTION_DATA = {"氣運之子": {"desc": "受此方天地眷顧..."}, "先天道胎": {"desc": "為法術而生的體質..."}, "荒古聖體": {"desc": "為戰鬥而生的霸道體質..."}}
MORTAL_MONSTERS = {"鐵爪山豬": {"stats": {"氣血": 80, "肉身強度": 15, "速度": 5}, "drops": {"生鐵獠牙": 0.7, "糙皮": 0.5}, "xp": 10}}
LOCATION_DATA = {
    "青石鎮": {"type": "城鎮", "desc": "坐落於青雲山脈腳下...", "travel_to": ["青雲山脈"]},
    "青雲山脈": {"type": "地圖", "desc": "綿延數百里...", "travel_to": ["青石鎮"]}
}

class Player:
    def __init__(self, name, gender):
        self.name = name
        self.gender = gender
        self.realm = "凡人"
        self.level = 1
        self.xp = 0
        self.max_xp = MORTAL_REALM_DATA["xp_per_level"]
        self.lifespan = random.randint(60, 80)
        self.constitution = None
        self.stats = {"氣血": 100, "最大氣血": 100, "法力": 5, "肉身強度": 5, "速度": 5, "防禦": 0}
        self.inventory = {}
        self.location = "青石鎮"
        self.in_combat = False
        self.combat_target = None

    def to_dict(self): return self.__dict__
    @classmethod
    def from_dict(cls, data):
        player = cls(data['name'], data['gender']); player.__dict__.update(data); return player
    def add_item(self, item_name, quantity=1): self.inventory[item_name] = self.inventory.get(item_name, 0) + quantity
    def add_xp(self, amount):
        if self.level >= 10: return "修為已達凡人境巔峰。"
        self.xp += amount; log_msg = f"修為增加了 {amount} 點。"
        while self.xp >= self.max_xp and self.level < 10:
            self.xp -= self.max_xp; self.level += 1; self.lifespan += MORTAL_REALM_DATA["lifespan_gain"]
            self.max_xp = math.ceil(self.max_xp * MORTAL_REALM_DATA["xp_multiplier"])
            self.stats["最大氣血"] += 10; self.stats["法力"] += 1; self.stats["肉身強度"] += 1
            self.stats["氣血"] = self.stats["最大氣血"]
            log_msg += f" 恭喜！你提升到了【凡人 {self.level} 層】！"
        return log_msg

HTML_TEMPLATE = """
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>文字修仙 MUD</title>
<style>body{font-family:sans-serif;background-color:#1a1a1a;color:#e0e0e0;margin:0;padding:15px;}.container{max-width:600px;margin:0 auto;background-color:#2b2b2b;border:1px solid #444;border-radius:8px;padding:20px;}h1,h2{color:#f0c674;text-align:center;border-bottom:1px solid #555;padding-bottom:10px;}.log{background-color:#111;border:1px solid #333;padding:15px;margin-bottom:20px;border-radius:5px;max-height:200px;overflow-y:auto;}.log p{margin:0 0 8px 0;}.status-panel{display:grid;grid-template-columns:1fr 1fr;gap:10px;background-color:#333;padding:15px;border-radius:5px;margin-bottom:20px;}.actions{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;}.btn{background-color:#5a5a5a;color:#e0e0e0;border:1px solid #777;padding:12px;width:100%;border-radius:5px;font-size:16px;cursor:pointer;}.btn-danger{background-color:#8c3826;}a{color:#f0c674;}.char-creation{text-align:center;}input{width:80%;padding:10px;margin:10px 0;border-radius:5px;border:1px solid #555;background-color:#333;color:#e0e0e0;}</style>
</head><body><div class="container"><h1>文字修仙 MUD</h1>
{% if player %}<h2>{{ player.name }} - {{ player.location }}</h2><div class="log">
{% for message in game_log %}<p>{{ message }}</p>{% else %}<p>仙路漫漫，請開始你的行動...</p>{% endfor %}</div>
<div class="status-panel"><div>境界: {{ player.realm }} {{ player.level }} 層</div><div>壽元: {{ player.lifespan }} 年</div><div>氣血: {{ player.stats.氣血 }}/{{ player.stats.最大氣血 }}</div><div>修為: {{ player.xp }}/{{ player.max_xp }}</div></div>
<div class="actions">{% if not player.in_combat %}<form action="/action" method="post"><button class="btn"