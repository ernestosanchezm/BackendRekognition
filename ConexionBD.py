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
from Entrenamiento import Entrenar
import json
import uuid
#-------------------------------------------------CONFIGURAR DATASET------------------------------------------------------------

def ExecuteQuery(query):    
    configBD={ 
        'host': "db-proyecto-mysql.cluster-cbwzye3glmch.us-east-1.rds.amazonaws.com",
        'user' : "sa",
        'passwd' : "luismiguel",
        'database' : "educati"}
    db = mysql.connect(**configBD)
    cursor = db.cursor()   
    cursor.execute(query)
    resBd=cursor.fetchall()      
    return resBd
    
    











