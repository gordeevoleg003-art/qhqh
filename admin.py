import sqlite3
import sys
import datetime
import urllib.request
import json

DB_PATH = "game_bot.db"

# ⚠️ ВСТАВЬ СЮДА СВОЙ ТОКЕН ОТ BOTFATHER
BOT_TOKEN = "8703857750:AAGWCvf_kgaMyigpNSDfwyLFzS2Sl8ppLig" 

def big_normalize(value):
    try:
        v = int(value)
    except Exception:
        v = 0
    if v < 0: v = 0
    return str(v).zfill(100)

def get_conn():
    return sqlite3.connect(DB_PATH)

def send_tg_message(chat_id, text):
    if "ТВОЙ_ТОКЕН_ЗДЕСЬ" in BOT_TOKEN or not BOT_TOKEN:
        print("⚠️ Токен не указан, сообщение не отправлено.")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"⚠️ Ошибка отправки: {e}")

def show_help():
    print("""
======================================================
🛠 МЕГА-ПУЛЬТ УПРАВЛЕНИЯ (v5.0)
======================================================
1. Деньги и Валюта:
   money ID СУММА       (Установить баланс)
   addmoney ID СУММА    (Добавить к балансу)
   frik ID СУММА        (Установить FC)
   addfrik ID СУММА     (Добавить FC)

2. Модерация (с отправкой в ЛС):
   ban ID ДНИ ПРИЧИНА   (Забанить, 0 - навсегда)
   unban ID             (Разбанить)
   mute ID МИНУТЫ ПРИЧИНА (Мут на любое время)

3. Игрок:
   role ID УРОВЕНЬ      (Админка 1-7, 0 - снять)
   title ID ТЕКСТ       (Кастомный титул)
   deltitle ID ТЕКСТ    (Снять кастомный титул)
   reset ID             (Полный сброс)
   reset_cd ID          (Сброс кулдаунов)
   res ID wood 1000     (Ресурсы: wood, iron, diamond)
   card ID РЕДКОСТЬ     (Карточка: common, rare, epic, legendary)
   status ID КЛЮЧ       (Выдать статус: dark_lord, poseidon, moroznik)
   vip ID ДНИ           (Выдать VIP на N дней)
   fp ID УРОВЕНЬ        (Установить уровень FRIK PASS)

4. Бизнесы:
   biz ID ТИП           (Выдать: apteka1, banda, lombard...)
   delbiz ТИП           (Забрать на аукцион)

5. Экономика (Глобально):
   tax ПРОЦЕНТ          (Налог)
   treasury СУММА       (Казна)
   mafia ПРОЦЕНТ        (Лимит мафии)
   mafia_cur ПРОЦЕНТ    (Ставка мафии)
   clear_rozygrysh      (Отменить розыгрыш)
   clear_sbor           (Отменить сбор)
   clear_auctions       (Отменить аукционы)
======================================================
""")

# ==================== ФУНКЦИИ ====================

def set_money(uid, amount):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (big_normalize(amount), uid))
    print(f"✅ Баланс {uid} УСТАНОВЛЕН на {amount}" if c.rowcount else f"❌ Игрок не найден!")
    conn.commit(); conn.close()

def add_money(uid, amount):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    row = c.fetchone()
    if not row:
        print(f"❌ Игрок {uid} не найден!"); conn.close(); return
    cur = int(str(row[0]).lstrip('0') or '0')
    new_bal = cur + amount
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (big_normalize(new_bal), uid))
    print(f"✅ К балансу {uid} ДОБАВЛЕНО {amount}. Теперь: {new_bal}")
    conn.commit(); conn.close()

def set_frik(uid, amount):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE users SET frikcoins = ? WHERE user_id = ?", (amount, uid))
    print(f"✅ FrikCoins {uid} УСТАНОВЛЕНЫ на {amount}")
    conn.commit(); conn.close()

def add_frik(uid, amount):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE users SET frikcoins = COALESCE(frikcoins, 0) + ? WHERE user_id = ?", (amount, uid))
    print(f"✅ К FC {uid} ДОБАВЛЕНО {amount}")
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

def del_title(uid, text):
    conn = get_conn(); c = conn.cursor()
    tk = "custom_" + text[:30]
    c.execute("DELETE FROM titles WHERE user_id = ? AND title_key = ?", (uid, tk))
    print(f"✅ Титул '{text}' снят с {uid}")
    conn.commit(); conn.close()

