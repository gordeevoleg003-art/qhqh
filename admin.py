import sqlite3
import sys
import datetime
import urllib.request
import json
import os
import shutil

DB_PATH = "game_bot.db"
# ⚠️ Впиши свой токен, если хочешь, чтобы бот присылал уведомления игрокам
BOT_TOKEN = "8703857750:AAGWCvf_kgaMyigpNSDfwyLFzS2Sl8ppLig" 

def big_normalize(value):
    try: v = int(value)
    except: v = 0
    if v < 0: v = 0
    return str(v).zfill(100)

def get_conn(): return sqlite3.connect(DB_PATH)

def send_tg_message(chat_id, text):
    if "ТВОЙ_ТОКЕН_ЗДЕСЬ" in BOT_TOKEN or not BOT_TOKEN: return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=5)
    except: pass

def show_help():
    print("""
======================================================
🛠 МЕГА-ПУЛЬТ УПРАВЛЕНИЯ (v8.0)
======================================================
1. Игроки и Экономика:
   money/addmoney/frik/addfrik, role, title, reset, reset_cd, res, card, status, vip
   tax, treasury, mafia, clear_auctions, setmult, freeze, unfreeze

2. Модерация и Массовые действия:
   ban ID ДНИ ПРИЧИНА, unban ID, mute ID МИНУТЫ ПРИЧИНА
   unmuteall, banlist, mutelist
   allmoney СУММА (Выдать всем), giftall КЕЙС (Выдать кейс всем)

3. 📊 АНАЛИТИКА:
   logs ID (Полный лог), spy ID (Транзакции), top (Топ-10), checkdb, dbbackup

4. 👨‍👩‍👧 СЕМЬИ (НОВОЕ):
   setfamily ID ИМЯ, kickfamily ID
   family_season_start (Обнулить репутацию)
   family_season_end (Выдать награды Топ-10)

5. ⚠️ HARD RESET:
   hardreset (ПОЛНЫЙ СБРОС ВСЕГО)
======================================================
""")

# --- ИГРОКИ ---
def set_money(uid, amount):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (big_normalize(amount), uid))
    print(f"✅ Баланс {uid} УСТАНОВЛЕН на {amount}" if c.rowcount else f"❌ Игрок не найден!")
    conn.commit(); conn.close()

def add_money(uid, amount):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    row = c.fetchone()
    if not row: print(f"❌ Игрок {uid} не найден!"); conn.close(); return
    cur = int(str(row[0]).lstrip('0') or '0')
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (big_normalize(cur + amount), uid))
    print(f"✅ К балансу {uid} ДОБАВЛЕНО {amount}. Теперь: {cur + amount}")
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

def reset_user(uid):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE users SET balance = ?, frikcoins = 0, is_left = 0 WHERE user_id = ?", (big_normalize(15000000), uid))
    for t in ["titles", "title_stats", "case_stats", "roulette_bets", "crypto_portfolio", "staff_roles", "mutes", "bans", "user_vip", "user_statuses", "user_cards", "card_cooldowns"]:
        try: c.execute(f"DELETE FROM {t} WHERE user_id = ?", (uid,))
        except: pass
    conn.commit(); conn.close()
    print(f"✅ Игрок {uid} полностью сброшен (баланс 15кк).")

def reset_cd(uid):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE users SET last_bonus = NULL WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM lombard_cooldowns WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM card_cooldowns WHERE user_id = ?", (uid,))
    conn.commit(); conn.close()
    print(f"✅ Кулдауны игрока {uid} сброшены.")

def give_res(uid, res_type, amount):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT user_id FROM craft_resources WHERE user_id = ?", (uid,))
    if not c.fetchone(): c.execute("INSERT INTO craft_resources (user_id) VALUES (?)", (uid,))
    c.execute(f"UPDATE craft_resources SET {res_type} = {res_type} + ? WHERE user_id = ?", (amount, uid))
    print(f"✅ Выдано {amount} {res_type} игроку {uid}")
    conn.commit(); conn.close()

def give_card(uid, rarity):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO user_cards (user_id, card_key, rarity) VALUES (?, 'custom_card', ?)", (uid, rarity))
    print(f"✅ Игроку {uid} выдана карточка редкости {rarity}")
    conn.commit(); conn.close()

def give_card_silent(uid, card_key, rarity):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO user_cards (user_id, card_key, rarity) VALUES (?, ?, ?)", (uid, card_key, rarity))
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

