# -*- coding: utf-8 -*-
import random
import math
import os
from flask import Flask, session, render_template_string, request, redirect, url_for

# ====================
# Flask 設定
# ====================
app = Flask(__name__)
app.secret_key = os.urandom(24)

# ====================
# 核心資料
# ====================
MORTAL_REALM_DATA = {
    "levels": list(range(1, 11)),
    "xp_per_level": 100,
    "xp_multiplier": 1.2,
    "lifespan_gain_per_level": 5
}
CURRENCY_CONVERSION = {"中品靈石": 100, "下品靈石": 1}

# 技法（全部凡人境）
MORTAL_TECHNIQUES = {
    # 金系
    "銳金訣": {
        "系別": "金", "type": "法修",
        "skills": [
            {"name": "金戈術", "kind": "主動", "cost": {"靈力": 5},
             "desc": "凝聚一道鋒銳金屬刀刃攻擊敵人，造成（法力*1.5）傷害。",
             "func": lambda p: int(p.stats.get("法力", 0) * 1.5)}
        ]
    },
    "銅皮功": {
        "系別": "金", "type": "體修",
        "skills": [
            {"name": "銅皮", "kind": "被動", "effect": ("damage_reduction", 0.05),
             "desc": "受到的所有傷害永久降低5%。"}
        ]
    },
    "金石訣": {
        "系別": "金", "type": "雙修",
        "skills": [
            {"name": "金石之基", "kind": "被動", "effect": ("bonus_defense", 5), "desc": "防禦力永久+5。"},
            {"name": "金石之護", "kind": "主動", "cost": {"靈力": 5},
             "desc": "2回合內防禦+15。",
             "buff": {"防禦": 15, "turns": 2}}
        ]
    },
    # 木系
    "引氣訣": {
        "系別": "木", "type": "法修",
        "skills": [
            {"name": "回春術", "kind": "主動", "cost": {"靈力": 8},
             "desc": "恢復（法力*2）氣血。",
             "func": lambda p: int(p.stats.get("法力", 0) * 2)}
        ]
    },
    "枯木功": {
        "系別": "木", "type": "體修",
        "skills": [
            {"name": "生息", "kind": "被動", "effect": ("regen_hp_per_turn", 5),
             "desc": "每回合恢復5點氣血。"}
        ]
    },
    "草還丹訣": {
        "系別": "木", "type": "雙修",
        "skills": [
            {"name": "藥性通曉", "kind": "被動", "effect": ("heal_potion_bonus", 0.2),
             "desc": "恢復類丹藥效果+20%。"},
            {"name": "草木治癒", "kind": "主動", "cost": {"靈力": 8},
             "desc": "恢復（法力*1.5）氣血。",
             "func": lambda p: int(p.stats.get("法力", 0) * 1.5)}
        ]
    },
    # 水系
    "靜水訣": {
        "系別": "水", "type": "法修",
        "skills": [
            {"name": "水箭術", "kind": "主動", "cost": {"靈力": 5},
             "desc": "造成（法力*1.5）傷害。",
             "func": lambda p: int(p.stats.get("法力", 0) * 1.5)}
        ]
    },
    "疊浪功": {
        "系別": "水", "type": "體修",
        "skills": [
            {"name": "疊浪", "kind": "被動", "effect": ("stacking_damage", 2),
             "desc": "連續命中同一目標時，傷害每次+2。"}
        ]
    },
    "江河訣": {
        "系別": "水", "type": "雙修",
        "skills": [
            {"name": "氣息綿長", "kind": "被動", "effect": ("max_spirit_bonus", 20),
             "desc": "最大靈力永久+20。"},
            {"name": "細水長流", "kind": "主動", "cost": {"靈力": 3},
             "desc": "造成（法力*1.2）傷害，持久戰。", "func": lambda p: int(p.stats.get("法力", 0) * 1.2)}
        ]
    },
    # 火系
    "升火訣": {
        "系別": "火", "type": "法修",
        "skills": [
            {"name": "火球術", "kind": "主動", "cost": {"靈力": 5},
             "desc": "造成（法力*1.6）傷害。", "func": lambda p: int(p.stats.get("法力", 0) * 1.6)}
        ]
    },
    "淬火體": {
        "系別": "火", "type": "體修",
        "skills": [
            {"name": "淬火", "kind": "被動", "effect": ("bonus_damage", 3),
             "desc": "武術攻擊附加3點火焰傷害。"}
        ]
    },
    "炎陽訣": {
        "系別": "火", "type": "雙修",
        "skills": [
            {"name": "炎陽之體", "kind": "被動", "effect": ("day_xp_bonus", 0.1),
             "desc": "白日修煉獲得修為+10%。"},
            {"name": "陽炎擊", "kind": "主動", "cost": {"靈力": 5},
             "desc": "本次武術攻擊附加（法力*0.8）火焰傷害。", "func": lambda p: int(p.stats.get("法力", 0) * 0.8), "on_weapon": True}
        ]
    },
    # 土系
    "歸元訣": {
        "系別": "土", "type": "法修",
        "skills": [
            {"name": "凝元", "kind": "被動", "effect": ("max_spirit_bonus", 20),
             "desc": "最大靈力永久+20。"}
        ]
    },
    "磐石功": {
        "系別": "土", "type": "體修",
        "skills": [
            {"name": "磐石", "kind": "被動", "effect": ("bonus_defense", 10),
             "desc": "防禦永久+10。"}
        ]
    },
    "厚土訣": {
        "系別": "土", "type": "雙修",
        "skills": [
            {"name": "厚土之軀", "kind": "被動", "effect": ("max_hp_bonus", 20),
             "desc": "最大氣血永久+20。"},
            {"name": "厚土之鎧", "kind": "主動", "cost": {"靈力": 5},
             "desc": "2回合內防禦+15。", "buff": {"防禦": 15, "turns": 2}}
        ]
    },
    # 稀有系
    "聽風術": {
        "系別": "稀有", "type": "雙修",
        "skills": [
            {"name": "御風", "kind": "被動", "effect": ("bonus_speed", 5),
             "desc": "速度永久+5。"},
            {"name": "風刃術", "kind": "主動", "cost": {"靈力": 4},
             "desc": "造成（法力*1.3）傷害。", "func": lambda p: int(p.stats.get("法力", 0) * 1.3)}
        ]
    },
    "感電策": {
        "系別": "稀有", "type": "雙修",
        "skills": [
            {"name": "驚蟄", "kind": "被動", "effect": ("proc_lightning", (0.1, 5)),
             "desc": "武術攻擊10%機率附加5點雷電傷害。"},
            {"name": "掌心雷", "kind": "主動", "cost": {"靈力": 7},
             "desc": "造成少量傷害，有25%機率麻痺1回合。", "func": lambda p: 5, "status_chance": 0.25, "status": "麻痺"}
        ]
    },
    "凝冰訣": {
        "系別": "稀有", "type": "雙修",
        "skills": [
            {"name": "寒氣", "kind": "被動", "effect": ("slow_on_hit", 1),
             "desc": "武術攻擊使敵人下一回合速度-1。"},
            {"name": "凝霜術", "kind": "主動", "cost": {"靈力": 8},
             "desc": "50%機率使敵人下一回合速度降一半。", "func": lambda p: 0, "chance_slow_half": 0.5}
        ]
    },
    "拜日式": {
        "系別": "稀有", "type": "雙修",
        "skills": [
            {"name": "日光滋養", "kind": "被動", "effect": ("day_recover", 1),
             "desc": "白日探索/移動每過一天可回1氣血1靈力。"},
            {"name": "聖光術", "kind": "主動", "cost": {"靈力": 6},
             "desc": "對妖獸造成少量傷害，25%機率目眩使下一擊命中率降低。", "func": lambda p: 3, "status_chance": 0.25, "status": "目眩"}
        ]
    },
    "陰影吐納": {
        "系別": "稀有", "type": "雙修",
        "skills": [
            {"name": "影襲", "kind": "被動", "effect": ("first_hit_bonus", 0.2),
             "desc": "戰鬥第一擊傷害+20%。"},
            {"name": "潛影", "kind": "主動", "cost": {"靈力": 10},
             "desc": "下一回合大幅提升閃避率。", "buff": {"evasion_bonus": 0.5, "turns": 1}}
        ]
    },
    # 特殊
    "無名吐納法": {
        "系別": "特殊", "type": "特殊",
        "skills": [
            {"name": "道法自然(初窺)", "kind": "被動", "effect": ("global_xp_bonus", 0.1),
             "desc": "所有來源修為+10%。"}
        ]
    }
}