def reset_user(uid):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE users SET balance = ?, frikcoins = 0, is_left = 0 WHERE user_id = ?", (big_normalize(15000000), uid))
    for t in ["titles", "title_stats", "case_stats", "roulette_bets", "crypto_portfolio", "staff_roles", "mutes", "bans", "user_vip", "user_statuses"]:
        c.execute(f"DELETE FROM {t} WHERE user_id = ?", (uid,))
    conn.commit(); conn.close()
    print(f"✅ Игрок {uid} полностью сброшен.")

def reset_cd(uid):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE users SET last_bonus = NULL WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM lombard_cooldowns WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM card_cooldowns WHERE user_id = ?", (uid,))
    conn.commit(); conn.close()
    print(f"✅ Кулдауны игрока {uid} сброшены.")

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

def ban_user(uid, days=0, reason="Console Ban"):
    conn = get_conn(); c = conn.cursor()
    until = None
    if days > 0:
        until = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT OR REPLACE INTO bans (user_id, reason, author_id, created_at, until) VALUES (?, ?, 0, ?, ?)", 
              (uid, reason, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), until))
    print(f"✅ Игрок {uid} забанен. Причина: {reason}. Срок: {'навсегда' if days == 0 else str(days) + ' дн.'}")
    conn.commit(); conn.close()
    
    msg = f"🚫 <b>ТЫ ЗАБАНЕН В БОТЕ</b>\n\n📅 Срок: {'навсегда' if days == 0 else str(days) + ' дн.'}\n📝 Причина: {reason}"
    send_tg_message(uid, msg)

def unban_user(uid):
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM bans WHERE user_id = ?", (uid,))
    print(f"✅ Игрок {uid} разбанен.")
    conn.commit(); conn.close()
    send_tg_message(uid, "✅ <b>Ты разбанен в боте!</b>")