def set_player_multiplier(uid, percent):
    if percent < 0: percent = 0
    if percent > 1000: percent = 1000
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"user_mult_{uid}", str(percent)))
    conn.commit(); conn.close()
    print(f"✅ Игроку {uid} установлен множитель {percent}% (x{percent/100}).")

def freeze_player(uid, minutes):
    conn = get_conn(); c = conn.cursor()
    until = (datetime.datetime.now() + datetime.timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"user_freeze_{uid}", until))
    conn.commit(); conn.close()
    print(f"✅ Игрок {uid} заморожен на {minutes} минут.")

def unfreeze_player(uid):
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM settings WHERE key = ?", (f"user_freeze_{uid}",))
    conn.commit(); conn.close()
    print(f"✅ Игрок {uid} разморожен.")

# --- МОДЕРАЦИЯ ---
def ban_user(uid, days=0, reason="Console Ban"):
    conn = get_conn(); c = conn.cursor()
    until = None
    if days > 0: until = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT OR REPLACE INTO bans (user_id, reason, author_id, created_at, until) VALUES (?, ?, 0, ?, ?)", 
              (uid, reason, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), until))
    conn.commit(); conn.close()
    print(f"✅ Игрок {uid} забанен.")
    send_tg_message(uid, f"🚫 <b>ТЫ ЗАБАНЕН В БОТЕ</b>\n\n📅 Срок: {'навсегда' if days == 0 else str(days) + ' дн.'}\n📝 Причина: {reason}")

def unban_user(uid):
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM bans WHERE user_id = ?", (uid,))
    conn.commit(); conn.close()
    print(f"✅ Игрок {uid} разбанен.")
    send_tg_message(uid, "✅ <b>Ты разбанен в боте!</b>")

def mute_user(uid, minutes=60, reason="Console Mute"):
    conn = get_conn(); c = conn.cursor()
    until = (datetime.datetime.now() + datetime.timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT OR REPLACE INTO mutes (user_id, until, reason, author_id) VALUES (?, ?, ?, 0)", (uid, until, reason))
    conn.commit(); conn.close()
    print(f"✅ Игрок {uid} замьючен на {minutes} минут.")
    send_tg_message(uid, f"🔇 <b>Ты замьючен на {minutes} мин</b>\nПричина: {reason}")

def unmute_all():
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM mutes")
    conn.commit(); conn.close()
    print("✅ Все муты сняты.")

def ban_list():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT user_id, until, reason FROM bans")
    rows = c.fetchall()
    print("📋 СПИСОК ЗАБАНЕННЫХ:")
    if not rows: print("  Пусто.")
    for r in rows: print(f"  ID: {r[0]} | До: {r[1]} | Причина: {r[2]}")
    conn.close()

def mute_list():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT user_id, until, reason FROM mutes")
    rows = c.fetchall()
    print("📋 СПИСОК ЗАМЬЮЧЕННЫХ:")
    if not rows: print("  Пусто.")
    for r in rows: print(f"  ID: {r[0]} | До: {r[1]} | Причина: {r[2]}")
    conn.close()

# --- ЭКОНОМИКА ---
def set_tax(percent):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('tax_percent', ?)", (str(percent),))
    conn.commit(); conn.close()
    print(f"✅ Налог установлен: {percent}%")

def set_treasury(amount):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE treasury SET balance = ? WHERE chat_id = (SELECT chat_id FROM treasury LIMIT 1)", (big_normalize(amount),))
    conn.commit(); conn.close()
    print(f"✅ Казна установлена на {amount}")

def set_mafia(percent, is_current=False):
    conn = get_conn(); c = conn.cursor()
    col = "current_percent" if is_current else "max_percent"
    c.execute(f"UPDATE mafia_settings SET {col} = ? WHERE id = 1", (percent,))
    conn.commit(); conn.close()
    print(f"✅ Мафия ({col}) установлена на {percent}%")

def clear_auctions():
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE auctions SET status = 'cancelled' WHERE status = 'active'")
    c.execute("UPDATE biz_businesses SET status = 'owned', owner_id = 0, auction_end = NULL WHERE status = 'auction'")
    conn.commit(); conn.close()
    print("✅ Все аукционы отменены.")

def all_money(amount):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT user_id, balance FROM users WHERE is_left = 0")
    users = c.fetchall()
    count = 0
    for uid, bal_str in users:
        cur = int(str(bal_str).lstrip('0') or '0')
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (big_normalize(cur + amount), uid))
        count += 1
    conn.commit(); conn.close()
    print(f"✅ Выдано по {amount} поинтов {count} активным игрокам.")

# --- БИЗНЕСЫ ---
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

