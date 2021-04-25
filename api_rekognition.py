# -*- coding: utf-8 -*-
"""
Created on Wed Mar 31 15:34:01 2021

@author: Ryzen
"""
import os
import csv
import boto3
import io
import cv2
import imutils
import mysql.connector as mysql
from botocore.config import Config
from flask import Flask,render_template,request
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage    
import json

app=Flask(__name__)
app.config['UPLOAD_FOLDER_IMAGENES']="./Imagenes"
app.config['UPLOAD_FOLDER_IMAGENES_RQST']="./ImagenesRQST"
app.config['UPLOAD_FOLDER_VIDEOS']="./VideosData"



def Reconocimiento(f): 
    imagePaths = os.listdir(app.config['UPLOAD_FOLDER_IMAGENES'])

    face_recognizer = cv2.face.LBPHFaceRecognizer_create()
    face_recognizer.read('modeloLBPHFace.xml')
    faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
    frame = cv2.imread(app.config['UPLOAD_FOLDER_IMAGENES_RQST']+"/"+secure_filename(f.filename))
     
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    auxFrame = gray.copy()
    
    faces = faceClassif.detectMultiScale(gray,1.3,5)
    
    for (x,y,w,h) in faces:
        rostro = auxFrame[y:y+h,x:x+w]
        rostro = cv2.resize(rostro,(150,150),interpolation= cv2.INTER_CUBIC)
        result = face_recognizer.predict(rostro)
    
        cv2.putText(frame,'{}'.format(result),(x,y-5),1,1.3,(255,255,0),1,cv2.LINE_AA)
    	
    		# LBPHFace
        if result[1] < 70:
            cv2.putText(frame,'{}'.format(imagePaths[result[0]]),(x,y-25),2,1.1,(0,255,0),1,cv2.LINE_AA)
            cv2.rectangle(frame, (x,y),(x+w,y+h),(0,255,0),2)
        else:
            cv2.putText(frame,'Desconocido',(x,y-20),2,0.8,(0,0,255),1,cv2.LINE_AA)
            cv2.rectangle(frame, (x,y),(x+w,y+h),(0,0,255),2)
    		
        return (format(imagePaths[result[0]]))  
        
def prediccion(f):    
    #CONFIGURAR LOS ACCESOS
      client=boto3.client('rekognition',
                    region_name='us-east-2',
                    aws_access_key_id="AKIA6P46JAOPIR5NGNNC",
                    aws_secret_access_key="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"
                    )     
      filename=secure_filename(f.filename)
      f.save(os.path.join(app.config['UPLOAD_FOLDER_IMAGENES_RQST'],filename))    
      #Uso de AWS para la deteccion
      response=client.detect_faces(
          Image={'Bytes':f.getvalue()},  
          Attributes=['ALL'])       
      
      mayor_confidence=0
      _response=''
      for element in response["FaceDetails"][0]["Emotions"]:
          if element["Confidence"]>mayor_confidence:
              mayor_confidence=element["Confidence"]   
      
      #CONECCION A MYSQL
      db = mysql.connect(
          host = "db-proyecto-mysql.cluster-cbwzye3glmch.us-east-1.rds.amazonaws.com",
          user = "sa",
          passwd = "luismiguel",
          database = "educati"
          )
      cursor = db.cursor()
      query = "SELECT * FROM users"
      cursor.execute(query)
      records = cursor.fetchall()      
      for record in records:
          print(record)
              
      for element in response["FaceDetails"][0]["Emotions"]:
          if mayor_confidence==element["Confidence"]:
              _response={
                  "Security":element["Confidence"],
                  "Emotion":element["Type"],
                   "Adic":records
                  }
                  
      return _response
 
def RegisterFaceUser(dni,f):     
    dataPath = app.config['UPLOAD_FOLDER_IMAGENES']    
    personPath = dataPath + '/' + dni     
   
    f.save(os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'],dni+".mp4"))  
    
    #luego de guardar el video, usarlo de captura
    videoPersonaPath=app.config['UPLOAD_FOLDER_VIDEOS']+"/"+dni+".mp4"
    cap = cv2.VideoCapture(videoPersonaPath)          
    
    if not os.path.exists(personPath):	
    	os.makedirs(personPath)
    
    faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
    count = 0
    
    while True:
    
    	ret, frame = cap.read()
    	if ret == False: break
    	frame =  imutils.resize(frame, width=640)
    	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    	auxFrame = frame.copy()
    
    	faces = faceClassif.detectMultiScale(gray,1.3,5)
    
    	for (x,y,w,h) in faces:
    		cv2.rectangle(frame, (x,y),(x+w,y+h),(0,255,0),2)
    		rostro = auxFrame[y:y+h,x:x+w]
    		rostro = cv2.resize(rostro,(150,150),interpolation=cv2.INTER_CUBIC)
    		cv2.imwrite(personPath + '/rotro_{}.jpg'.format(count),rostro)
    		count = count + 1
    	#cv2.imshow('frame',frame)
    
    	k =  cv2.waitKey(1)
    	if k == 27 or count >= 300:
    		break

    


@app.route("/RegisterFaceStudent")
def pagina_principal():   
    return render_template('formulario_registerFaceStudent.html')

@app.route("/Predictionemotion")
def pagina_principal2():   
    return render_template('formulario_rekognition_emotion.html')

@app.route("/Predictor",methods=['POST'])
def Predictor():    
    if request.method=='POST':
        f=request.files['archivo']       
        #name=request.form['username']       
        responseEmotion=prediccion(f)
        responseRekognition=Reconocimiento(f)
        response={
            "responseEmotion":responseEmotion,
            "responseRekognition":responseRekognition
            }
        #MOSTRAR LA RESPUESTA
        return {
            'statusCode': 200,
            'body': response 
        }      
    
@app.route("/Cargardata",methods=['POST'])
def Cargardata():    
    if request.method=='POST':
        f=request.files['archivo']        
        nombre=request.form['dni']
        response=RegisterFaceUser(nombre,f)
        #MOSTRAR LA RESPUESTA
        return {
            'statusCode': 200,
            'body': response        
        }      


if __name__=='__main__':
    app.run(host='0.0.0.0',port=8080,debug=True)
            