def mute_user(uid, minutes=60, reason="Console Mute"):
    conn = get_conn(); c = conn.cursor()
    until = (datetime.datetime.now() + datetime.timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT OR REPLACE INTO mutes (user_id, until, reason, author_id) VALUES (?, ?, ?, 0)", (uid, until, reason))
    print(f"✅ Игрок {uid} замьючен на {minutes} минут.")
    conn.commit(); conn.close()
    
    msg = f"🔇 <b>Ты замьючен на {minutes} мин</b>\nПричина: {reason}"
    send_tg_message(uid, msg)

def set_tax(percent):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('tax_percent', ?)", (str(percent),))
    print(f"✅ Налог установлен: {percent}%")
    conn.commit(); conn.close()

def set_treasury(amount):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE treasury SET balance = ? WHERE chat_id = (SELECT chat_id FROM treasury LIMIT 1)", (big_normalize(amount),))
    print(f"✅ Казна установлена на {amount}")
    conn.commit(); conn.close()

def set_mafia(percent, is_current=False):
    conn = get_conn(); c = conn.cursor()
    col = "current_percent" if is_current else "max_percent"
    c.execute(f"UPDATE mafia_settings SET {col} = ? WHERE id = 1", (percent,))
    print(f"✅ Мафия ({col}) установлена на {percent}%")
    conn.commit(); conn.close()

def give_res(uid, res_type, amount):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT user_id FROM craft_resources WHERE user_id = ?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO craft_resources (user_id, wood, iron, diamond) VALUES (?, 0, 0, 0)", (uid,))
    c.execute(f"UPDATE craft_resources SET {res_type} = {res_type} + ? WHERE user_id = ?", (amount, uid))
    print(f"✅ Выдано {amount} {res_type} игроку {uid}")
    conn.commit(); conn.close()

def give_card(uid, rarity):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO user_cards (user_id, card_key, rarity) VALUES (?, 'custom_card', ?)", (uid, rarity))
    print(f"✅ Игроку {uid} выдана карточка редкости {rarity}")
    conn.commit(); conn.close()

def give_status(uid, key):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO user_statuses (user_id, status_key, awarded_by) VALUES (?, ?, 0)", (uid, key))
    print(f"✅ Игроку {uid} выдан статус {key}")
    conn.commit(); conn.close()

def give_vip(uid, days):
    conn = get_conn(); c = conn.cursor()
    until = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT OR REPLACE INTO user_vip (user_id, until) VALUES (?, ?)", (uid, until))
    print(f"✅ Игроку {uid} выдан VIP на {days} дней")
    conn.commit(); conn.close()

def set_fp_level(uid, level):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT id FROM fp_season WHERE status = 'active' LIMIT 1")
    season = c.fetchone()
    if not season:
        print("❌ Нет активного сезона FRIK PASS!"); conn.close(); return
    c.execute("UPDATE fp_progress SET level = ? WHERE user_id = ? AND season_id = ?", (level, uid, season[0]))
    print(f"✅ Игроку {uid} установлен уровень FRIK PASS: {level}")
    conn.commit(); conn.close()

def clear_rozygrysh():
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE rozygrysh SET status = 'cancelled' WHERE status = 'active'")
    c.execute("UPDATE biz_businesses SET status = 'owned' WHERE status = 'rozygrysh'")
    print("✅ Активный розыгрыш отменён.")
    conn.commit(); conn.close()

def clear_sbor():
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE sbor SET status = 'cancelled' WHERE status = 'active'")
    print("✅ Активный сбор отменён.")
    conn.commit(); conn.close()

def clear_auctions():
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE auctions SET status = 'cancelled' WHERE status = 'active'")
    c.execute("UPDATE biz_businesses SET status = 'owned', owner_id = 0, auction_end = NULL WHERE status = 'auction'")
    print("✅ Все аукционы отменены.")
    conn.commit(); conn.close()

def info_user(uid):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT balance, frikcoins FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone()
    if not u:
        print("❌ Игрок не найден."); return
    bal = int(str(u[0]).lstrip('0') or '0')
    fc = u[1] or 0
    print(f"👤 Игрок {uid}: Баланс: {bal}, FC: {fc}")
    conn.close()

def count_users():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE is_left = 0")
    print(f"👥 Всего активных игроков: {c.fetchone()[0]}")
    conn.close()

# ==================== ОБРАБОТКА КОМАНД ====================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
    else:
        cmd = sys.argv[1].lower()
        try:
            if cmd == "money" and len(sys.argv) >= 4: set_money(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "addmoney" and len(sys.argv) >= 4: add_money(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "frik" and len(sys.argv) >= 4: set_frik(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "addfrik" and len(sys.argv) >= 4: add_frik(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "role" and len(sys.argv) >= 4: set_role(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "title" and len(sys.argv) >= 4: give_title(int(sys.argv[2]), " ".join(sys.argv[3:]))
            elif cmd == "deltitle" and len(sys.argv) >= 4: del_title(int(sys.argv[2]), " ".join(sys.argv[3:]))
            elif cmd == "reset" and len(sys.argv) >= 3: reset_user(int(sys.argv[2]))
            elif cmd == "reset_cd" and len(sys.argv) >= 3: reset_cd(int(sys.argv[2]))
            elif cmd == "biz" and len(sys.argv) >= 4: biz_give(int(sys.argv[2]), sys.argv[3])
            elif cmd == "delbiz" and len(sys.argv) >= 3: biz_take(sys.argv[2])
            elif cmd == "ban" and len(sys.argv) >= 3:
                uid = int(sys.argv[2])
                days = int(sys.argv[3]) if len(sys.argv) >= 4 else 0
                reason = " ".join(sys.argv[4:]) if len(sys.argv) >= 5 else "Console Ban"
                ban_user(uid, days, reason)
            elif cmd == "unban" and len(sys.argv) >= 3: unban_user(int(sys.argv[2]))
            elif cmd == "mute" and len(sys.argv) >= 4:
                uid = int(sys.argv[2])
                minutes = int(sys.argv[3])
                reason = " ".join(sys.argv[4:]) if len(sys.argv) >= 5 else "Console Mute"
                mute_user(uid, minutes, reason)
            elif cmd == "tax" and len(sys.argv) >= 3: set_tax(int(sys.argv[2]))
            elif cmd == "treasury" and len(sys.argv) >= 3: set_treasury(int(sys.argv[2]))
            elif cmd == "mafia" and len(sys.argv) >= 3: set_mafia(int(sys.argv[2]), False)
            elif cmd == "mafia_cur" and len(sys.argv) >= 3: set_mafia(int(sys.argv[2]), True)
            elif cmd == "res" and len(sys.argv) >= 5: give_res(int(sys.argv[2]), sys.argv[3], int(sys.argv[4]))
            elif cmd == "card" and len(sys.argv) >= 4: give_card(int(sys.argv[2]), sys.argv[3])
            elif cmd == "status" and len(sys.argv) >= 4: give_status(int(sys.argv[2]), sys.argv[3])
            elif cmd == "vip" and len(sys.argv) >= 4: give_vip(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "fp" and len(sys.argv) >= 4: set_fp_level(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "clear_rozygrysh": clear_rozygrysh()
            elif cmd == "clear_sbor": clear_sbor()
            elif cmd == "clear_auctions": clear_auctions()
            elif cmd == "info" and len(sys.argv) >= 3: info_user(int(sys.argv[2]))
            elif cmd == "count_users": count_users()
            else:
                print("❌ Ошибка. Напиши 'python admin.py' для списка команд.")
        except Exception as e:
            print(f"❌ Ошибка: {e}")