# --- СЕМЬИ ---
def set_family_name(uid, new_name):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT family_id FROM family_members WHERE user_id = ?", (uid,))
    row = c.fetchone()
    if not row: print(f"❌ Игрок {uid} не в семье."); conn.close(); return
    c.execute("UPDATE families SET name = ? WHERE id = ?", (new_name, row[0]))
    conn.commit(); conn.close()
    print(f"✅ Название семьи изменено на '{new_name}'.")

def kick_from_family(uid):
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM family_members WHERE user_id = ?", (uid,))
    if c.rowcount > 0: print(f"✅ Игрок {uid} выгнан из семьи.")
    else: print(f"❌ Игрок {uid} не был в семье.")
    conn.commit(); conn.close()

def start_family_season():
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE families SET reputation = 0, last_duel = NULL")
    c.execute("SELECT value FROM settings WHERE key = 'family_season_number'")
    row = c.fetchone()
    current_season = int(row[0]) if row and row[0].isdigit() else 1
    new_season = current_season + 1
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('family_season_number', ?)", (str(new_season),))
    conn.commit(); conn.close()
    print(f"🏁 НОВЫЙ СЕЗОН СЕМЕЙ #{new_season} ЗАПУЩЕН! Репутация обнулена.")

def end_family_season_and_reward():
    print("🏆 ЗАВЕРШЕНИЕ СЕЗОНА СЕМЕЙ (ТОП-10)...")
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT id, name, owner_id, reputation FROM families ORDER BY reputation DESC LIMIT 10")
    top_families = c.fetchall()
    if not top_families: print("❌ Семей нет."); conn.close(); return

    rewards = {
        1: {"points": 300_000_000, "card": "akashi", "rarity": "legendary", "title": "👑 Сезонный Чемпион"},
        2: {"points": 200_000_000, "card": "kuroko_rare", "rarity": "rare", "title": "🥈 Вице-Чемпион"},
        3: {"points": 150_000_000, "card": "aomine", "rarity": "epic", "title": "🥉 Бронза"},
        4: {"points": 100_000_000, "card": "murasakibara", "rarity": "epic", "title": "Топ-4"},
        5: {"points": 90_000_000, "card": "midorima", "rarity": "epic", "title": "Топ-5"},
        6: {"points": 75_000_000, "card": "kise", "rarity": "rare", "title": "Топ-6"},
        7: {"points": 60_000_000, "card": "momoi", "rarity": "rare", "title": "Топ-7"},
        8: {"points": 50_000_000, "card": "riko", "rarity": "common", "title": "Топ-8"},
        9: {"points": 40_000_000, "card": "hyuga", "rarity": "common", "title": "Топ-9"},
        10: {"points": 30_000_000, "card": "izuki", "rarity": "common", "title": "Топ-10"}
    }

    for place, (fam_id, fam_name, owner_id, rep) in enumerate(top_families, 1):
        rew = rewards.get(place)
        if not rew: continue
        print(f"🏅 Место {place}: '{fam_name}' (ID: {owner_id})")
        c.execute("SELECT balance FROM users WHERE user_id = ?", (owner_id,))
        row = c.fetchone()
        if row:
            cur = int(str(row[0]).lstrip('0') or '0')
            c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (big_normalize(cur + rew["points"]), owner_id))
        give_card_silent(owner_id, rew["card"], rew["rarity"])
        if rew["title"]: c.execute("INSERT OR IGNORE INTO titles (user_id, title_key, custom_text) VALUES (?, ?, ?)", (owner_id, f"custom_{rew['title']}", rew["title"]))
    conn.commit(); conn.close()
    print("\n✅ НАГРАДЫ ТОП-10 ВЫДАНЫ!")

# --- АНАЛИТИКА ---
def show_logs(uid):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT first_name, username, registered, last_active FROM users WHERE user_id = ?", (uid,))
    u = c.fetchone()
    if not u: print("❌ Игрок не найден."); return
    print(f"👤 {u[0]} (@{u[1]}) | ID: {uid}")
    c.execute("SELECT case_type, opens FROM case_stats WHERE user_id = ?", (uid,))
    cases = c.fetchall()
    if cases:
        print("\n📦 КЕЙСЫ:")
        for row in cases: print(f"  {row[0]}: {row[1]}")
    c.execute("SELECT roulette_wins, roulette_losses FROM title_stats WHERE user_id = ?", (uid,))
    stats = c.fetchone()
    if stats: print(f"\n🎰 Рулетка: Побед {stats[0]}, Проигрышей {stats[1]}")
    conn.close()