# 物品 / 怪 / 地圖 / 商店 / 製作（簡略版保留你之前那套結構）
MORTAL_ITEMS = {
    "止血草": {"type": "靈草", "value": 2}, "清心花": {"type": "靈草", "value": 2}, "鐵線草": {"type": "靈草", "value": 3},
    "月光草": {"type": "靈草", "value": 4}, "陽炎果": {"type": "靈草", "value": 4}, "火絨花": {"type": "靈草", "value": 1},
    "厚土根": {"type": "靈草", "value": 3}, "石膚苔": {"type": "靈草", "value": 3}, "冰晶草": {"type": "靈草", "value": 5},
    "向陽花": {"type": "靈草", "value": 8},
    "鐵礦": {"type": "礦物", "value": 4}, "銅礦": {"type": "礦物", "value": 6}, "石英": {"type": "礦物", "value": 5},
    "石炭": {"type": "礦物", "value": 3}, "硫磺": {"type": "礦物", "value": 3}, "岩鹽": {"type": "礦物", "value": 2},
    "黏土": {"type": "礦物", "value": 1}, "石灰岩": {"type": "礦物", "value": 1}, "黑曜石": {"type": "礦物", "value": 7},
    "化石": {"type": "礦物", "value": 1},
    "生鐵獠牙": {"type": "掉落物", "value": 8}, "糙皮": {"type": "掉落物", "value": 5}, "枯藤蔓": {"type": "掉落物", "value": 2},
    "毒浆果": {"type": "掉落物", "value": 4}, "蛇蛻": {"type": "掉落物", "value": 6}, "水靈鱗片": {"type": "掉落物", "value": 7},
    "火狐尾": {"type": "掉落物", "value": 7}, "焦炭": {"type": "掉落物", "value": 2}, "岩甲片": {"type": "掉落物", "value": 6},
    "地穴爪": {"type": "掉落物", "value": 5}, "夜蝠翼": {"type": "掉落物", "value": 15}, "鋼翼刃羽": {"type": "掉落物", "value": 30}
}

