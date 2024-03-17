# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`
import datetime
import os
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import firestore

load_dotenv()
cred = credentials.Certificate(os.getenv("desktop_path"))

firebase_admin.initialize_app(cred, {
    'databaseURL': os.getenv("DATABASE_URL")
})

db = firestore.client()
users_ref = db.collection("Users")

def check_person(id):
    print("entered check_person")
    
    if users_ref.document(str(id)).get().exists == False:
        print("returned false from check person")
        return (0,0,False)
    else:
        x = users_ref.document(str(id)).get().to_dict()
        delete_data(id)
        print("returned true from check person")
        return (x["chat_id"], x["Name"], True)

def delete_data(id):
    curr_ref = users_ref.document(str(id))
    curr_date = datetime.datetime.today()
    curr_week = curr_date.strftime("%U")
    
    week_dict = curr_ref.get().to_dict()['week_numbers_booked']

    for week in week_dict.keys():
        if week < curr_week:
            curr_ref.update({
                f"week_numbers_booked.{week}": firestore.DELETE_FIELD
            })


def get_booking_hours(week_number, id):
    x = users_ref.document(str(id)).get().to_dict()
    weeks_booked_dict = x['week_numbers_booked']

    if week_number in weeks_booked_dict:
        return weeks_booked_dict[week_number]['number_of_hours_booked']
    
    else:
        return 0

def push_data(person):
    week_number = person.date.strftime("%U")
    curr_ref = users_ref.document(str(person.chat_id))
    if not person.in_db:
        curr_ref.set({
            "Name": person.name,
            "ID": person.student_id,
            "chat_id": person.chat_id,
            "username": person.username,
            "week_numbers_booked": {
                week_number: {
                    "dates_booked": [person.date],
                    "number_of_hours_booked": person.hours_booked
                }
            }
        })
        
    elif person.in_db:
        x = curr_ref.get().to_dict()
        weeks_booked_dict = x['week_numbers_booked']

        if week_number in weeks_booked_dict:
            
            curr_ref.update(
                {
                    f"week_numbers_booked.{week_number}.dates_booked": firestore.ArrayUnion([person.date]),
                    f"week_numbers_booked.{week_number}.number_of_hours_booked": firestore.Increment(person.hours_booked)
                }
            )
        else:
            curr_ref.update({
                f"week_numbers_booked.{week_number}.dates_booked": [person.date],
                f"week_numbers_booked.{week_number}.number_of_hours_booked": person.hours_booked
            })


    return

