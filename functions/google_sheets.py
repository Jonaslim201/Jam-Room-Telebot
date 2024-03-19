import os.path
import datetime
import calendar
import os
from dotenv import load_dotenv

from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


load_dotenv()
FILE_NAME = os.getenv("FILE_NAME")
# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SPREADSHEET_RANGE = os.getenv("SPREADSHEET_RANGE")
print("sheet defined")

month_to_integer = {}
for index, month in enumerate(calendar.month_name):
    if index < 10:
        index = "0" + str(index)
    else:
        str(index)
    
    month_to_integer[month] = index

del month_to_integer['']

letters = {}
values = []
sheet = None

minutes = 0
start = datetime.time(hour = 9, minute = 0)
row_names = {}

for i in range(29):
    x = (datetime.datetime.combine(datetime.date(1,1,1), start) + datetime.timedelta(minutes = minutes)).time().isoformat(timespec='minutes').replace(":", "")
    row_names[x] = str(i + 4)
    minutes += 30

for i in range(26):
  letters[i] = chr(i+65)
  


def main():
  """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
  global values
  global sheet

  creds = None
  if os.path.exists(FILE_NAME):
    creds = service_account.Credentials.from_service_account_file(FILE_NAME)
    print('creds found')

  try:
    
    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    print("sheet captured")
    result = (
        sheet.values()
        .get(spreadsheetId=SPREADSHEET_ID, range=SPREADSHEET_RANGE)
        .execute()
    )

    values = result.get("values", [])[0]    

    if not values:
      print("No data found.")
      return
    print("values gotten")

  except HttpError as err:
    print(err)


def check_slot(date, start_time, end_time, name):
  print(date, start_time, end_time, name)
  rgb = []
  latest_date = datetime.datetime.strptime(values[-1], "%m/%d/%Y")
  if latest_date < date:
    print("Requested date: ", date)
    print("Latest date: ", latest_date)
    return False
  else:
    diff = date - datetime.datetime.strptime(values[1], "%m/%d/%Y")
    index = diff.days + 1

  letter_index = fuck_this_function(index)
  cell_range = "'Jam Room Bookings'!"+ letter_index + row_names[start_time] + ":" + letter_index + str((int(row_names[end_time]) - 1))

  cell_rows = []
  for i in range(int(row_names[start_time]), int(row_names[end_time]) + 1):
    cell_rows.append(i)

  req_cells = sheet.get(spreadsheetId = SPREADSHEET_ID, ranges = [cell_range], includeGridData = True).execute()
  try:
    merged_cells = req_cells['sheets'][0]['merges'][0]
    start_row_index = merged_cells['startRowIndex'] + 1
    end_row_index = merged_cells['endRowIndex'] + 1

    print(end_row_index)
    if end_row_index == 31:
      end_row_index = 32

    for key, item in row_names.items():
      if str(start_row_index) == item:
        start_row_index = key
      
      if str(end_row_index) == item:
        end_row_index = key
    
    return (False, [start_row_index, end_row_index], True)


  except KeyError:
    print("Returned key error from google_sheets.check_slots")


  for cell in req_cells['sheets'][0]['data'][0]['rowData']:
      rgb.append(cell['values'][0]['effectiveFormat']['backgroundColor'])
  
  found_booked_cells = find_booked_cells(rgb)

  if all(v is None for v in found_booked_cells):
    book_slot(cell_range, name, index, start_time, end_time)
    return (True, [cell_range.split("!")[1]], False)
  
  else:
    booked_timeslots = find_booked_timeslots(found_booked_cells, cell_rows)
    print(booked_timeslots)
    exact_slots = find_exact_slots(booked_timeslots)

    return (False, exact_slots, False)



def find_booked_cells(rgb):
  arr = []
  for i in range(len(rgb)):
    if (not "blue" in rgb[i]) and (not 'green' in rgb[i]):
      arr.append(i)
    elif (rgb[i]["green"] > rgb[i]["red"]) and (rgb[i]["green"] > rgb[i]["blue"]):
      print(i)
      arr.append(i)
    else:
      arr.append(None)
      
  return arr



def find_booked_timeslots(found_booked_cells, cell_rows):
  arr = []
  for i in range(len(found_booked_cells)):
    if found_booked_cells[i] != None:
      timeslot = list(row_names.keys())[list(row_names.values()).index(str(cell_rows[found_booked_cells[i]]))]
      arr.append(timeslot)
    else:
      arr.append(None)
  return arr



def find_exact_slots(booked_timeslots):
  arr = []
  time_slot_exists = False
  x = ""
  for i in range(len(booked_timeslots)):

    if booked_timeslots[i] != None:
      timeslot = (datetime.datetime.strptime(booked_timeslots[i], "%H%M") + datetime.timedelta(minutes = 30)).strftime('%H%M')

      if i == len(booked_timeslots) - 1:
          if not time_slot_exists:
            x = booked_timeslots[i] + "-" + timeslot
            arr.append(x)
          elif time_slot_exists:
            x = x + "-" + timeslot
            arr.append(x)
          break
        

    if not time_slot_exists and booked_timeslots[i] != None:
      x = booked_timeslots[i]

      if booked_timeslots[i + 1] == None:
        x = x + "-" + timeslot
        arr.append(x)
        x = ""

      else:
        time_slot_exists = True

    elif time_slot_exists and booked_timeslots[i + 1] == None:
      x += "-" + timeslot
      arr.append(x)
      x = ""
      time_slot_exists = False

  return arr
        

def book_slot(cell_range, name, index, start_time, end_time):

  temp_arr = cell_range.split("!")
  first_cell = temp_arr[0] + "!" +  temp_arr[1].split(":")[0]
  body = {
    "values": [[name]]
  }
  sheet.values().update(
    spreadsheetId = SPREADSHEET_ID,
    valueInputOption='USER_ENTERED',
    range = first_cell,
    body = body
  ).execute()

  requests = {
  "requests": [
    {
      "repeatCell": {
        "fields": "userEnteredFormat.backgroundColor",
        "range": {
          "startColumnIndex": index,
          "endColumnIndex": index + 1,
          "startRowIndex": int(row_names[start_time]) - 1,
          "endRowIndex": int(row_names[end_time]) - 1,
          "sheetId": 1820846734
        },
        "cell": {
          "userEnteredFormat": {
            "backgroundColor": {
              "red": 1,
              "blue": 0,
              "green": 0
            }
          }
        }
      }
    }
  ]
  }

  sheet.batchUpdate(spreadsheetId = SPREADSHEET_ID, body = requests).execute()
  print("start column: ", index, "\nend column", index + 1, "\nstart row", int(row_names[start_time]) - 1, "\nend row", int(row_names[end_time])-1)
  print("cell updated at", first_cell)

def fuck_this_function(index):
  global letters

  remainder = index%26
  quotient = index//26

  if quotient == 0:
    return str(letters[remainder])

  return str(letters[quotient-1]) + str(letters[remainder])


