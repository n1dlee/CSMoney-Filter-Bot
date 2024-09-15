import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
from main import collect_data

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class FilterState(StatesGroup):
    category = State()
    weapon_types = State()
    min_price = State()
    max_price = State()
    quality = State()
    stattrak = State()
    browsing = State()

weapon_categories = {
    "Ножи 🔪": ["Bayonet", "Bowie", "Butterfly", "Falchion", "Flip", "Gut", "Huntsman", "Karambit", "M9 Bayonet", 
             "Navaja", "Shadow Daggers", "Stiletto", "Talon", "Ursus", "Classic", "Skeleton", "Nomad", "Survival", "Kukri", "Paracord"],
    "Винтовки 🔫": ["AK-47", "AUG", "FAMAS", "Galil AR", "M4A1-S", "M4A4", "SG 553"],
    "Пистолеты 🔫": ["CZ75-Auto", "Desert Eagle", "Dual Berettas", "Five-SeveN", "Glock-18", "P2000", "P250", "R8 Revolver", "Tec-9", "USP-S"],
    "Пистолеты-пулеметы 🔫": ["MP9", "MAC-10", "MP7", "UMP-45", "P90", "PP-Bizon"],
    "Дробовики 🔫": ["MAG-7", "Nova", "XM1014", "Sawed-Off"],
    "Пулеметы 🔫": ["Negev", "M249"]
}

@dp.message(Command(commands=['start', 'help']))
async def send_welcome(message: Message):
    await message.reply("Добро пожаловать в CS.Money Bot! 🎮\nИспользуйте /filter для начала настройки фильтров поиска. 🔍")

@dp.message(Command(commands=['filter']))
async def start_filter(message: Message, state: FSMContext):
    keyboard = InlineKeyboardBuilder()
    for category in weapon_categories.keys():
        keyboard.add(InlineKeyboardButton(text=category, callback_data=f"category_{category.split()[0]}"))
    keyboard.adjust(2)
    await message.reply("Выберите категорию оружия: 🎯", reply_markup=keyboard.as_markup())
    await state.set_state(FilterState.category)

@dp.callback_query(FilterState.category)
async def process_category(callback_query: types.CallbackQuery, state: FSMContext):
    category = callback_query.data.split('_')[1]
    await state.update_data(category=category)
    
    keyboard = InlineKeyboardBuilder()
    for weapon in weapon_categories[f"{category} 🔪" if category == "Ножи" else f"{category} 🔫"]:
        keyboard.add(InlineKeyboardButton(text=weapon, callback_data=f"weapon_{weapon}"))
    keyboard.add(InlineKeyboardButton(text="✅ Готово", callback_data="weapons_done"))
    keyboard.adjust(2)
    
    await callback_query.message.edit_text(f"Выбрана категория: {category} 🎯\nВыберите типы оружия (можно несколько):", reply_markup=keyboard.as_markup())
    await state.set_state(FilterState.weapon_types)