MORTAL_MONSTERS = {
    '外圍': {"岩甲穿山兽": {"stats": {"氣血": 100, "肉身強度": 20, "速度": 2}, "drops": {"岩甲片": 0.7, "地穴爪": 0.5}, "xp": 12}},
    '初入': {"鐵爪山豬": {"stats": {"氣血": 80, "肉身強度": 15, "速度": 5}, "drops": {"生鐵獠牙": 0.7, "糙皮": 0.5}, "xp": 10}},
    '內部': {"溪澗水蛇": {"stats": {"氣血": 60, "法力": 3, "肉身強度": 8, "速度": 7}, "drops": {"蛇蛻": 0.6, "水靈鱗片": 0.4}, "xp": 9}},
    '深入': {"赤尾火狐": {"stats": {"氣血": 55, "法力": 5, "肉身強度": 5, "速度": 9}, "drops": {"火狐尾": 0.6, "焦炭": 0.3}, "xp": 9}},
    '核心': {"幽影蝠": {"stats": {"氣血": 40, "法力": 8, "肉身強度": 3, "速度": 13}, "drops": {"夜蝠翼": 0.2}, "xp": 15}},
    '禁地': {"幼年鋼翼獅鷲": {"stats": {"氣血": 300, "肉身強度": 40, "速度": 30}, "drops": {"鋼翼刃羽": 0.1, "糙皮": 1.0}, "xp": 100}},
}

LOCATION_DATA = {
    "青石鎮": {"type": "城鎮", "desc": "坐落於青雲山脈腳下...", "actions": ["修煉", "調息", "狀態", "背包", "切換功法", "製作", "商店", "前往他處"], "travel_to": {"青雲山脈": 15}},
    "青雲山脈": {"type": "地圖", "desc": "綿延數百里...", "zones": ["外圍", "初入", "內部", "深入", "核心", "禁地"],
                 "resources": {'外圍': {"靈草": {"止血草": 0.5, "石膚苔": 0.5}},
                               '初入': {"靈草": {"清心花": 0.5, "厚土根": 0.5}},
                               '內部': {"礦物": {"鐵礦": 0.5, "銅礦": 0.5}},
                               '深入': {"靈草": {"月光草": 0.5, "火絨花": 0.5}},
                               '核心': {"礦物": {"石英": 0.5, "石炭": 0.5}},
                               '禁地': {"靈草": {"向陽花": 1.0}}}, "actions": ["探索", "狀態", "背包"]}
}

