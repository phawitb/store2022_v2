from flask import Flask, Response, render_template, url_for
from datetime import datetime
import time
import csv
import pandas as pd
import cv2
import keyboard
from promptpay import qrcode
import configparser

app = Flask(__name__)

def save_history(table,timestamp):  #datetime.now()
   data = {
      'table':table,
      'timestamp':timestamp
   }
   #update historys.csv
   df_hist = pd.DataFrame(columns = ['table','timestamp'])
   df_hist = df_hist.append(data, ignore_index = True)
   df_hist.to_csv('data/historys.csv', mode='a', header=False,index=False)

def update_status(waiting_amount,finish):
    config = configparser.ConfigParser()
    config.read('data/status.txt')
#     config.add_section('status')
    config.set('status', 'waiting_amount', str(waiting_amount))
    if finish != '':
        config.set('status', 'finish', str(finish))
    with open('data/status.txt', 'w') as configfile:
        config.write(configfile)

def read_status():
    parser = configparser.ConfigParser()
    parser.read('data/status.txt')
    finish = parser.get("status", "finish")
    waiting_amount = parser.get("status", "waiting_amount")
    return waiting_amount,finish

def get_keyboard():
   global Barcodes,checkout
   if Barcodes:
      if keyboard.is_pressed('-'):
         Barcodes.pop()
         checkout = False
      if keyboard.is_pressed('enter'):
         checkout = True

def gen_frames():
   while True:
      success, frame = camera.read() 
    #   read_barcodes()
      if success:
         try:
            frame = cv2.resize(frame, (640,480))
            ret, buffer = cv2.imencode('.jpg', cv2.flip(frame,1))
            frame = buffer.tobytes()
         except Exception as e:
            pass
      else:
         img = cv2.imread("static/images/cam.png", cv2.IMREAD_COLOR)
         img = cv2.resize(img, (640,480))
         ret, buffer = cv2.imencode('.jpg', img)
         frame = buffer.tobytes()

      yield (b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def genQrpayment(id_or_phone_number,amount):
    payload_with_amount = qrcode.generate_payload(id_or_phone_number,amount)
    qrcode.to_file(payload_with_amount, "static/images/qrcode_true.png")
         
def gen_qr():
   global checkout,Total,finish,finish_start,Barcodes,delay_state,table
   while True:
      try:
         if checkout == False:
            img = cv2.imread("static/images/qrcode_false.png", cv2.IMREAD_COLOR)
         else:
            genQrpayment(id_or_phone_number,Total)
            img = cv2.imread("static/images/qrcode_true.png", cv2.IMREAD_COLOR)

            update_status(Total,'')
            waiting_amount,finish = read_status()

            if finish == 'True':
               img = cv2.imread("static/images/finish.png", cv2.IMREAD_COLOR)
               timestamp = datetime.now()
               
               if delay_state == False:
                  save_history(table,timestamp)
                  finish_start = time.time()
                  delay_state = True
            if time.time() - finish_start > 4 and delay_state:
               update_status(0,False)
               checkout = False
               Barcodes = []
               delay_state = False
        
               # time.sleep(3)

               # parser['finish']=False
               # with open('data/status.txt', 'w') as configfile:
               #    parser.write(configfile)
            




         img = cv2.resize(img, (1600,1600))
        #  print('getbarcode....................................................................',img.shape)
         # ret, buffer = cv2.imencode('.jpg', cv2.flip(img,1))
         ret, buffer = cv2.imencode('.jpg', img)
         frame = buffer.tobytes()
         yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
      except:
         pass

def find_product_data(df,barcode):
    for i,b in enumerate(df['barcode']):
        if str(b) == str(barcode):
            return df['name'][i],df['price'][i]
    else:
        return None,None

def getBarcodeFromCsv(filename):
    file = open(filename)
    csvreader = csv.reader(file)
    rows = []
    for row in csvreader:
        rows.append(row[0])
    file.close()
    f = open(filename, "w")
    f.truncate()
    f.close()
    return rows

def create_table(df,Barcodes):
    global Total
    df_barcode = []
    for i in set(df['barcode']):
        df_barcode.append(str(i))
    keys = list(set(Barcodes).intersection(set(df_barcode)))  #get barcode key only in database
    
    table = ''
    Total = 0 
    for k in keys:
        barcode = k
        count = Barcodes.count(k)
        name,price = find_product_data(df,barcode)
        total = price*count
        Total += total
        table += f'/{name}|{count}|{total}'
    table += '/||'*(10-len(keys))   #add to 10 lists

    if Total == 0:
       table = 'Total 0//||/||/||/||'
    else:
       table = f'Total {Total}/{table}'

    return table

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/item_feed')
def item_feed():
    def generate():
        global Barcodes,table

        get_keyboard()
        
        #create table
        barcodes = getBarcodeFromCsv('data/current_barcode.csv')
        df = pd.read_csv('data/products.csv')
        if barcodes:
            for barcode_info in barcodes:
                if str(barcode_info) in str(df['barcode']):
                    Barcodes.append(barcode_info)
        table = create_table(df,Barcodes)
        yield table
            
    return Response(generate(), mimetype='text') 

@app.route('/video_feed')
def video_feed():
   return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/qr_feed')
def qr_feed():
   return Response(gen_qr(), mimetype='multipart/x-mixed-replace; boundary=frame')






Barcodes = []
camera = cv2.VideoCapture(1)
checkout = False
id_or_phone_number = "0805471749"
Total = 0
finish = False
update_status(Total,finish)
finish_start = time.time()
delay_state = False
table = ''

if __name__ == '__main__':
    app.env = "development"
    app.run(use_reloader = True,debug=True, threaded=True)















# from flask import Flask, render_template
# import csv

# def read_csv():
# 	file = open('data/data.csv')
# 	csvreader = csv.reader(file)
# 	Pokemons = next(csvreader)
# 	return Pokemons

# app = Flask(__name__)

# # Pokemons =["Pikachu", "xCharizard", "Squirtle", "Jigglypuff",
# # 		"Bulbasaur", "Gengar", "Charmander", "Mew", "Lugia", "Gyarados"]

# @app.route('/')
# def homepage():
# 	Pokemons = read_csv()
# 	return render_template("index.html", len = len(Pokemons), Pokemons = Pokemons)

# if __name__ == '__main__':
#    app.run(use_reloader = True, debug = True)