@dp.callback_query(FilterState.weapon_types)
async def process_weapon_types(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "weapons_done":
        await process_weapons_done(callback_query, state)
        return

    weapon_type = callback_query.data.split('_')[1]
    current_data = await state.get_data()
    weapon_types = current_data.get('weapon_types', [])
    
    if weapon_type in weapon_types:
        weapon_types.remove(weapon_type)
    else:
        weapon_types.append(weapon_type)
    
    await state.update_data(weapon_types=weapon_types)
    
    category = current_data['category']
    keyboard = InlineKeyboardBuilder()
    for weapon in weapon_categories[f"{category} 🔪" if category == "Ножи" else f"{category} 🔫"]:
        keyboard.add(InlineKeyboardButton(
            text=f"✅ {weapon}" if weapon in weapon_types else weapon,
            callback_data=f"weapon_{weapon}"
        ))
    keyboard.add(InlineKeyboardButton(text="✅ Готово", callback_data="weapons_done"))
    keyboard.adjust(2)
    
    await callback_query.message.edit_text(
        f"Выбранные типы оружия: {', '.join(weapon_types)}\nВыберите еще или нажмите 'Готово':",
        reply_markup=keyboard.as_markup()
    )

async def process_weapons_done(callback_query: types.CallbackQuery, state: FSMContext):
    current_data = await state.get_data()
    weapon_types = current_data.get('weapon_types', [])
    if not weapon_types:
        await callback_query.answer("Выберите хотя бы один тип оружия! 🚫", show_alert=True)
        return
    await callback_query.message.edit_text("Введите минимальную цену: 💰")
    await state.set_state(FilterState.min_price)

@dp.message(FilterState.min_price)
async def process_min_price(message: Message, state: FSMContext):
    try:
        min_price = int(message.text)
        await state.update_data(min_price=min_price)
        await message.reply("Введите максимальную цену: 💰")
        await state.set_state(FilterState.max_price)
    except ValueError:
        await message.reply("Пожалуйста, введите корректное целое число для минимальной цены. 🚫")

@dp.message(FilterState.max_price)
async def process_max_price(message: Message, state: FSMContext):
    try:
        max_price = int(message.text)
        await state.update_data(max_price=max_price)
        keyboard = InlineKeyboardBuilder()
        qualities = ["FN", "MW", "FT", "WW", "BS"]
        for quality in qualities:
            keyboard.add(InlineKeyboardButton(text=quality, callback_data=f"quality_{quality}"))
        keyboard.add(InlineKeyboardButton(text="✅ Готово", callback_data="quality_done"))
        keyboard.adjust(3)
        await message.reply("Выберите качество (можно несколько): 🌟", reply_markup=keyboard.as_markup())
        await state.set_state(FilterState.quality)
    except ValueError:
        await message.reply("Пожалуйста, введите корректное целое число для максимальной цены. 🚫")

@dp.callback_query(FilterState.quality)
async def process_quality(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "quality_done":
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="Да ✅", callback_data="stattrak_yes"))
        keyboard.add(InlineKeyboardButton(text="Нет ❌", callback_data="stattrak_no"))
        await callback_query.message.edit_text("Хотите StatTrak предметы? 🔢", reply_markup=keyboard.as_markup())
        await state.set_state(FilterState.stattrak)
        return

    quality = callback_query.data.split('_')[1].lower()
    current_data = await state.get_data()
    qualities = current_data.get('qualities', [])
    
    if quality in qualities:
        qualities.remove(quality)
    else:
        qualities.append(quality)
    
    await state.update_data(qualities=qualities)
    
    keyboard = InlineKeyboardBuilder()
    for q in ["FN", "MW", "FT", "WW", "BS"]:
        keyboard.add(InlineKeyboardButton(
            text=f"✅ {q}" if q.lower() in qualities else q,
            callback_data=f"quality_{q}"
        ))
    keyboard.add(InlineKeyboardButton(text="✅ Готово", callback_data="quality_done"))
    keyboard.adjust(3)
    
    await callback_query.message.edit_text(
        f"Выбранные качества: {', '.join(qualities)}\nВыберите еще или нажмите 'Готово':",
        reply_markup=keyboard.as_markup()
    )

@dp.callback_query(FilterState.stattrak)
async def process_stattrak(callback_query: types.CallbackQuery, state: FSMContext):
    stattrak = callback_query.data.split('_')[1]
    await state.update_data(stattrak=True if stattrak == 'yes' else None)
    await callback_query.message.edit_text("Спасибо за ввод фильтров. Начинаю поиск предметов... 🔎")
    await get_deals(callback_query.message, state)

async def get_deals(message: Message, state: FSMContext):
    data = await state.get_data()
    offset = data.get('offset', 0)
    deals = collect_data(
        weapon_types=data['weapon_types'],
        min_price=data['min_price'],
        max_price=data['max_price'],
        qualities=data.get('qualities', []),
        stattrak=data['stattrak'],
        offset=offset,
        batch_size=5
    )
    
    if not deals:
        await message.reply("Не найдено предметов, соответствующих вашим критериям. 😕")
        return

    for deal in deals:
        float_value = deal.get('float')
        if float_value is not None:
            try:
                float_string = f"{float(float_value):.4f}"
            except (ValueError, TypeError):
                float_string = str(float_value)
        else:
            float_string = "N/A"
        
        deal_message = (
            f"Предмет: {deal['full']} 🎨\n"
            f"Цена: ${deal['default']:.2f} 💰\n"
            f"Скидка: {deal['discount']:.2%} 🏷️\n"
            f"Float: {float_string} 📊\n"
            f"Ссылка на 3D: {deal['links']['3d']} 🔗\n"
            f"Ссылка на изображение: {deal['asset']['images']['screenshot']} 🖼️"
        )
        await message.reply(deal_message)

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Загрузить еще ⏬", callback_data="load_more"))
    keyboard.add(InlineKeyboardButton(text="Стоп 🛑", callback_data="stop_browsing"))
    await message.reply("Что дальше?", reply_markup=keyboard.as_markup())
    
    await state.update_data(offset=offset + 5)
    await state.set_state(FilterState.browsing)

@dp.callback_query(FilterState.browsing)
async def process_browsing(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "load_more":
        await callback_query.message.edit_text("Загружаю еще предметы... 🔄")
        await get_deals(callback_query.message, state)
    elif callback_query.data == "stop_browsing":
        await callback_query.message.edit_text("Поиск остановлен. Используйте /filter для нового поиска. 🔍")
        await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