SHOP_DATA = {
    "煉器鋪": {"sells": ["鐵礦", "銅礦", "石炭", "糙皮", "生鐵獠牙"]},
    "丹藥鋪": {"sells": ["止血草", "清心花", "厚土根"]},
    "福祿鋪": {"sells": ["枯藤蔓", "焦炭", "蛇蛻"]}
}

MORTAL_RECIPES = {
    "煉器": {
        '鐵骨戰錘': {'type': '法器', 'req_prof': '體修', 'materials': {'鐵礦': 2, '生鐵獠牙': 1}, 'stats': {'肉身強度': 15}, "value": 50},
    },
    "煉丹": {
        '氣血散': {'type': '丹藥', 'desc': '恢復氣血', 'materials': {'止血草': 2}, 'effect': ('氣血', 50), "value": 10},
    },
    "畫符": {
        '火球符': {'type': '符籙', 'desc': '攻擊', 'materials': {'焦炭': 1, '火狐尾': 1}, 'effect': ('damage', 25), "value": 25},
    }
}


# ====================
# Player 類
# ====================
class Player:
    def __init__(self, name, gender):
        self.name, self.gender = name, gender
        self.realm, self.level, self.xp, self.max_xp = "凡人", 1, 0, 100
        self.lifespan_days = random.randint(60, 80) * 365
        self.time_passed = 0
        self.stats = {
            "氣血": 100, "最大氣血": 100,
            "靈力": 10, "最大靈力": 10,
            "法力": 5, "肉身強度": 5,
            "速度": 5, "防禦": 0, "氣運": random.randint(1, 10)
        }
        self.inventory = {}
        self.equipment = {"法器": None, "防具": None, "功法": None}
        self.currency = {"中品靈石": 0, "下品靈石": 50}
        self.passives = {}
        self.location, self.zone = "青石鎮", None
        self.in_combat, self.combat_target, self.in_event, self.viewing = False, None, None, None
        self.flags = {"first_mountain_encounter": True}
        self.techniques = []  # 學會的功法名稱列表
        self.active_buffs = []  # 暫時 buff dict list
        self._last_target = None  # 疊浪功用
        self.used_first_hit = False  # 陰影吐納

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        player = cls(data['name'], data['gender'])
        player.__dict__.update(data)
        return player

    def get_total_currency(self):
        return self.currency["下品靈石"] + self.currency["中品靈石"] * CURRENCY_CONVERSION["中品靈石"]

    def update_currency(self, total_lower):
        self.currency["中品靈石"] = total_lower // CURRENCY_CONVERSION["中品靈石"]
        self.currency["下品靈石"] = total_lower % CURRENCY_CONVERSION["中品靈石"]

    def pass_days(self, days):
        self.time_passed += days
        self.lifespan_days -= days
        return f"光陰似箭，{days}天過去了。"

    def add_item(self, i, q=1):
        self.inventory[i] = self.inventory.get(i, 0) + q
        return f"你獲得了【{i}】x{q}。"

    def remove_item(self, i, q=1):
        if self.inventory.get(i, 0) >= q:
            self.inventory[i] -= q
            if self.inventory[i] <= 0:
                del self.inventory[i]
            return f"移除 【{i}】x{q}。"
        return f"背包沒有足夠的【{i}】。"

    def has_materials(self, materials):
        return all(self.inventory.get(item, 0) >= need for item, need in materials.items())

    def remove_materials(self, materials):
        if not self.has_materials(materials):
            raise ValueError("材料不足")
        for item, need in materials.items():
            self.inventory[item] -= need
            if self.inventory[item] == 0:
                del self.inventory[item]

    def add_xp(self, amount):
        bonus = 0
        # 無名吐納法加成
        if "無名吐納法" in self.techniques:
            bonus += math.ceil(amount * 0.1)
        total_gain = amount + bonus
        if self.level >= 10:
            return "修為已達凡人境巔峰。"
        self.xp += total_gain
        log_msg = f"修為增加了 {total_gain} 點。"
        while self.xp >= self.max_xp and self.level < 10:
            self.xp -= self.max_xp
            self.level += 1
            self.lifespan_days += MORTAL_REALM_DATA["lifespan_gain_per_level"] * 365
            self.max_xp = math.ceil(self.max_xp * MORTAL_REALM_DATA["xp_multiplier"])
            self.stats["最大氣血"] += 10
            self.stats["氣血"] = self.stats["最大氣血"]
            log_msg += f" 恭喜！你提升到了【凡人 {self.level} 層】！"
        return log_msg


