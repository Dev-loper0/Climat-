from flask import Flask, render_template, redirect, url_for, request, send_file
app = Flask(__name__)


import os
import json
import csv
import requests
import csv
import xlsxwriter


def get_cord(name):
   url = f"https://public.opendatasoft.com/api/records/1.0/search/?dataset=geonames-all-cities-with-a-population-1000&q={name}&lang=fr&sort=name&facet=feature_code&facet=cou_name_en&facet=timezone"
   response = requests.get(url=url, verify=True, timeout=30.00)
   content = json.loads(response.content.decode('utf-8'))
   if len(content["records"]) > 0:
      return(content["records"][0]["geometry"]["coordinates"])

   return None


def get_data(name, geo, start, end):
   if name != None:
      geo = get_cord(name)

      if geo == None:
         return None
      try:
         int(start)
         int(end)
      except:
         return None

   longitude, latitude = geo[0], geo[1]
   url = f"https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=T2M_RANGE,T2M_MAX,T2M_MIN,PRECTOTCORR_SUM&community=RE&longitude={longitude}&latitude={latitude}&format=CSV&start={start}&end={end}"
   response = requests.get(url=url, verify=True, timeout=30.00)
   content = response.content.decode('utf-8')
   content = content.split('-END HEADER-')[1]
   
   with open('output.csv', 'w+') as f:
       f.write(content)
   return 1


def csv2excel(name, geo, start, end):
   workbook = xlsxwriter.Workbook('output.xlsx')
   worksheet = workbook.add_worksheet()
   worksheet.set_column('A:A', 20)

   geo = get_data(name, geo, start, end)
   if geo == None:
      return None
   with open('output.csv', newline='') as csvfile:

      dreader = csv.reader(csvfile, delimiter=' ', quotechar='|')

      rcount = 0

      for row in dreader:
         if len(row) > 0:
            ccount = 0
            row = row[0].split(',')
            for col in row:
               if col == 'T2M_MAX':
                  worksheet.write(rcount, ccount, 'T Max.(m)')
               elif col == 'T2M_MIN':
                  worksheet.write(rcount, ccount, 'T Min.(M)')
               elif col == 'T2M_RANGE':
                  worksheet.write(rcount, ccount, 'Moy.(M+m/2)')
               elif col == 'PRECTOTCORR_SUM':
                  worksheet.write(rcount, ccount, 'P(mm)')
               else:
                  worksheet.write(rcount, ccount, col)
               ccount += 1
            rcount += 1

   workbook.close()
   return 1


@app.route('/getdata', methods=['POST', 'GET'])
def getdata():
   start = request.args.get("start")
   end = request.args.get("end")
   #if int(start) < 1 :
   if request.args.get("region") != "":
      region = request.args.get("region")
      resp = csv2excel(region, None, start, end)
      if resp == None:
         return render_template("error.html")

   else:
     if request.args.get("longitude") != "":
       if request.args.get("latitude") != "":
         geo = [request.args.get("longitude"), request.args.get("latitude")]
         csv2excel(None, geo, start, end)
     else:
       return render_template("error.html")
     
   return send_file('output.xlsx')


@app.route('/')
def index():
   return render_template("index.html")


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=81)