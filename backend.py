from flask import Flask, Response, render_template, url_for
from datetime import datetime
import time
import csv
import pandas as pd
import cv2
import keyboard

app = Flask(__name__)

Barcodes = []
camera = cv2.VideoCapture(1)
checkout = False

def get_keyboard():
   global Barcodes,checkout
   if Barcodes:
      if keyboard.is_pressed('-'):
         Barcodes.pop()
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
         
def gen_qr():
   global checkout
   while True:
      try:
         if checkout == False:
            img = cv2.imread("static/images/qrcode_false.png", cv2.IMREAD_COLOR)
         else:
            img = cv2.imread("static/images/qrcode_true.png", cv2.IMREAD_COLOR)
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
        global Barcodes

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

if __name__ == '__main__':
    
    app.run(debug=True, threaded=True)















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
