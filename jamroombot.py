import base64
import telebot
from datetime import date
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import os
from dotenv import load_dotenv

from functions import firestore
from person import Person
from telebot import *
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

load_dotenv()
API_TOKEN = os.getenv("TELEBOT_API_KEY")
bot = telebot.TeleBot(API_TOKEN, parse_mode=None)
firestore_db = firestore.users_ref
print("Got db from firestore")
db = {}

@bot.message_handler(commands=['cancel'], func = lambda message: message.chat.id in db)
def cancel(message):
    finish(message.chat.id)
    bot.reply_to(message, "Cancelled. Select /start to start booking again.")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    print("entered start")
    loading_message = bot.send_message(message.chat.id, "Loading, this may take a moment. or not idk depends on the server")
    checked_person = firestore.check_person(message.chat.id)
    print("checked person", checked_person)
    db[message.chat.id] = Person(chat_id = message.chat.id, username = message.from_user.username, hours_booked = checked_person[2])

    if checked_person[2] == False:
        bot.edit_message_text("Hello! Welcome to the Jam Room booking bot to make the secretary's job even easier! Please remember the following:\n\n1. Each band has a maximum of 4 hours of booking per week.\n\n2. Please do not litter, throw all your trash when leaving the room.\n\n3. For any booking related queries such as cancelling your slot, please approach the secretary.", 
                            db[message.chat.id].chat_id, 
                            loading_message.message_id)
        
        bot.send_message(db[message.chat.id].chat_id, "Click /book to start booking!")
        return
    
    elif checked_person[2] == True:
        db[message.chat.id].in_db = True
        db[message.chat.id].name_given = True
        db[message.chat.id].name = checked_person[1]
        print("name in person object", db[message.chat.id].name)
        bot.edit_message_text(f"Welcome back {db[message.chat.id].name}! Please remember the following:\n\n1. Each band has a maximum of 4 hours of booking per week.\n\n2. Please do not litter, throw all your trash when leaving the room.\n\n3. For any booking related queries such as cancelling your slot, please approach the secretary.", 
                                db[message.chat.id].chat_id, 
                                loading_message.message_id)
        
        bot.send_message(db[message.chat.id].chat_id, "Click /book to start booking!")
        return
        

def exceeded_four_hours(message):
    bot.send_message(message.chat.id, "did u think this bot was gg let u book more than 4 hours lmao get cooked.")


@bot.message_handler(commands=['book'])
def start_booking(message):
    if message.chat.id not in db:
        bot.send_message(message.chat.id, "Please send /start to the start the booking.")
        return
    elif not db[message.chat.id].in_db:
        bot.send_message(db[message.chat.id].chat_id, "Please enter your name.")
    else:
        activate_calendar(message)
    

@bot.message_handler(func = lambda message: message.chat.id in db
                     and db[message.chat.id].in_db == False
                     and db[message.chat.id].name_given == False)
def get_name(message):
    print("enterd get_name")
    db[message.chat.id].name = message.text
    db[message.chat.id].name_given = True
    get_id(message.chat.id)


def get_id(chat_id):
    bot.send_message(db[chat_id].chat_id, "Please enter your student id in the format 100####.")


@bot.message_handler(func = lambda message: message.chat.id in db
                     and db[message.chat.id].date_chosen == False
                     and db[message.chat.id].in_db == False 
                     and db[message.chat.id].name_given == True)
def check_id(message):
    correct_input = db[message.chat.id].check_id(message)
    
    if correct_input:
        bot.send_message(db[message.chat.id].chat_id, "Name and ID registered.")
        activate_calendar(message)
        
    elif not correct_input:
        bot.send_message(db[message.chat.id].chat_id, "Please enter valid input.")


def activate_calendar(message):
    calendar, step = DetailedTelegramCalendar(min_date=date.today(), max_date=date.today()+timedelta(weeks=8)).build()
    bot.send_message(db[message.chat.id].chat_id,
                    f"Select {LSTEP[step]}",
                    reply_markup=calendar)



