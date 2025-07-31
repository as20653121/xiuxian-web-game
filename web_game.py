# --- 準備工作 ---
# 1. 安裝Kivy: pip install kivy
# 2. 執行此腳本

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
import random

# 將您的遊戲核心邏輯 (Player類別等) 放在這裡
# 為了範例簡潔，我們只模擬一部分
class GameLogic:
    def __init__(self):
        self.level = 1
        self.xp = 0
        self.max_xp = 100
        self.hp = 100
        self.max_hp = 100

    def cultivate(self):
        xp_gain = random.randint(10, 20)
        self.xp += xp_gain
        if self.xp >= self.max_xp:
            self.level += 1
            self.xp = 0
            self.max_xp = int(self.max_xp * 1.2)
            return f"修為增加了 {xp_gain} 點。恭喜！你提升到了凡人 {self.level} 層！"
        return f"修為增加了 {xp_gain} 點。"

    def explore(self):
        if random.random() < 0.7:
            return "遭遇了【鐵爪山豬】！戰鬥開始！"
        else:
            return "你找到了一株【止血草】。"

class GameScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [20, 20, 20, 20]
        self.spacing = 10
        
        # 遊戲邏輯實例
        self.game = GameLogic()

        # 1. 狀態面板
        self.status_layout = BoxLayout(size_hint_y=None, height=40)
        self.level_label = Label(text=f"境界: 凡人 {self.game.level} 層", font_size='18sp')
        self.hp_label = Label(text=f"氣血: {self.game.hp}/{self.game.max_hp}", font_size='18sp')
        self.status_layout.add_widget(self.level_label)
        self.status_layout.add_widget(self.hp_label)
        self.add_widget(self.status_layout)

        # 2. 遊戲日誌 (可滾動)
        self.scroll_view = ScrollView(size_hint=(1, 1))
        self.log_label = Label(text="歡迎來到修仙世界...\n", size_hint_y=None, font_size='16sp', text_size=(Window.width-80, None))
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        self.scroll_view.add_widget(self.log_label)
        self.add_widget(self.scroll_view)

        # 3. 操作按鈕
        self.action_layout = BoxLayout(size_hint_y=None, height=60, spacing=10)
        cultivate_btn = Button(text="修煉", font_size='20sp', on_press=self.do_cultivate)
        explore_btn = Button(text="探索", font_size='20sp', on_press=self.do_explore)
        self.action_layout.add_widget(cultivate_btn)
        self.action_layout.add_widget(explore_btn)
        self.add_widget(self.action_layout)
        
    def add_log(self, message):
        self.log_label.text += message + "\n"

    def update_status(self):
        self.level_label.text = f"境界: 凡人 {self.game.level} 層"
        self.hp_label.text = f"氣血: {self.game.hp}/{self.game.max_hp}"

    def do_cultivate(self, instance):
        log_message = self.game.cultivate()
        self.add_log(log_message)
        self.update_status()

    def do_explore(self, instance):
        log_message = self.game.explore()
        self.add_log(log_message)

class XiuxianApp(App):
    def build(self):
        Window.clearcolor = (0.1, 0.1, 0.1, 1) # 設定背景色
        return GameScreen()

if __name__ == '__main__':
    XiuxianApp().run()