def spy_user(uid):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT amount, type, details, timestamp FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 10", (uid,))
    trans = c.fetchall()
    print(f"🕵️ ШПИОНАЖ ID {uid}:")
    if not trans: print("  Нет транзакций.")
    for t in trans: print(f"  {t[3]} | {t[1]} | {int(str(t[0]).lstrip('0') or '0')} | {t[2]}")
    conn.close()

def show_top():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT user_id, first_name, balance FROM users WHERE is_left = 0 ORDER BY CAST(balance AS INTEGER) DESC LIMIT 10")
    top = c.fetchall()
    print("\n🏆 ТОП-10 ИГРОКОВ:")
    for i, row in enumerate(top, 1):
        print(f"  {i}. {row[1]} (ID: {row[0]}) — {int(str(row[2]).lstrip('0') or '0')}")
    conn.close()

def db_backup():
    if not os.path.exists("backups"): os.makedirs("backups")
    backup_name = f"backups/game_bot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    try:
        shutil.copy2("game_bot.db", backup_name)
        print(f"✅ Резервная копия: {backup_name}")
    except Exception as e: print(f"❌ Ошибка бэкапа: {e}")

def check_db():
    conn = get_conn(); c = conn.cursor()
    c.execute("PRAGMA integrity_check;")
    print(f"🔍 Проверка БД: {c.fetchone()[0]}")
    conn.close()