# ====================
# 模板（簡化並含功法選擇/學習/顯示）
# ====================
HTML_TEMPLATE = """
<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8">
<title>文字修仙 MUD</title>
<style>
body{background:#1f2230;color:#ddd;font-family:system-ui;padding:10px;}
.container{max-width:720px;margin:0 auto;background:#2a2e44;padding:20px;border-radius:10px;}
.button{padding:10px 14px;margin:4px;border:none;border-radius:6px;cursor:pointer;background:#4a5578;color:white;font-weight:600;}
.small{font-size:0.8em;color:#aaa;}
.card{background:#1f2338;padding:12px;border:1px solid #444;border-radius:8px;margin-bottom:12px;}
.flex{display:flex;gap:10px;flex-wrap:wrap;}
.badge{background:#5b99e5;padding:2px 6px;border-radius:4px;font-size:0.7em;margin-right:4px;}
</style></head><body><div class="container">
<h1>文字修仙 MUD（凡人境）</h1>
{% if player %}
    <div class="card">
        <strong>{{ player.name }}</strong>（{{ player.gender }}） | 修為：凡人 {{ player.level }} 層 | 氣血：{{ player.stats["氣血"] }}/{{ player.stats["最大氣血"] }} | 靈力：{{ player.stats["靈力"] }}/{{ player.stats["最大靈力"] }}<br>
        當前位置：{% if player.zone %}{{ player.location }} - {{ player.zone }}{% else %}{{ player.location }}{% endif %}<br>
        已學功法：{% for t in player.techniques %}<span class="badge">{{ t }}</span>{% endfor %} <br>
        <div>靈石：中品 {{ player.currency["中品靈石"] }} / 下品 {{ player.currency["下品靈石"] }}</div>
    </div>
    <div class="card">
        <div class="flex">
            {% for action in location_data[player.location].actions %}
                <form method="post"><button class="button" name="action" value="{{ action }}">{{ action }}</button></form>
            {% endfor %}
            {% if player.location == "青雲山脈" %}
                <form method="post"><button class="button" name="action" value="探索">探索</button></form>
            {% endif %}
            <form method="post"><button class="button" name="action" value="view_techniques">切換功法 / 學習功法</button></form>
        </div>
    </div>
    <div class="card">
        <h3>功法管理</h3>
        {% if player.viewing == 'techniques' %}
            <div class="flex">
            {% for name, tech in MORTAL_TECHNIQUES.items() %}
                <div style="flex:1 1 250px;background:#242a4f;padding:8px;border-radius:6px;position:relative;">
                    <div><strong>{{ name }}</strong>（{{ tech.type }}）</div>
                    <div class="small">系別：{{ tech["系別"] }}</div>
                    <div class="small">{{ tech.skills | length }} 項技能</div>
                    <div style="margin-top:6px;">
                        {% if name in player.techniques %}
                            <div style="color:#7fff7f;font-weight:600;">已學會</div>
                            <form method="post"><button class="button" name="action" value="learn:{{ name }}" disabled>學習（已學）</button></form>
                        {% else %}
                            <form method="post"><button class="button" name="action" value="learn:{{ name }}">學習（消耗3天）</button></form>
                        {% endif %}
                    </div>
                    <div style="margin-top:6px;">
                        {% for sk in tech.skills %}
                            <div>
                                <em>{{ sk.name }}</em> - {{ sk.kind }}：{{ sk.desc }}
                            </div>
                        {% endfor %}
                    </div>
                </div>
            {% endfor %}
            </div>
            <form method="post"><button class="button" name="action" value="返回">返回</button></form>
        {% endif %}
    </div>
    <div class="card">
        <h3>操作日誌</h3>
        {% for msg in game_log %}
            <div>{{ msg }}</div>
        {% endfor %}
    </div>
    <div class="card">
        <h3>戰鬥 / 事件</h3>
        {% if player.in_combat %}
            <div><strong>戰鬥中：對手是 {{ player.combat_target.name }}（氣血 {{ player.combat_target.hp }}）</strong></div>
            <div class="flex">
                <form method="post"><button class="button" name="action" value="攻擊">武術攻擊</button></form>
                <form method="post"><button class="button" name="action" value="逃跑">逃跑</button></form>
                {% for t in player.techniques %}
                    {% set tech = MORTAL_TECHNIQUES[t] %}
                    {% for sk in tech.skills %}
                        {% if sk.kind == "主動" %}
                            <form method="post">
                                <button class="button" name="action" value="use_skill:{{ t }}:{{ sk.name }}">
                                    {{ sk.name }} ({{ t }})
                                </button>
                            </form>
                        {% endif %}
                    {% endfor %}
                {% endfor %}
            </div>
        {% endif %}
    </div>
    <div style="margin-top:10px;"><a href="/reset" style="color:#f88;">重新開始</a></div>
{% else %}
    <div class="card">
        <h2>開啟仙途</h2>
        <form method="post">
            <input name="name" placeholder="道號" required> <input name="gender" placeholder="性別" required>
            <button class="button" type="submit" value="開始">踏入</button>
        </form>
    </div>
{% endif %}
</div></body></html>
"""

