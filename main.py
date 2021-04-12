# -*- coding: utf-8 -*-
"""
Created on Wed Mar 31 15:34:01 2021

@author: Ryzen
"""
import os
import csv
import boto3
import io

from botocore.config import Config
from flask import Flask,render_template,request
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage    
import json

app=Flask(__name__)
app.config['UPLOAD_FOLDER']="./Imagenes"

def prediccion(f):    
    #CONFIGURAR LOS ACCESOS
     client=boto3.client('rekognition',
                    region_name='us-east-2',
                    aws_access_key_id="AKIA6P46JAOPIR5NGNNC",
                    aws_secret_access_key="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"
                    )     
     filename=secure_filename(f.filename)
     f.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))    
     #Uso de AWS para la deteccion
     response=client.detect_faces(
         Image={'Bytes':f.getvalue()},  
         Attributes=['ALL']) 
     
     return response


@app.route("/")
def pagina_principal():   
    return render_template('formulario.html')

@app.route("/Predictor",methods=['POST'])
def Predictor():    
    if request.method=='POST':
        f=request.files['archivo']        
        response=prediccion(f)
        #MOSTRAR LA RESPUESTA
        return {
            'statusCode': 200,
            'body': response        
        }      
    
if __name__=='__main__':
    app.run(debug=True)
            
