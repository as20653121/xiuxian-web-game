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
<div class="actions">{% if not player.in_combat %}<form action="/action" method="post"><button class="btn" type="submit" name="action" value="修煉">修煉</button></form><form action="/action" method="post"><button class="btn" type="submit" name="action" value="探索">探索</button></form><form action="/action" method="post"><button class="btn" type="submit" name="action" value="狀態">詳細狀態</button></form><form action="/action" method="post"><button class="btn" type="submit" name="action" value="旅行">前往他處</button></form>
{% else %}<form action="/action" method="post"><button class="btn btn-danger" type="submit" name="action" value="攻擊">攻擊</button></form><form action="/action" method="post"><button class="btn" type="submit" name="action" value="逃跑">逃跑</button></form>{% endif %}</div>
<div style="text-align:center;margin-top:20px;"><a href="/reset">開啟新的輪迴</a></div>
{% else %}<div class="char-creation"><h2>開啟仙途</h2><form action="/" method="post"><input type="text" name="name" placeholder="請賜道號" required><br><input type="text" name="gender" placeholder="請定性別 (男/女)" required><br><input class="btn" type="submit" value="踏入此界"></form></div>{% endif %}
</div></body></html>"""

def get_player():
    return Player.from_dict(session['player_data']) if 'player_data' in session else None
def save_player(player): session['player_data'] = player.to_dict()

@app.route('/', methods=['GET', 'POST'])
def index():
    game_log = session.pop('game_log', [])
    if request.method == 'POST':
        player = Player(request.form['name'], request.form['gender'])
        if random.random() < 0.1:
            const_name = random.choice(list(CONSTITUTION_DATA.keys())); player.constitution = {"name": const_name}
            game_log.append(f"你似乎是萬中無一的【{const_name}】!")
        game_log.append(f"{player.name}，你的故事，將從【青石鎮】開始。")
        save_player(player); session['game_log'] = game_log; return redirect(url_for('index'))
    return render_template_string(HTML_TEMPLATE, player=get_player(), game_log=game_log)

@app.route('/action', methods=['POST'])
def handle_action():
    player = get_player(); game_log = []
    if not player: return redirect(url_for('index'))
    action = request.form.get('action')

    if action == "修煉": game_log.append(player.add_xp(10 + player.level * 2))
    elif action == "探索":
        if player.location == "青雲山脈":
            monster_name = random.choice(list(MORTAL_MONSTERS.keys()))
            player.in_combat = True; player.combat_target = {"name": monster_name, "hp": MORTAL_MONSTERS[monster_name]['stats']['氣血']}
            game_log.append(f"你遭遇了【{monster_name}】！")
        else: game_log.append("城鎮之中，沒什麼好探索的。")
    elif action == "攻擊":
        if player.in_combat:
            target_info = player.combat_target; monster_data = MORTAL_MONSTERS[target_info['name']]
            damage = max(1, player.stats["肉身強度"] + random.randint(-2, 2)); target_info['hp'] -= damage
            game_log.append(f"你對【{target_info['name']}】造成了 {damage} 點傷害。")
            if target_info['hp'] <= 0:
                game_log.append(f"你擊敗了【{target_info['name']}】!"); player.in_combat = False
                game_log.append(player.add_xp(monster_data.get('xp', 10)))
                for item, chance in monster_data.get('drops', {}).items():
                    if random.random() < chance: player.add_item(item); game_log.append(f"你獲得了【{item}】。")
            else:
                monster_damage = max(1, monster_data['stats']['肉身強度'] - player.stats['防禦']); player.stats['氣血'] -= monster_damage
                game_log.append(f"【{target_info['name']}】對你造成了 {monster_damage} 點傷害。")
                if player.stats['氣血'] <= 0:
                    player.stats['氣血'] = 1; player.location = "青石鎮"; player.in_combat = False
                    game_log.append("你重傷倒下...醒來時回到了青石鎮。")
    elif action == "逃跑":
        game_log.append("你成功逃離了戰鬥！"); player.in_combat = False
    elif action == "狀態":
        game_log.append(f"道號: {player.name}, 壽元: {player.lifespan}"); game_log.append(f"境界: {player.realm} {player.level}層"); game_log.append(f"修為: {player.xp}/{player.max_xp}")
    elif action == "旅行":
        current_loc = player.location; destination = LOCATION_DATA[current_loc]['travel_to'][0]
        player.location = destination; game_log.append(f"你動身前往【{destination}】。")
    
    save_player(player); session['game_log'] = game_log; return redirect(url_for('index'))

@app.route('/reset')
def reset():
    session.clear(); return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)