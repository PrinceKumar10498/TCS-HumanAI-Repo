import os
import json
import time
from io import BytesIO
import requests
import demjson
import pytesseract
import pandas as pd
from PIL import Image
from fuzzywuzzy import process

from .utils import *

#creating session
def create_session(self):

        self.session['timestamp'] = int(time.time() * 1000)
        r = requests.session()
        self.session['cookies'] = r.cookies
        try:
            f = BytesIO(r.content)
        except OSError:
            return None
        im = Image.open(f)
        text = pytesseract.image_to_string(im, lang = 'eng')
        self.create_session() 

#get trains between stations
def get_trains_between_stations(self, src=None, dest=None, date=None, as_df=False):

        src = self.get_stn_code(src)  if src else self.src
        dest = self.get_stn_code(dest) if dest else self.dest
        date = date if date else self.date

        if not all([src,dest,date]) and not self.check_config():
            return "Source, destination or date is empty!"

        params = {
            "dt": date,
            "sourceStation": src,
            "destinationStation": dest,
            "language": "en",
            "inputPage": "TBIS",
            "flexiWithDate": "y",
            "_": self.session['timestamp']
        }
        r = requests.get(API_ENDPOINT, params=params, cookies=self.session['cookies'])
        try:
            data = r.json()['trainBtwnStnsList']
        except:
            if r.json()['errorMessage'] == "Session out or Bot attack":
                self.create_session()
                return self.get_trains_between_stations(src, dest, date)
            else:
                return r.json()['errorMessage']
            
        if as_df:
            headers = ['trainName', 'trainNumber', 'fromStnCode', 'toStnCode', 'departureTime', 'arrivalTime',  
                       'duration', 'distance', 'runningMon', 'runningTue', 'runningWed', 'runningThu', 'runningFri', 
                       'runningSat', 'runningSun',  'avlClasses', 'trainType']
            df = pd.DataFrame(data, columns=headers)
            return df
        else:
            return data

# get train schedule
def get_train_schedule(self, train_no, src=None, date=None, as_df=True):

        src = self.get_stn_code(src) if src else self.src
        date = date if date else self.date

        if not all([src,date]) and not self.check_config(dest=False):
            return "Source or date is empty!"
        
        params = {
            "trainNo": train_no,
            "journeyDate": date,
            "sourceStation": src,
            "language": "en",
            "inputPage": "TBIS_SCHEDULE_CALL",
            "_": self.session['timestamp']
        }
        r = requests.get(API_ENDPOINT, params=params, cookies=self.session['cookies'])
        try:
            data = r.json()['stationList']
        except:
            if r.json()['errorMessage'] == "Session out or Bot attack":
                self.create_session()
                return self.get_train_schedule(train_no, src=src,date=date)
            else:
                return r.json()['errorMessage']
            
        if as_df:
            headers = ['stationCode', 'stationName', 'departureTime', 'arrivalTime', 'routeNumber', 'haltTime', 
                       'distance', 'dayCount', 'stnSerialNumber']
            df = pd.DataFrame(data, columns=headers)
            return df
        else:
            return data

#get train fare
def get_train_fare(self, train_no, classc='SL', quota='GN', src=None, dest=None, date=None):

        train_no_code = self.trains[str(train_no)]
        src = self.get_stn_code(src) if src else self.src
        dest = self.get_stn_code(dest) if dest else self.dest
        date = date if date else self.date

        if not all([src,dest,date]) and not self.check_config():
            return "Source, destination or date is empty!"
        
        columns = ['baseFare', 'reservationCharge', 'superfastCharge', 'fuelAmount', 'totalConcession', 
                   'tatkalFare', 'goodsServiceTax', 'otherCharge', 'cateringCharge', 'dynamicFare', 'totalFare', 
                   'wpServiceCharge', 'wpServiceTax', 'travelInsuranceCharge', 'travelInsuranceServiceTax', 
                   'totalCollectibleAmount']
        
        params = {
            "trainNo": train_no_code,
            "classc": classc,
            "quota": quota,
            "dt": date,
            "sourceStation": src,
            "destinationStation": dest,
            "language": "en",
            "inputPage": "FARE",
            "_": self.session['timestamp']
        }
        r = requests.get(API_ENDPOINT, params=params, cookies=self.session['cookies'])
        try:
            data = {}
            for key,val in r.json().items():
                if key in columns:
                    data[key] = r.json()[key]
            return data
        except:
            if r.json()['errorMessage'] == "Session out or Bot attack":
                self.create_session()
                return self.get_seat_availability(train_no, classc=classc, quota=quota, 
                    src=src, dest=dest, date=date)
            else:
                return r.json()['errorMessage']

#get pnr status
    def get_pnr_status(self, pnr_no):

        params = {
            "inputPnrNo": pnr_no,
            "language": "en",
            "inputPage": "PNR",
            "_": self.session['timestamp']
        }
        r = requests.get(API_ENDPOINT, params=params, cookies=self.session['cookies'])
        try:
            return r.json()
        except:
            if r.json()['errorMessage'] == "Session out or Bot attack":
                self.create_session()
                return self.get_pnr_status(pnr_no)
            else:
                return r.json()['errorMessage']

#These all above are API's which will be used in the project in the main on which I am working. 