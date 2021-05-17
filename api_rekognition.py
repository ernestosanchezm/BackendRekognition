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
from entrenandoRF import GenerarModelo
import json
import uuid

app=Flask(__name__)
app.config['UPLOAD_FOLDER_IMAGENES']="./Imagenes"
app.config['UPLOAD_FOLDER_IMAGENES_RQST']="./ImagenesRQST"
app.config['UPLOAD_FOLDER_VIDEOS']="./VideosData"
app.config['UPLOAD_FOLDER_VIDEOS_DATASET']="./VideosDataSet"
                
configBD={ 
    'host': "db-proyecto-mysql.cluster-cbwzye3glmch.us-east-1.rds.amazonaws.com",
    'user' : "sa",
    'passwd' : "luismiguel",
    'database' : "educati"}

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
    		
        nombreUser=(GetUserForDni(str(format(imagePaths[result[0]]))))["nombre"]
        return (nombreUser)  
        
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
            
    for element in response["FaceDetails"][0]["Emotions"]:
        if mayor_confidence==element["Confidence"]:
            _response={
                "Security":element["Confidence"],
                "Emotion":element["Type"]              
                }
                
    return _response
 
def RegisterFaceUser(dni,f):    
    objUser=GetUserForDni(dni)    
    
    if objUser['error']==True:
        return objUser['mensaje']         
              
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
    
    GenerarModelo()
    return "Registro exitoso "+objUser['nombre']


def RegistarDataset(f):          
    nombreVideo=str(uuid.uuid4())
    dataPath = app.config['UPLOAD_FOLDER_IMAGENES']   
    f.save(os.path.join(app.config['UPLOAD_FOLDER_VIDEOS_DATASET'],nombreVideo+".mp4"))  
    
    #luego de guardar el video, usarlo de captura
    videoPersonaPath=app.config['UPLOAD_FOLDER_VIDEOS_DATASET']+"/"+nombreVideo+".mp4"
    cap = cv2.VideoCapture(videoPersonaPath)          
    
    faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
    count = 0
    respuestas=[]
    
    #CONFIGURAR LOS ACCESOS
    client=boto3.client('rekognition',
                          region_name='us-east-2',
                          aws_access_key_id="AKIA6P46JAOPIR5NGNNC",
                          aws_secret_access_key="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"
                          )  
    cantCONFUSED=0
    cantANGRY=0
    cantDISGUSTED=0
    cantSAD=0
    cantCALM=0
    cantSURPRISED=0
    cantFEAR=0
    cantHAPPY=0
    
    mayor_confidence=0
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
              cv2.imshow('image', rostro)
              imagen=cv2.imencode('.jpg', rostro)[1].tostring()                      
              #Uso de AWS para la deteccion
              response=client.detect_faces(
                 Image={'Bytes':imagen},  
                 Attributes=['ALL'])    
                          
             

              _response=''
              try:        
                   for element in response["FaceDetails"][0]["Emotions"]:
                       if element["Confidence"]>mayor_confidence:
                           mayor_confidence=element["Confidence"]   
                        
                   for element in response["FaceDetails"][0]["Emotions"]:
                       if mayor_confidence==element["Confidence"]:
                           if element["Type"]=='CONFUSED':
                               cantCONFUSED+=1
                           if element["Type"]=='ANGRY':
                               cantANGRY+=1
                           if element["Type"]=='DISGUSTED':
                               cantDISGUSTED+=1                          
                           if element["Type"]=='SAD':
                               cantSAD+=1
                           if element["Type"]=='CALM':
                               cantCALM+=1
                           if element["Type"]=='SURPRISED':
                               cantSURPRISED+=1
                           if element["Type"]=='FEAR':
                               cantFEAR+=1
                           if element["Type"]=='HAPPY':
                               cantHAPPY+=1
                               
              except:
                   print('error')
              finally:
                   count = count + 1                     
              
     	k =  cv2.waitKey(1)
     	if k == 27 or count >=50:
              break
    total=cantCONFUSED+cantANGRY+cantDISGUSTED+cantSAD+cantCALM+cantSURPRISED+cantFEAR+cantHAPPY
    pCONFUSED=round(cantCONFUSED*100/total,2)
    pANGRY=round(cantANGRY*100/total,2)
    pDISGUSTED=round(cantDISGUSTED*100/total,2)
    pSAD=round(cantSAD*100/total,2)
    pCALM=round(cantCALM*100/total,2)
    pSURPRISED=round(cantSURPRISED*100/total,2)
    pFEAR=round(cantFEAR*100/total,2)
    pHAPPY=round(cantHAPPY*100/total,2)
    
    
    respuestas.append(pCONFUSED) 
    respuestas.append(pANGRY) 
    respuestas.append(pDISGUSTED) 
    respuestas.append(pSAD) 
    respuestas.append(pCALM) 
    respuestas.append(pSURPRISED) 
    respuestas.append(pFEAR) 
    respuestas.append(pHAPPY) 
    
    return respuestas

    