@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal(c):
    result, key, step = DetailedTelegramCalendar().process(c.data)
    date_today = date.today()
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              db[c.from_user.id].chat_id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        print(type(result))
        if result < date_today:
            bot.edit_message_text("u cant book a timeslot from the past dumbass. Now u gotta use /book to book again, look at what you have done.", db[c.from_user.id].chat_id, c.message.message_id)
        elif result > date_today + relativedelta(months = +2):
            bot.edit_message_text("You are only able to book a slot 2 months in advance.", db[c.from_user.id].chat_id, c.message.message_id)
        else:
            db[c.from_user.id].date_chosen = True
            db[c.from_user.id].date = result

            print(db[c.from_user.id].date, type(db[c.from_user.id].date))

            bot.edit_message_text(f"You selected {result}",
                                db[c.from_user.id].chat_id,
                                c.message.message_id)
            bot.send_message(db[c.from_user.id].chat_id, "Enter your timing in this 24h format eg. 1200-1330")


@bot.message_handler(func = lambda message: message.chat.id in db
                     and db[message.chat.id].date_chosen == True
                     and db[message.chat.id].time_chosen == False)
def check_value(message):
    curr_booking_hours = 0

    if db[message.chat.id].in_db == True:
        week_number = db[message.chat.id].date.strftime("%U")
        curr_booking_hours = firestore.get_booking_hours(week_number, message.chat.id)

        if curr_booking_hours >= 4:
            exceeded_four_hours(message)
            return False
    
    correct_input = db[message.chat.id].check_value(message, curr_booking_hours)

    if correct_input[0] == False and correct_input[1] == False:
        bot.send_message(db[message.chat.id].chat_id, "Please enter a valid input.")
        return False
    elif correct_input[0] == True:
        bot.send_message(db[message.chat.id].chat_id, "Please do not exceed the weekly 4 hours booking limit. If you require more than 4 hours, please contact the secretary.\nSelect /cancel from the commands to restart the booking if you would like to change dates.")
        return False
    else:
        bot.send_message(db[message.chat.id].chat_id, "You have chosen " + db[message.chat.id].start_time.strftime('%H%M') + "-" + db[message.chat.id].end_time.strftime('%H%M') + ".")
        db[message.chat.id].time_chosen = True
        checking_slot(message.chat.id)


def checking_slot(chat_id):
    if db[chat_id].time_chosen:
        
        print(db[chat_id].start_time)
        print(db[chat_id].end_time)
        bot.send_message(db[chat_id].chat_id, "Checking availability and booking your slot. Please do not cancel.")
        result = db[chat_id].check_slot()

        if result[0] == "Event":
            bot.send_message(db[chat_id].chat_id, f"There appears to be an event from {result[1][0]} to {result[1][1]}. Please check against the sheet for the timeslot.\n\nTo restart the booking, use /book.")
        
        elif result[0] == None and not db[chat_id].slot_available:
            reply = ""
            for timeslot in result[1]:
                reply += timeslot + "\n"
            bot.send_message(db[chat_id].chat_id, "Your slot is not available as the following slots are booked: \n" + reply 
                             + "\nPlease refer to the spreadsheet /sheet to check for available slots.")
            
            bot.send_message(db[chat_id].chat_id, "Please press /book to restart your booking.")

        finish(chat_id)
        return



def finish(chat_id):
    ##add cond if slot avail is false
    if db[chat_id].slot_available:
        firestore.push_data(db[chat_id])
        del db[chat_id]
        bot.send_message(chat_id, "Your slot has been booked. For any issues please pm the current Secretary.")
    else:
        db[chat_id].reset()
    
    bot.stop_polling()
     

@bot.message_handler(commands=['help'])
def help(message):
	bot.reply_to(message, "Select /start to start the bot dumbass")

@bot.message_handler(commands=['sheet'])
def sheet(message):
    bot.reply_to(message, "https://docs.google.com/spreadsheets/d/1q0-aP072NUM49hjMtAnUmKY94u83p7Dtp9lWf2D1NV0/edit?usp=sharing")

@bot.message_handler(commands=['jam_guide'])
def jam_room_guide(message):
    bot.reply_to(message, "To be updated")


print("Bot has started")
bot.infinity_polling()