# ====================
# 工具函式
# ====================
def get_player():
    return Player.from_dict(session.get("player_data")) if session.get("player_data") else None

def save_player(player):
    session["player_data"] = player.to_dict()

def compute_learning_chance(player):
    base = 90 - len(player.techniques) * 15
    if player.realm != "凡人":
        base += 10
    return max(10, min(95, base))

def apply_passive_effects_on_receive(player, incoming):
    # 受攻時減傷
    dmg = incoming
    # 銅皮功
    if "銅皮功" in player.techniques:
        dmg = math.floor(dmg * (1 - 0.05))
    # 其他被動防禦加成
    for t in player.techniques:
        tech = MORTAL_TECHNIQUES.get(t, {})
        for sk in tech["skills"]:
            if sk.get("kind") == "被動":
                effect = sk.get("effect", ())
                if effect and effect[0] == "bonus_defense":
                    dmg = max(0, dmg - effect[1])
    return dmg

def apply_passive_on_attack(player, target_name, base_dmg):
    dmg = base_dmg
    # 疊浪功: 同一目標連擊
    if "疊浪功" in player.techniques:
        if player._last_target == target_name:
            dmg += 2
        player._last_target = target_name
    # 淬火體
    if "淬火體" in player.techniques:
        dmg += 3
    # 陰影吐納第一擊 bonus
    if "陰影吐納" in player.techniques and not player.used_first_hit:
        dmg = int(dmg * 1.2)
        player.used_first_hit = True
    # 感電策機率雷電
    if "感電策" in player.techniques:
        if random.random() < 0.1:
            dmg += 5  # 雷電
    return dmg

def handle_heal_effects(player, amount):
    # 草還丹訣被動
    if "草還丹訣" in player.techniques:
        amount = int(amount * 1.2)
    player.stats["氣血"] = min(player.stats["最大氣血"], player.stats["氣血"] + amount)
    return f"恢復了 {amount} 點氣血。"

def apply_daily_recover(player):
    # 拜日式 白日探索/移動
    # 這裡暫用 location 切換時處理
    if "拜日式" in player.techniques:
        player.stats["氣血"] = min(player.stats["最大氣血"], player.stats["氣血"] + 1)
        player.stats["靈力"] = min(player.stats["最大靈力"], player.stats["靈力"] + 1)
        return "日光滋養回復 1 氣血與 1 靈力。"
    return ""

# ====================
# Routes
# ====================
@app.route("/", methods=["GET", "POST"])
def index():
    game_log = session.pop("game_log", [])
    player = get_player()
    if request.method == "POST" and not player:
        player = Player(request.form["name"], request.form["gender"])
        save_player(player)
        return redirect(url_for("index"))

    # 修煉、調息、狀態、背包、切換功法、製作、商店、前往他處
    all_items = MORTAL_ITEMS.copy()
    for craft in MORTAL_RECIPES.values():
        for name, data in craft.items():
            all_items[name] = data

    return render_template_string(HTML_TEMPLATE,
                                  player=player,
                                  game_log=game_log,
                                  location_data=LOCATION_DATA,
                                  MORTAL_TECHNIQUES=MORTAL_TECHNIQUES,
                                  all_items=all_items,
                                  recipes=MORTAL_RECIPES)