def GetUserForToken(token):    
    resBd=[]
    try:
        #CONECCION A MYSQL
        db = mysql.connect(**configBD)
        cursor = db.cursor()
        query = "select * from Users u where u.token="+str(token)
        cursor.execute(query)
        resBd=cursor.fetchall()         
        if len(resBd)==1: 
            resBd={       
                "error":False,
                "mensaje":"Consulta exitosa",
                "nombre":resBd[0][1],
                "dni":resBd[0][4],
                }            
        else:
            return {       
                "error":True,
                "mensaje":"No se encontraron registros o se encontraros multiples",
                "nombre":None,
                "dni":None,
                }          
    except:        
        return {       
                "error":True,
                "mensaje":"Ocurrio un error inesperado",
                "nombre":None,
                "dni":None,
                } 
    
    return resBd

def GetUserForDni(dni):    
    resBd=None
    try:
        #CONECCION A MYSQL
        db = mysql.connect(**configBD)
        cursor = db.cursor()
        query = "select * from Users u where u.dni="+str(dni)
        cursor.execute(query)
        resBd=cursor.fetchall()         
        
        if len(resBd)==1: 
            resBd={       
                "error":False,
                "mensaje":"Consulta exitosa",
                "nombre":resBd[0][1],
                "dni":resBd[0][4],
                }              
        else:
            return {       
                "error":False,
                "mensaje":"Se encontraron múltiples registros",
                "nombre":None,
                "dni":None,
                }   
            
    except:        
        return {       
                "error":False,
                "mensaje":"Ocurrio un error inesperado",
                "nombre":None,
                "dni":None,
                }    
    return resBd

def ValidarToken(token):        
    objUsuario=GetUserForToken(token)        
    if objUsuario["error"]==True:
        return False
    
    return True    
    
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
        token=request.headers.get('token')
        #VALIDAR TOKEN
        if ValidarToken(token)==False:
            return {
                'statusCode': 400,
                'body': "Error de Autenticación"
                } 
        
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
        dni=request.form['dni']
        token=request.headers.get('token')
        #VALIDAR TOKEN
        if ValidarToken(token)==False:
            return {
                'statusCode': 400,
                'body': "Error de Autenticación"
                } 
        
        response=RegisterFaceUser(dni,f)
        #MOSTRAR LA RESPUESTA
        return {
            'statusCode': 200,
            'body': response        
        }      

@app.route("/registrardataset",methods=['POST'])
def RegistroDataset():    
    if request.method=='POST':
        f=request.files['archivo']        
        EDAD=int(request.form['EDAD'])
        NOMBRE=str(request.form['NOMBRE'])
        CURSO=str(request.form['CURSO'])
        SEXO=str(request.form['SEXO'])
        NOTA=int(request.form['NOTA'])
        RESULTADO=str(request.form['RESULTADO'])
        GRADO=int(request.form['GRADO'])
        token=request.headers.get('token')
        # VALIDAR TOKEN
        if ValidarToken(token)==False:
            return {
                'statusCode': 400,
                'body': "Error de Autenticación"
                } 
        res=RegistarDataset(f)
        
        #CONECCION A MYSQL
        db = mysql.connect(**configBD)
        cursor = db.cursor()                
        sql="insert into DATASET(CONFUSED,ANGRY,DISGUSTED,SAD,CALM,SURPRISED,FEAR,HAPPY,EDAD,NOMBRE,CURSO,SEXO,NOTA,RESULTADO,GRADO) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        datos=(res[0],res[1],res[2],res[3],res[4],res[5],res[6],res[7],EDAD,NOMBRE,CURSO,SEXO,NOTA,RESULTADO,GRADO)    
        cursor.execute(sql, datos)   
        db.commit()
        db.close()    
        
        response={}
        for elem in res:
            response={
                'CONFUSED':res[0],
                'ANGRY':res[1],
                'DISGUSTED':res[2],
                'SAD':res[3],
                'CALM':res[4],
                'SURPRISED':res[5],
                'FEAR':res[6],
                'HAPPY':res[7],
                'EDAD':EDAD,
                'NOMBRE':NOMBRE,
                'CURSO':CURSO,
                'SEXO':SEXO,
                'NOTA':NOTA,
                'RESULTADO':RESULTADO,
                'GRADO':GRADO
                }
        #MOSTRAR LA RESPUESTA
        return {
            'statusCode': 200,
            'body':  response       
        }      

if __name__=='__main__':
    app.run(host='0.0.0.0',port=8080,debug=True)
            
