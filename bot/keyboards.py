from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def build_delete_keyboard(uid, delete_state):
    rows = delete_state[uid]["targetRows"]
    selected = delete_state[uid]["selectedIds"]
    keyboard = []
    for r in rows:
        label = f"🟢 SELECTED | {r['itemName']} | ₹{r['expenseAmount']}" if r["rowId"] in selected else f"🔴 SELECT | {r['itemName']} | ₹{r['expenseAmount']}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"del|{r['rowId']}")])
    keyboard.append([InlineKeyboardButton("🗑 CONFIRM DELETE", callback_data="del|confirm")])
    return InlineKeyboardMarkup(keyboard)

def build_category_keyboard(categories):
    return [[InlineKeyboardButton(c, callback_data=f"cat|{c}") for c in categories[i:i+2]] for i in range(0, len(categories), 2)]
