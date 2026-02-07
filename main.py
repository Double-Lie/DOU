import flet as ft
import time
# 确保 solver.py 在同一目录下
from solver import DoudizhuSolver, CHAR_TO_RANK, RANK_TO_CHAR

def main(page: ft.Page):
    # ================= 配置 (Material 3) =================
    page.title = "斗地主残局大师"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO, use_material3=True)
    page.scroll = ft.ScrollMode.AUTO  # 适配手机屏幕滚动
    
    solver = DoudizhuSolver()

    # ================= 状态变量 =================
    state = {
        "landlord_hand": [], 
        "peasant_hand": [],  
        "last_move": None,   
        "current_turn": "landlord",
        "selected_indices": set(),
        "history_log": []
    }

    # ================= 辅助函数 =================
    def parse_cards(card_str):
        res = []
        card_str = card_str.upper().replace(" ", "")
        for char in card_str:
            if char in CHAR_TO_RANK:
                res.append(CHAR_TO_RANK[char])
        return sorted(res)

    def format_card_label(rank):
        return RANK_TO_CHAR[rank]

    def get_card_color(rank):
        return ft.Colors.RED if rank >= 16 else ft.Colors.BLACK

    # ================= UI 组件 =================
    log_text = ft.Text("准备开始对局...", size=14, color=ft.Colors.GREY_700)
    table_area = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=-15)
    
    ai_hand_view = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=-20)
    player_hand_view = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=-20)

    # 使用 M3 风格的 FilledButton 代替旧的 ElevatedButton
    btn_play = ft.FilledButton("出牌", icon=ft.Icons.PLAY_ARROW, disabled=True)
    btn_pass = ft.Button("不出", icon=ft.Icons.SKIP_NEXT, disabled=True) 
    btn_reset = ft.IconButton(icon=ft.Icons.RESTART_ALT, tooltip="重置对局")

    input_landlord = ft.TextField(
        label="地主手牌 (AI)", 
        hint_text="如: 2AKQJT987", 
        capitalization=ft.TextCapitalization.CHARACTERS
    )
    input_peasant = ft.TextField(
        label="农民手牌 (你)", 
        hint_text="如: DX2AA", 
        capitalization=ft.TextCapitalization.CHARACTERS
    )
    
    # ================= 逻辑处理 =================

    def render_card(rank, is_selected=False, on_click=None, index=None):
        """生成符合 M3 设计规范的扑克牌"""
        return ft.Container(
            content=ft.Text(
                format_card_label(rank), 
                color=get_card_color(rank),
                weight=ft.FontWeight.BOLD,
                size=18
            ),
            width=48, height=70,
            bgcolor=ft.Colors.WHITE,
            # 修正: 使用 Border.all 和 Margin.only
            border=ft.Border.all(1, ft.Colors.BLUE_GREY_200) if not is_selected else ft.Border.all(2, ft.Colors.INDIGO),
            border_radius=8,
            alignment=ft.Alignment(0, 0), 
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)),
            margin=ft.Margin.only(bottom=15 if is_selected else 0),
            on_click=lambda e: on_click(index) if on_click else None,
            animate_margin=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        )

    def update_ui():
        ai_hand_view.controls = [render_card(r) for r in sorted(state["landlord_hand"], reverse=True)]
        
        player_hand_view.controls = []
        sorted_p_hand = sorted(state["peasant_hand"], reverse=True)
        for i, r in enumerate(sorted_p_hand):
            player_hand_view.controls.append(
                render_card(r, i in state["selected_indices"], toggle_card_selection, i)
            )

        table_area.controls = []
        if state["last_move"]:
            table_area.controls = [render_card(r) for r in sorted(state["last_move"].cards, reverse=True)]
        else:
            table_area.controls = [ft.Text("等待出牌...", italic=True, color=ft.Colors.GREY_400)]

        is_my_turn = state["current_turn"] == "peasant"
        btn_play.disabled = not is_my_turn
        btn_pass.disabled = not is_my_turn or state["last_move"] is None
        
        page.update()

    def toggle_card_selection(index):
        if index in state["selected_indices"]:
            state["selected_indices"].remove(index)
        else:
            state["selected_indices"].add(index)
        update_ui()

    def run_ai_turn():
        if not state["landlord_hand"]: return
        state["current_turn"] = "landlord"
        log_text.value = "AI 正在思考最优解..."
        update_ui()
        
        time.sleep(0.6)
        move, val = solver.get_best_strategy(state["landlord_hand"], state["peasant_hand"], state["last_move"])
        
        if move:
            for c in move.cards: state["landlord_hand"].remove(c)
            state["last_move"] = move
            log_text.value = f"地主出牌: {move} ({'必胜' if val==100 else '均势'})"
        else:
            state["last_move"] = None
            log_text.value = "地主选择：不出"
        
        state["current_turn"] = "peasant"
        check_game_over()
        update_ui()

    def on_play_click(e):
        sorted_hand = sorted(state["peasant_hand"], reverse=True)
        selected_cards = sorted([sorted_hand[i] for i in state["selected_indices"]])
        legal_moves = solver.get_legal_moves(state["peasant_hand"], state["last_move"])
        
        found_move = next((m for m in legal_moves if m.cards == selected_cards), None)
        if found_move:
            for c in found_move.cards: state["peasant_hand"].remove(c)
            state["last_move"] = found_move
            state["selected_indices"].clear()
            if not check_game_over(): run_ai_turn()
        else:
            log_text.value = "非法出牌！请检查规则。"
            page.update()

    def check_game_over():
        if not state["landlord_hand"] or not state["peasant_hand"]:
            winner = "地主 (AI)" if not state["landlord_hand"] else "农民 (你)"
            
            # 定义关闭弹窗的函数
            def close_dlg(e):
                dlg.open = False
                page.update()

            dlg = ft.AlertDialog(
                title=ft.Text("游戏结束"), 
                content=ft.Text(f"获胜者: {winner}"),
                actions=[ft.TextButton("确定", on_click=close_dlg)]
            )
            
            page.dialog = dlg
            dlg.open = True
            page.update()
            
            return True
           
        return False

    # ================= 布局视图 =================
    game_view = ft.SafeArea(
        content=ft.Column([
            ft.Row([ft.Text("对局详情", size=24, weight="bold"), btn_reset], alignment="spaceBetween"),
            ft.Card(content=ft.Container(
                content=ft.Column([ft.Text("地主手牌"), ai_hand_view]), padding=15
            )),
            ft.Container(table_area, height=120, alignment=ft.Alignment(0, 0)),
            ft.Card(content=ft.Container(
                content=ft.Column([ft.Text("我的手牌 (点击选牌)"), player_hand_view]), padding=15
            )),
            ft.Row([btn_pass, btn_play], alignment="center", spacing=20),
            log_text
        ], spacing=20)
    )

    input_view = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.AUTO_AWESOME, size=50, color=ft.Colors.INDIGO),
            ft.Text("斗地主残局大师", size=30, weight="bold"),
            ft.Text("输入残局手牌规则: 3-9, T, J, Q, K, A, 2, X(小王), D(大王)", size=12, color=ft.Colors.GREY),
            input_landlord, input_peasant,
            ft.FilledButton("开始计算", icon=ft.Icons.PLAY_CIRCLE_FILL, 
                           on_click=lambda e: start_game(), width=250, height=50),
        ], horizontal_alignment="center", spacing=20),
        alignment=ft.Alignment(0, 0)
    )

    def start_game():
        if not input_landlord.value or not input_peasant.value: 
            return
        state["landlord_hand"] = parse_cards(input_landlord.value)
        state["peasant_hand"] = parse_cards(input_peasant.value)
        
        # 替换页面内容而不是简单的 clean
        page.controls.clear()
        page.add(game_view)
        page.update() # 显式调用一次更新
        run_ai_turn()

    btn_play.on_click = on_play_click
    btn_pass.on_click = lambda e: (state.update({"last_move": None}), run_ai_turn())
    btn_reset.on_click = lambda e: (page.clean(), page.add(input_view))

    page.add(input_view)

# 修正: 使用 run 代替 app
if __name__ == "__main__":
    ft.run(main)