@app.route("/action", methods=["POST"])
def handle_action():
    player = get_player()
    game_log = []
    if not player:
        return redirect(url_for("index"))
    action = request.form.get("action", "")

    # 基本操作
    if action == "返回":
        player.viewing = None
    elif action == "背包":
        player.viewing = "backpack"
    elif action == "狀態":
        game_log.append(f"修為：凡人 {player.level} 層；氣血 {player.stats['氣血']}/{player.stats['最大氣血']}；靈力 {player.stats['靈力']}/{player.stats['最大靈力']}")
    elif action == "調息":
        prev_hp = player.stats["氣血"]
        prev_mp = player.stats["靈力"]
        player.stats["氣血"] = min(player.stats["最大氣血"], player.stats["氣血"] + 20)
        player.stats["靈力"] = min(player.stats["最大靈力"], player.stats["靈力"] + 5)
        game_log.append(f"調息：氣血 {prev_hp}→{player.stats['氣血']}、靈力 {prev_mp}→{player.stats['靈力']}。")
    elif action == "修煉":
        # 基礎經驗 + 氣運/2
        base = 10 + player.stats.get("氣運", 0) // 2
        bonus = 0
        # 雙修/法修加成（簡化：如果學了炎陽訣白日+10% 是在此增加）
        if "炎陽訣" in player.techniques:
            bonus += int(base * 0.1)
        if "江河訣" in player.techniques:
            # 無特別加成，已反映在 stats 最大靈力
            pass
        # 消耗天數
        day_msg = player.pass_days(1)
        xp_gain = base + bonus
        msg = player.add_xp(xp_gain)
        game_log.append(f"修煉獲得經驗 {xp_gain}。{msg} {day_msg}")
    elif action == "前往他處":
        if player.location == "青石鎮":
            player.location = "青雲山脈"
            player.zone = "外圍"
            game_log.append("前往青雲山脈。")
            extra = apply_daily_recover(player)
            if extra:
                game_log.append(extra)
        else:
            player.location = "青石鎮"
            player.zone = None
            game_log.append("返回青石鎮。")
    elif action == "探索":
        if player.location == "青雲山脈" and player.zone:
            zone = player.zone
            if random.random() < 0.5:
                mons = MORTAL_MONSTERS.get(zone, {})
                if mons:
                    name, data = random.choice(list(mons.items()))
                    player.in_combat = True
                    player.combat_target = type("M", (), {"name": name, "hp": data["stats"].get("氣血", 0)})
                    game_log.append(f"遭遇 【{name}】！")
                else:
                    game_log.append("此區無怪。")
            else:
                res = LOCATION_DATA["青雲山脈"]["resources"].get(zone, {})
                if res:
                    _, pool = random.choice(list(res.items()))
                    if pool:
                        item, chance = random.choice(list(pool.items()))
                        if random.random() < chance:
                            player.add_item(item, 1)
                            game_log.append(f"獲得資源：【{item}】。")
                        else:
                            game_log.append("探索無所獲。")
                else:
                    game_log.append("此區無資源。")
        else:
            game_log.append("無法探索。")
    elif action == "view_techniques":
        player.viewing = "techniques"
    elif action.startswith("learn:"):
        tech_name = action.split(":", 1)[1]
        chance = compute_learning_chance(player)
        roll = random.randint(1, 100)
        player.pass_days(3)
        if tech_name in player.techniques:
            game_log.append(f"已學會【{tech_name}】。")
        else:
            if roll <= chance:
                player.techniques.append(tech_name)
                game_log.append(f"學會了【{tech_name}】，成功率 {chance}%（骰到 {roll}）")
                # 即時應用永久被動：最大值提升類型
                if tech_name in ["江河訣", "歸元訣"]:
                    # 由被動 effect 處理
                    pass
                if tech_name == "厚土訣":
                    player.stats["最大氣血"] += 20
                    player.stats["氣血"] = player.stats["最大氣血"]
                if tech_name in ["江河訣", "歸元訣"]:
                    player.stats["最大靈力"] += 20
                    player.stats["靈力"] = player.stats["最大靈力"]
                if tech_name == "聽風術":
                    player.stats["速度"] += 5
            else:
                game_log.append(f"學習【{tech_name}】失敗，成功率 {chance}%（骰到 {roll}）")
    elif action == "攻擊":
        if player.in_combat and player.combat_target:
            base = max(1, player.stats.get("肉身強度", 0))
            dmg = apply_passive_on_attack(player, player.combat_target.name, base)
            # 陽炎擊/火球術/水箭等為主動 skill 需點選 use_skill 才觸發
            # 對怪造成傷害
            player.combat_target.hp -= dmg
            game_log.append(f"你武術攻擊造成 {dmg} 點傷害。")
            if player.combat_target.hp <= 0:
                zone = player.zone or "外圍"
                mon = MORTAL_MONSTERS.get(zone, {}).get(player.combat_target.name, {})
                xp = mon.get("xp", 0)
                game_log.append(f"擊敗【{player.combat_target.name}】 獲得 {xp} 經驗。")
                game_log.append(player.add_xp(xp))
                drops = mon.get("drops", {})
                for item, prob in drops.items():
                    if random.random() < prob:
                        player.add_item(item, 1)
                        game_log.append(f"掉落 【{item}】。")
                player.in_combat = False
                player.combat_target = None
    elif action == "逃跑":
        if player.in_combat:
            if random.random() < 0.5:
                game_log.append("逃跑成功。")
                player.in_combat = False
                player.combat_target = None
            else:
                game_log.append("逃跑失敗。")
    elif action.startswith("use_skill:"):
        # 格式 use_skill:功法:技能名
        _, tech_name, skill_name = action.split(":", 2)
        if tech_name in player.techniques and player.in_combat and player.combat_target:
            tech = MORTAL_TECHNIQUES.get(tech_name, {})
            found = None
            for sk in tech.get("skills", []):
                if sk["name"] == skill_name:
                    found = sk
                    break
            if not found:
                game_log.append(f"找不到技能 {skill_name}。")
            else:
                # 消耗靈力
                cost = found.get("cost", {})
                if player.stats["靈力"] < cost.get("靈力", 0):
                    game_log.append("靈力不足。")
                else:
                    player.stats["靈力"] -= cost.get("靈力", 0)
                    # 主動公式
                    if found.get("func"):
                        effect_val = found["func"](player)
                        if "術" in skill_name or "術" in found["name"]:
                            # 攻擊型
                            dmg = effect_val
                            # 特殊：陽炎擊算在武術上加
                            player.combat_target.hp -= dmg
                            game_log.append(f"使用【{skill_name}】對敵造成 {dmg} 傷害。")
                            if player.combat_target.hp <= 0:
                                zone = player.zone or "外圍"
                                mon = MORTAL_MONSTERS.get(zone, {}).get(player.combat_target.name, {})
                                xp = mon.get("xp", 0)
                                game_log.append(f"擊敗【{player.combat_target.name}】 獲得 {xp} 經驗。")
                                game_log.append(player.add_xp(xp))
                                player.in_combat = False
                                player.combat_target = None
                        else:
                            # 補血
                            msg = handle_heal_effects(player, effect_val)
                            game_log.append(f"使用【{skill_name}】：{msg}")
                    # buff 處理（例如金石之護、厚土之鎧、潛影）
                    if found.get("buff"):
                        buff = found["buff"].copy()
                        buff["remaining"] = buff["turns"]
                        player.active_buffs.append(buff)
                        game_log.append(f"獲得臨時 buff：{skill_name} ({buff})")
                    # 狀態效果
                    if found.get("status") and random.random() < found.get("status_chance", 0):
                        game_log.append(f"使敵人處於 {found['status']} 狀態。")
                    if found.get("chance_slow_half") and random.random() < found["chance_slow_half"]:
                        game_log.append("敵人速度減半（寒氣效果）。")
        else:
            game_log.append("不能使用技能。")
    else:
        game_log.append(f"未知操作：{action}")

    # 處理 buff 減少
    for b in list(player.active_buffs):
        if b.get("remaining", 0) > 0:
            b["remaining"] -= 1
            if b["remaining"] <= 0:
                # 回復原狀
                if "防禦" in b:
                    player.stats["防禦"] -= b["防禦"]
                player.active_buffs.remove(b)

    # 戰鬥中敵人反擊簡略（可擴）
    if player.in_combat and player.combat_target:
        # 假設怪每回合回擊一次（若還活著且你剛攻擊）
        if player.combat_target.hp > 0:
            incoming = 5  # 簡化固定傷害
            reduced = apply_passive_effects_on_receive(player, incoming)
            player.stats["氣血"] -= reduced
            game_log.append(f"敵人反擊，受到 {reduced} 傷害。")
            if player.stats["氣血"] <= 0:
                game_log.append("你暈厥了，重置到青石鎮。")
                # 簡單懲罰
                player.location = "青石鎮"
                player.zone = None
                player.stats["氣血"] = player.stats["最大氣血"]
                player.in_combat = False
                player.combat_target = None

    save_player(player)
    session["game_log"] = game_log
    return redirect(url_for("index"))

@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("index"))

# ====================
# 啟動
# ====================
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
