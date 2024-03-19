import datetime
import sys
sys.path.insert(1, 'C:/Telebot/functions')
import google_sheets

class Person():
    def __init__(self, chat_id, username = None, hours_booked = 0):
        self.chat_id = chat_id
        self.username = "@" + username

        self.name = ""
        self.student_id = 1000000

        self.date = ""
        self.start_time = "0000"
        self.end_time = "0000"
        self.cell_range = ""
        self.hours_booked = hours_booked

        self.in_db = False

        self.date_chosen = False
        self.time_chosen = False

        self.name_given = False
        self.id_given = False
        
        self.slot_available = False

        self.start = False
        
    
        
    def check_value(self, message, curr_booking_hours):

        print("check_value went through")
        correct_input = False
        booking_exceeded = False

        try:
            correct_input = True
            while correct_input:
                if not self.check_time(message):
                    print("returned False from inner check_time")
                    correct_input = False
                #Checking if split values are indeed in 24h format, return False if not
                self.start_time = datetime.datetime.strptime(self.start_time, '%H%M')
                self.end_time = datetime.datetime.strptime(self.end_time, '%H%M')
                if (self.start_time > self.end_time) or (self.start_time < datetime.datetime.strptime("0900", '%H%M')) or (self.end_time > datetime.datetime.strptime("2300", '%H%M')):
                    correct_input = False
            
                time_diff = self.end_time - self.start_time
                if time_diff.seconds/3600 > 4:
                    booking_exceeded = True
                    correct_input = False
                    return(booking_exceeded, correct_input)
                else:
                    total_hours = curr_booking_hours + time_diff.seconds/3600
                    print("Total hours ", total_hours)
                    print("curr_booking_hours ", curr_booking_hours)
                    print("slot asked for ", time_diff.seconds/3600)
                    if total_hours > 4:
                        booking_exceeded = True
                        correct_input = False
                        return(booking_exceeded, correct_input)
                    else:
                        self.hours_booked = time_diff.seconds/3600
                        print(self.hours_booked)

                #Checking for valid minute values
                if not self.check_00_30(self.start_time) or not self.check_00_30(self.end_time):
                    print("returned False from inner check_00_30")
                    correct_input = False
                else:
                    print("correct input is True")
                    break
        
        except ValueError as ve1:
            print('ValueError 1:', ve1)
            correct_input = False

        except TypeError as ve2:
            print('TypeError 1:', ve2)
            correct_input = False

        return (False, correct_input)
    

    def check_time(self, message):

    #Checking if there is a "-", return False if not
        print("checking time")
        try:
            if len(message.text.split("-")) != 2:
                print("returned False from check_time")
                return False
            #Splitting string on the "-"
            else:
                self.start_time = message.text.split('-')[0].strip()
                self.end_time = message.text.split("-")[1].strip()
                if len(self.start_time) != 4 or len(self.end_time) != 4:
                    print("returned False from check_time else part")
                    return False
                print("returned True from check_time")
                return True
        except:
            return False


    def check_00_30(self, time):
        x = time.strftime('%H%M')
        print(x)
        if (x[-1] == "0") and (x[-2] == "0" or x[-2] == "3"):
            print("returned True from check_00_30")
            return True
        else:
            print("returned false from check_00_30")
            return False
    
    def check_id(self, message):
        correct_input = False
        print("went thru check id")
        try:
            correct_input = True
            while correct_input:
                if (len(message.text) != 7) or (message.text[:3] != "100"):
                    correct_input = False
                elif (len(message.text) == 7) or (message.text[:3] == "100"):
                    int(message.text)
                    correct_input = True
                    break

        except ValueError as ve1:
            print('ValueError 1:', ve1)
            correct_input = False

        if correct_input:
            self.id_given = True
            self.student_id = message.text
        return correct_input
    
    def reset(self):
        

        self.date_chosen = False
        self.name_given = False
        self.id_given = False
        self.time_chosen = False
        self.slot_available = False

    def check_slot(self):
        google_sheets.main()

        self.date = datetime.datetime.combine(self.date, datetime.datetime.min.time())
        self.start_time = self.start_time.strftime("%H%M")
        self.end_time = self.end_time.strftime("%H%M")
        
        result = google_sheets.check_slot(self.date, self.start_time, self.end_time, self.name)

        if result[2] == True:
            self.slot_available = False
            return ("Event", result[1])
        elif result[0] == True:
            self.slot_available = True
            self.cell_range = result[1]
            return (None, None)
        elif result[0] == False:
            return (None, result[1])