def hard_reset():
    conn = get_conn(); c = conn.cursor()
    print("⚠️ НАЧАТ ПОЛНЫЙ СБРОС БАЗЫ...")
    tables = ["transactions", "roulette_history", "duels", "invites", "promocodes", "promo_uses", "case_stats", "special_cases", "rl_blocks", "titles", "title_stats", "roulette_bets", "roulette_last_bets", "auctions", "auction_bets", "families", "family_members", "family_invites", "family_duels", "family_season", "biz_businesses", "biz_history", "biz_player_apteka", "biz_player_bolnitsa", "biz_trades", "biz_daily_stats", "biz_upgrades", "lombard_loans", "lombard_cooldowns", "lombard_block", "rozygrysh", "rozygrysh_tickets", "rozygrysh_cooldown", "craft_resources", "craft_buffs", "craft_history", "user_states_db", "users_left", "spam_bans", "fake_money_log", "court_cases", "court_judge_requests", "frozen_money", "league_bets", "shield_list", "sbor", "sbor_bets", "polls", "poll_votes", "poll_messages", "advokats", "advokat_deals", "advokat_requests", "biz_trades", "house_trades", "crypto_coins", "crypto_portfolio", "crypto_history", "fp_season", "fp_progress", "fp_history", "staff_roles", "help_questions", "help_stats", "staff_log", "title_give_log", "warnings", "mutes", "bans", "event_active", "event_tickets", "user_snowballs", "user_statuses", "event_games", "event_game_players", "event_game_history", "event_case_log", "containers", "container_bets", "mystic_titles", "container_history", "user_vip", "family_shield", "fake_balance", "user_cards", "card_cooldowns", "card_history"]
    for t in tables:
        try: c.execute(f"DELETE FROM {t}")
        except: pass
    c.execute("UPDATE users SET balance = '0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000', frikcoins = 0, is_left = 0")
    c.execute("UPDATE treasury SET balance = '0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'")
    c.execute("UPDATE settings SET value = '5' WHERE key = 'tax_percent'")
    c.execute("UPDATE mafia_settings SET max_percent = 20, current_percent = 20")
    c.execute("UPDATE houses SET owner_id = 0, bought_at = NULL")
    c.execute("DELETE FROM phones")
    c.execute("DELETE FROM biz_businesses")
    auction_end = (datetime.datetime.now() + datetime.timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")
    for bt, name in [('apteka1', '🏥 Аптека №1'), ('apteka2', '🏥 Аптека №2'), ('apteka3', '🏥 Аптека №3'), ('bolnitsa1', '🩺 Больница №1'), ('bolnitsa2', '🩺 Больница №2'), ('banda', '🔫 Банда'), ('sud1', '⚖️ Суд №1'), ('sud2', '⚖️ Суд №2'), ('advokat', '⚖️ Адвокатская контора'), ('lombard', '🏪 Ломбард')]:
        c.execute("INSERT INTO biz_businesses (biz_type, name, min_bet, status, auction_end) VALUES (?, ?, '200000000', 'auction', ?)", (bt, name, auction_end))
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO biz_businesses (biz_type, name, min_bet, owner_id, status, last_payment) VALUES ('mafia', '🎩 Мафия', '200000000', 6548175188, 'owned', ?)", (now_str,))
    c.execute("INSERT INTO biz_businesses (biz_type, name, min_bet, owner_id, status, last_payment) VALUES ('league', '⚽ Лига чемпионов', '200000000', 6548175188, 'owned', ?)", (now_str,))
    conn.commit(); conn.close()
    print("✅ ПОЛНЫЙ СБРОС ЗАВЕРШЕН!")

if __name__ == "__main__":
    if len(sys.argv) < 2: show_help()
    else:
        cmd = sys.argv[1].lower()
        try:
            if cmd == "money" and len(sys.argv) >= 4: set_money(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "addmoney" and len(sys.argv) >= 4: add_money(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "frik" and len(sys.argv) >= 4: set_frik(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "addfrik" and len(sys.argv) >= 4: add_frik(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "role" and len(sys.argv) >= 4: set_role(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "title" and len(sys.argv) >= 4: give_title(int(sys.argv[2]), " ".join(sys.argv[3:]))
            elif cmd == "reset" and len(sys.argv) >= 3: reset_user(int(sys.argv[2]))
            elif cmd == "reset_cd" and len(sys.argv) >= 3: reset_cd(int(sys.argv[2]))
            elif cmd == "res" and len(sys.argv) >= 5: give_res(int(sys.argv[2]), sys.argv[3], int(sys.argv[4]))
            elif cmd == "card" and len(sys.argv) >= 4: give_card(int(sys.argv[2]), sys.argv[3])
            elif cmd == "status" and len(sys.argv) >= 4: give_status(int(sys.argv[2]), sys.argv[3])
            elif cmd == "vip" and len(sys.argv) >= 4: give_vip(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "setmult" and len(sys.argv) >= 4: set_player_multiplier(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "freeze" and len(sys.argv) >= 4: freeze_player(int(sys.argv[2]), int(sys.argv[3]))
            elif cmd == "unfreeze" and len(sys.argv) >= 3: unfreeze_player(int(sys.argv[2]))
            elif cmd == "ban" and len(sys.argv) >= 3:
                uid = int(sys.argv[2]); days = int(sys.argv[3]) if len(sys.argv) >= 4 else 0
                reason = " ".join(sys.argv[4:]) if len(sys.argv) >= 5 else "Console Ban"
                ban_user(uid, days, reason)
            elif cmd == "unban" and len(sys.argv) >= 3: unban_user(int(sys.argv[2]))
            elif cmd == "mute" and len(sys.argv) >= 4:
                uid = int(sys.argv[2]); minutes = int(sys.argv[3])
                reason = " ".join(sys.argv[4:]) if len(sys.argv) >= 5 else "Console Mute"
                mute_user(uid, minutes, reason)
            elif cmd == "unmuteall": unmute_all()
            elif cmd == "banlist": ban_list()
            elif cmd == "mutelist": mute_list()
            elif cmd == "tax" and len(sys.argv) >= 3: set_tax(int(sys.argv[2]))
            elif cmd == "treasury" and len(sys.argv) >= 3: set_treasury(int(sys.argv[2]))
            elif cmd == "mafia" and len(sys.argv) >= 3: set_mafia(int(sys.argv[2]), False)
            elif cmd == "mafia_cur" and len(sys.argv) >= 3: set_mafia(int(sys.argv[2]), True)
            elif cmd == "clear_auctions": clear_auctions()
            elif cmd == "allmoney" and len(sys.argv) >= 3: all_money(int(sys.argv[2]))
            elif cmd == "biz" and len(sys.argv) >= 4: biz_give(int(sys.argv[2]), sys.argv[3])
            elif cmd == "delbiz" and len(sys.argv) >= 3: biz_take(sys.argv[2])
            elif cmd == "setfamily" and len(sys.argv) >= 4: set_family_name(int(sys.argv[2]), " ".join(sys.argv[3:]))
            elif cmd == "kickfamily" and len(sys.argv) >= 3: kick_from_family(int(sys.argv[2]))
            elif cmd == "family_season_start": start_family_season()
            elif cmd == "family_season_end": end_family_season_and_reward()
            elif cmd == "logs" and len(sys.argv) >= 3: show_logs(int(sys.argv[2]))
            elif cmd == "spy" and len(sys.argv) >= 3: spy_user(int(sys.argv[2]))
            elif cmd == "top": show_top()
            elif cmd == "dbbackup": db_backup()
            elif cmd == "checkdb": check_db()
            elif cmd == "hardreset": hard_reset()
            else: print("❌ Ошибка. Напиши 'python admin.py' для списка команд.")
        except Exception as e: print(f"❌ Ошибка: {e}")