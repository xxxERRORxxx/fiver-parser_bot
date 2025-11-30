import os
import logging
import asyncio
import aiohttp
import random
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', "8298039933:AAH0itPeYuE2yGP4y3-dfirU0klHkLG37hc")
CHANNEL_USERNAME = "@sexyparser"
CHANNEL_LINK = "https://t.me/sexyparser"

class RealFiverrParser:
    async def get_real_listings(self, quantity):
        """РЕАЛЬНЫЙ ПАРСИНГ FIVERR"""
        try:
            listings = []
            async with aiohttp.ClientSession() as session:
                # Реальные категории Fiverr
                categories = [
                    "graphics-design", "digital-marketing", "writing-translation",
                    "video-animation", "music-audio", "programming-tech"
                ]
                
                for category in categories:
                    if len(listings) >= quantity:
                        break
                    
                    # Парсим через Fiverr API
                    url = f"https://www.fiverr.com/api/v1/gigs?category={category}&limit=20"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                    
                    try:
                        async with session.get(url, headers=headers, timeout=10) as response:
                            if response.status == 200:
                                data = await response.json()
                                gigs = data.get('gigs', [])
                                
                                for gig in gigs:
                                    if len(listings) >= quantity:
                                        break
                                    
                                    # Проверяем что отзывов 0
                                    if gig.get('rating', {}).get('reviews_count', 1) == 0:
                                        listing = {
                                            'title': gig.get('title', 'Service'),
                                            'seller': gig.get('seller', {}).get('username', 'seller'),
                                            'reviews': 0,
                                            'price': f"${gig.get('price', {}).get('starting_at', 5)}",
                                            'link': f"https://www.fiverr.com/{gig.get('seller', {}).get('username', 'user')}/{gig.get('slug', 'gig')}",
                                            'is_real': True
                                        }
                                        listings.append(listing)
                    
                    except Exception as e:
                        logger.error(f"Ошибка парсинга {category}: {e}")
                        continue
            
            # Если не нашли достаточно, добавляем из других источников
            if len(listings) < quantity:
                needed = quantity - len(listings)
                additional = await self.get_backup_listings(needed)
                listings.extend(additional)
            
            return listings[:quantity]
            
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return await self.get_backup_listings(quantity)
    
    async def get_backup_listings(self, quantity):
        """Резервный метод парсинга"""
        try:
            # Альтернативные методы получения реальных объявлений
            listings = []
            
            # Можно добавить парсинг через другие API
            # или использовать веб-скрейпинг
            
            return listings[:quantity]
        except:
            return []

class FiverrBot:
    def __init__(self):
        self.parser = RealFiverrParser()
        self.user_states = {}
        self.subscribed_users = set()
        self.application = None
    
    async def check_subscription(self, user_id):
        """РЕАЛЬНАЯ ПРОВЕРКА ПОДПИСКИ"""
        try:
            chat_member = await self.application.bot.get_chat_member(
                chat_id=CHANNEL_USERNAME, 
                user_id=user_id
            )
            return chat_member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            logger.error(f"Ошибка проверки подписки: {e}")
            return True
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        is_subscribed = await self.check_subscription(user.id)
        if not is_subscribed:
            keyboard = [
                [InlineKeyboardButton("🔥 ПОДПИСАТЬСЯ", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ Я ПОДПИСАЛСЯ", callback_data="check_sub")]
            ]
            await update.message.reply_html(
                f"⚠️ <b>Подпишись на {CHANNEL_USERNAME}</b>\n\nДоступ только для подписчиков!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        self.subscribed_users.add(user.id)
        await self.show_main_menu(update)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user = query.from_user
        
        await query.answer()
        
        is_subscribed = await self.check_subscription(user.id)
        if is_subscribed:
            self.subscribed_users.add(user.id)
            await query.edit_message_text("✅ <b>Доступ открыт!</b>", parse_mode='HTML')
            await self.show_main_menu_from_callback(query)
        else:
            await query.edit_message_text("❌ <b>Подписка не найдена!</b>", parse_mode='HTML')
    
    async def show_main_menu(self, update: Update):
        keyboard = [
            [KeyboardButton("🎯 НАЙТИ 0 ОТЗЫВОВ")],
            [KeyboardButton("📊 СТАТУС")]
        ]
        await update.message.reply_html(
            "🚀 <b>FIVERR ПАРСЕР</b>\n\nРежим: <b>РЕАЛЬНЫЙ поиск</b>",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
    
    async def show_main_menu_from_callback(self, query):
        keyboard = [
            [KeyboardButton("🎯 НАЙТИ 0 ОТЗЫВОВ")],
            [KeyboardButton("📊 СТАТУС")]
        ]
        await query.message.reply_html(
            "🚀 <b>Доступ к парсеру открыт!</b>",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        text = update.message.text
        
        if not await self.check_subscription(user.id):
            await update.message.reply_text("❌ <b>Доступ закрыт!</b>", parse_mode='HTML')
            return
        
        if text == "🎯 НАЙТИ 0 ОТЗЫВОВ":
            await update.message.reply_html("🔢 <b>Сколько объявлений?</b> (1-10)")
            self.user_states[user.id] = "waiting_quantity"
        
        elif text == "📊 СТАТУС":
            is_sub = await self.check_subscription(user.id)
            status = "✅ Подписка активна" if is_sub else "❌ Нет подписки"
            await update.message.reply_html(f"📊 <b>Статус:</b>\n{status}\n\nРежим: <b>Реальный парсинг</b>")
        
        elif self.user_states.get(user.id) == "waiting_quantity":
            try:
                quantity = int(text)
                if 1 <= quantity <= 10:
                    await self.start_parsing(update, quantity)
                else:
                    await update.message.reply_text("❌ От 1 до 10!")
            except:
                await update.message.reply_text("❌ Введи число!")
    
    async def start_parsing(self, update: Update, quantity: int):
        user = update.effective_user
        
        try:
            status_msg = await update.message.reply_html("🔄 <b>ЗАПУСКАЮ РЕАЛЬНЫЙ ПАРСИНГ...</b>")
            
            if not await self.check_subscription(user.id):
                await status_msg.edit_text("❌ <b>Доступ отозван!</b>")
                return
            
            # РЕАЛЬНЫЙ ПАРСИНГ
            listings = await self.parser.get_real_listings(quantity)
            
            if not await self.check_subscription(user.id):
                await status_msg.edit_text("❌ <b>Доступ отозван!</b>")
                return
            
            if not listings:
                await status_msg.edit_text("❌ <b>Не удалось найти объявления</b>")
                return
            
            await status_msg.edit_text(f"✅ <b>НАЙДЕНО: {len(listings)}</b>")
            
            # Отправляем РЕАЛЬНЫЕ ссылки
            for listing in listings:
                if listing['reviews'] == 0:  # ТОЛЬКО 0 ОТЗЫВОВ!
                    await update.message.reply_text(f"🔗 {listing['link']}")
                    await asyncio.sleep(0.5)
            
            await update.message.reply_html("🎯 <b>Поиск завершен!</b>\nВсе объявления с 0 отзывами!")
            
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            await update.message.reply_text("❌ <b>Ошибка парсинга</b>")

    def run(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback, pattern="^check_sub$"))
        self.application.add_handler(MessageHandler(filters.TEXT, self.handle_message))
        
        logger.info("🚀 Бот запущен - РЕАЛЬНЫЙ ПАРСИНГ")
        self.application.run_polling()

if __name__ == "__main__":
    bot = FiverrBot()
    bot.run()
