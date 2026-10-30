import sqlite3
import sys

DB_PATH = "game_bot.db"

def big_normalize(value):
    try:
        v = int(value)
    except Exception:
        v = 0
    if v < 0: v = 0
    return str(v).zfill(100)

def get_conn():
    return sqlite3.connect(DB_PATH)

def show_help():
    print("""
======================================================
🛠 КОНСОЛЬНЫЙ ПУЛЬТ (РАБОТАЕТ БЕЗ ПЕРЕЗАПУСКА БОТА)
======================================================
1. Деньги и валюта:
   python admin.py money ID СУММА       (Выдать поинты)
   python admin.py frik ID СУММА        (Выдать FrikCoins)

2. Управление игроком (мгновенно):
   python admin.py role ID УРОВЕНЬ      (Выдать админку 1-7, 0 - снять)
   python admin.py title ID ТЕКСТ       (Выдать кастомный титул)
   python admin.py reset ID             (Полный сброс игрока)

3. Бизнесы (мгновенно):
   python admin.py biz ID ТИП           (Выдать бизнес: apteka1, banda, lombard и т.д.)
   python admin.py delbiz ТИП           (Забрать бизнес на аукцион)

4. Блокировки (мгновенно):
   python admin.py ban ID               (Забанить в боте)
   python admin.py unban ID             (Разбанить)
======================================================
""")

def set_money(uid, amount):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (big_normalize(amount), uid))
    print(f"✅ Баланс {uid} установлен на {amount}" if c.rowcount else f"❌ Игрок {uid} не найден!")
    conn.commit(); conn.close()

def set_frik(uid, amount):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE users SET frikcoins = COALESCE(frikcoins, 0) + ? WHERE user_id = ?", (amount, uid))
    print(f"✅ FrikCoins {uid} изменены на {amount}")
    conn.commit(); conn.close()

def set_role(uid, lvl):
    roles = {1: "admin_1", 2: "admin_2", 3: "admin_3", 4: "admin_4", 5: "admin_5", 6: "admin_6", 7: "admin_7"}
    conn = get_conn(); c = conn.cursor()
    if lvl == 0:
        c.execute("DELETE FROM staff_roles WHERE user_id = ?", (uid,))
        print(f"✅ Роль с {uid} снята.")
    else:
        rk = roles.get(lvl)
        if not rk: print("❌ Уровень 1-7 или 0"); return
        c.execute("INSERT OR REPLACE INTO staff_roles (user_id, role, added_by) VALUES (?, ?, 0)", (uid, rk))
        print(f"✅ Выдана роль {lvl} игроку {uid}")
    conn.commit(); conn.close()

def give_title(uid, text):
    conn = get_conn(); c = conn.cursor()
    tk = "custom_" + text[:30]
    c.execute("INSERT OR IGNORE INTO titles (user_id, title_key, custom_text) VALUES (?, ?, ?)", (uid, tk, text))
    print(f"✅ Титул '{text}' выдан {uid}")
    conn.commit(); conn.close()

def reset_user(uid):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE users SET balance = ?, frikcoins = 0, is_left = 0 WHERE user_id = ?", (big_normalize(15000000), uid))
    for t in ["titles", "title_stats", "case_stats", "roulette_bets", "crypto_portfolio", "staff_roles", "mutes", "bans"]:
        c.execute(f"DELETE FROM {t} WHERE user_id = ?", (uid,))
    conn.commit(); conn.close()
    print(f"✅ Игрок {uid} сброшен.")

def biz_give(uid, biz_type):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE biz_businesses SET owner_id = ?, status = 'owned', auction_end = NULL WHERE biz_type = ?", (uid, biz_type))
    print(f"✅ Бизнес {biz_type} выдан {uid}" if c.rowcount else "❌ Бизнес не найден")
    conn.commit(); conn.close()

def biz_take(biz_type):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE biz_businesses SET owner_id = 0, status = 'auction' WHERE biz_type = ?", (biz_type,))
    print(f"✅ Бизнес {biz_type} забран.")
    conn.commit(); conn.close()

def ban_user(uid, is_ban=True):
    conn = get_conn(); c = conn.cursor()
    if is_ban:
        c.execute("INSERT OR REPLACE INTO bans (user_id, reason, author_id, until) VALUES (?, 'Console Ban', 0, NULL)", (uid,))
        print(f"✅ Игрок {uid} забанен.")
    else:
        c.execute("DELETE FROM bans WHERE user_id = ?", (uid,))
        print(f"✅ Игрок {uid} разбанен.")
    conn.commit(); conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
    else:
        cmd = sys.argv[1].lower()
        try:
            if cmd == "money" and len(sys.argv) >= 4: set_money(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "frik" and len(sys.argv) >= 4: set_frik(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "role" and len(sys.argv) >= 4: set_role(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "title" and len(sys.argv) >= 4: give_title(int(sys.argv[2]), " ".join(sys.argv[3:]))
            elif cmd == "reset" and len(sys.argv) >= 3: reset_user(int(sys.argv[2]))
            elif cmd == "biz" and len(sys.argv) >= 4: biz_give(int(sys.argv[2]), sys.argv[3])
            elif cmd == "delbiz" and len(sys.argv) >= 3: biz_take(sys.argv[2])
            elif cmd == "ban" and len(sys.argv) >= 3: ban_user(int(sys.argv[2]), True)
            elif cmd == "unban" and len(sys.argv) >= 3: ban_user(int(sys.argv[2]), False)
            else:
                print("❌ Ошибка. Напиши 'python admin.py' для списка команд.")
        except Exception as e:
            print(f"❌ Ошибка: {e}")