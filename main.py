import os
import phonenumbers

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from phonenumbers import geocoder, carrier, timezone

BOT_TOKEN = os.environ["BOT_TOKEN"]

CHANNEL = "@team_shadow_striker"
CHANNEL_LINK = "https://t.me/team_shadow_striker"

FOOTER = "\n\nCreated By Zavian Chowdhury"


def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎 Search Number", callback_data="search")],
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)]
    ])


async def joined(user_id, context):
    try:
        member = await context.bot.get_chat_member(
            CHANNEL, user_id
        )
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await joined(update.effective_user.id, context):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ Verify", callback_data="verify")]
        ])

        await update.message.reply_text(
            "Welcome to Zavian Number Intelligence Bot!\n\n"
            "Please join our official channel to continue.",
            reply_markup=keyboard
        )
        return

    await update.message.reply_text(
        "Welcome!\n\nSelect an option below.",
        reply_markup=menu()
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "verify":
        if await joined(query.from_user.id, context):
            await query.edit_message_text(
                "Verification Successful!",
                reply_markup=menu()
            )
        else:
            await query.answer(
                "Please join the channel first.",
                show_alert=True
            )

    elif query.data == "search":
        if not await joined(query.from_user.id, context):
            await query.message.reply_text("Please join our channel first.")
            return

        context.user_data["awaiting_number"] = True
        await query.message.reply_text(
            "Send a phone number with country code.\n\n"
            "Example: +8801XXXXXXXXX"
        )

    elif query.data.startswith("social_"):
        await query.message.reply_text(
            "Account status cannot be verified from a phone number alone."
            + FOOTER
        )


async def number_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_number"):
        return

    if not await joined(update.effective_user.id, context):
        await update.message.reply_text("Please join our channel first.")
        return

    try:
        number = phonenumbers.parse(update.message.text.strip(), None)

        if not phonenumbers.is_valid_number(number):
            await update.message.reply_text("Invalid phone number.")
            return

        country = geocoder.country_name_for_number(number, "en")
        operator = carrier.name_for_number(number, "en")
        zones = timezone.time_zones_for_number(number)

        number_type = phonenumbers.number_type(number)

        types = {
            0: "Fixed Line",
            1: "Mobile",
            2: "Fixed Line or Mobile",
            3: "Toll Free",
            4: "Premium Rate",
            5: "Shared Cost",
            6: "VoIP",
            7: "Personal Number",
            8: "Pager",
            9: "UAN",
            10: "Voicemail"
        }

        formatted = phonenumbers.format_number(
            number,
            phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )

        report = (
            "📱 PHONE NUMBER REPORT\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"Number: {formatted}\n"
            f"Country: {country or 'Unknown'}\n"
            f"Country Code: +{number.country_code}\n"
            f"Carrier: {operator or 'Unavailable'}\n"
            f"Number Type: {types.get(number_type, 'Unknown')}\n"
            f"Timezone: {', '.join(zones) if zones else 'Unknown'}\n\n"
            "SOCIAL ACCOUNT CHECKER\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Account existence: Not Verified"
            + FOOTER
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("WhatsApp", callback_data="social_whatsapp"),
                InlineKeyboardButton("Telegram", callback_data="social_telegram")
            ],
            [
                InlineKeyboardButton("Facebook", callback_data="social_facebook"),
                InlineKeyboardButton("Gmail", callback_data="social_gmail")
            ],
            [
                InlineKeyboardButton("🔎 Search Another Number", callback_data="search")
            ]
        ])

        await update.message.reply_text(
            report,
            reply_markup=keyboard
        )

        context.user_data["awaiting_number"] = False

    except phonenumbers.NumberParseException:
        await update.message.reply_text(
            "Invalid format. Example: +8801XXXXXXXXX"
        )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, number_handler)
    )

    print("Bot Started!")
    app.run_polling()


if __name__ == "__main__":
    main()
