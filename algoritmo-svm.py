import csv
import pandas as pd
import numpy as np
import math
from sklearn import svm
import time
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectFromModel
from sklearn.svm import LinearSVC
from sklearn import metrics
from ggplot import *

#-------------------------------------------------CONFIGURAR DATASET------------------------------------------------------------


traindata = []
trainlabel=[]

#ABRIR EL ARCHIVO
f = open( 'bank.csv', 'rU' ) 
for line in f:
    cells = line.split( ";" )
    
    traindata.append( ( cells[0:len(cells)-1 ] ) )
    trainlabel.append(cells[len(cells)-1].rstrip('\n'))   #REMOVER LOS: '\n' DEL CSV

np.savetxt("banktraindata.csv", traindata, fmt='%s', delimiter=",")		 
np.savetxt("banktrainlabel.csv", np.array(trainlabel).reshape(-1,1), fmt='%s', delimiter=",") 
f.close()

testdata = []
testlabel=[]

f = open( 'bank-full.csv', 'rU' ) #open the file in read universal mode
for line in f:
    cells = line.split( ";" )
    
    testdata.append( ( cells[0:len(cells)-1 ] ) ) 
    testlabel.append(cells[len(cells)-1].rstrip('\n'))

np.savetxt("banktestdata.csv", testdata, fmt= '%s', delimiter=",")		 
np.savetxt("banktestlabel.csv", np.array(testlabel).reshape(-1,1), fmt='%s', delimiter=",")	




#---------------------------------PROCESAR DATA----------------------------------------------------------------


def is_number(s):   #SABER SI SE TRATA DE UN NUMERO
    try:
        float(s)
        return True
    except ValueError:
        return False

def preprocess_label(file_name):	
	mycsvans = open(file_name, "rt")
	csvAns = csv.reader(mycsvans)		#LECTOR DEL ARCHIVO CSV

	headerans=next(csvAns, None)				#SALTAR LA PRIMERA ROW: EL DE ENCABEZADO
	ans=[]
	ind=0
    #para no contar encabezado:	
	for row in csvAns:  		
		if ind==0:
			ind+=1
			continue
		#print row								
		if row[0]=='yes' :
			ans.append(1)
		elif row[0]=='no' :
			ans.append(0)
	
	#print ans
	return ans

y_1=preprocess_label("banktestlabel.csv")
y=preprocess_label("banktrainlabel.csv")


def preprocess_data(file_name,y_labels):
	mycsvfile = open(file_name, "rt")
	csvFile = csv.reader(mycsvfile)



	header=next(csvFile, None)				#CABECERAS DEL CSV: CATEGORIAS	
	second_row=next(csvFile, None)				#USAR SEGUNDA FILA PARA SABER QUE TIPO DE VARIABLES TIENE CADA UNA DE LAS CABECERAS	
	column=[]						#TODOS LOS NOMBRES
	categorical= []						#CATEGORIAS NO NUMERICAS
	non_categorical= []					#CATEGORIAS QUE SON NUMERICAS


	i=0
	for index in range(len(second_row)):			#SELECCIONAR LAS CATEGORIAS: categorical y non_categorical
		i=i+1	    		
		column.append( header[index])
		if not is_number(second_row[index]): 
			categorical.append(header[index])			
		else :
			non_categorical.append(header[index])


	mycsvfile.seek(1)					#EXCLUIR LA PRIMERA FILA DEL ENCABEZADO
	mydictionary={}						#CONVERTIR CSV EN JSON: MAPEO

	for index in range(len(column)):
		mydictionary.update({column[index]:[]})
	ind=0
	for row in csvFile:		
		if ind==0:      
			ind+=1
			continue
		for index in range(len(column)):
			
			mydictionary[column[index]].append(row[index])
                
	df = pd.DataFrame(mydictionary, columns = column)	#CONVERTIR A DATAFRAME LAS COLUMNAS CON CATEGORIA NO NUMERICA
	df_new = pd.DataFrame(mydictionary, columns = non_categorical)	#CONVERTIR A DATAFRAME LAS COLUMNAS CON CATEGORIA NUMERICA
    
	for index in range(len(categorical)):			# LOOP PARA AGREGAR AL MARCO DE DATOS LOS VALORES CATEGORICOS NO NUMERICOS, LUEGO DE CONVERTIR A NUMERO
		temp=pd.get_dummies(df[categorical[index]])
		df_new = pd.concat([df_new,temp], axis=1)



	matrix=df_new.to_numpy()				#CONVERTIR FRAME A MATRIZ	
	A=np.squeeze(np.asarray(matrix))			#CONVERTIR DE MATRIZ A ARREGLO
	A=A.astype(int)						#CONVERTIR TODOS LOS VALORES DE LA MATRIZ A INT
 
	min_ofeachcol=A.min(0)					#MINIMO DE CADA COLUMNA
	max_ofeachcol=A.max(0)					#MAXIMO DE CADA COLUMNA

	print ("RE-ESCALAMIENTO DE VALORES...")
	A=(2.0*A - max_ofeachcol - min_ofeachcol)/(max_ofeachcol - min_ofeachcol) #RE-ESCALAMIENTO DE DATA 
	mean_ofeachcol=A.mean(0)
	std_ofeachcol=A.std(0)
    
	print ("ESTANDARIZANDO DATOS...")
	A=(1.0*A-mean_ofeachcol)/std_ofeachcol	

	i=0
	X= []
	
	for each in y_labels:
		X.append(A[i])
		#y.append(each)
		#each = np.append(A[i],each)
		#B.append(each)	
		i=i+1

	return X

X=preprocess_data("banktraindata.csv",y)
X_1=preprocess_data("banktestdata.csv",y_1)

#----------------------------------------SI SE DESEA MENORAR LA CANTIDAD DE DATA DE ENTRENAMIENTO----------------
X=X[0:int(len(X)/2)]
y=y[0:int(len(y)/2)]

#-------------------------- COMENZAR A CLASIFICAR: SVM-----------------------------------------------------

print ("ENTRENANDO SVM...")

#---------------------SELECCION DE CARACTERISTICAS------------------------------------------
svc = svm.SVC(C=8192, kernel='rbf', degree=2, gamma=0.00048828125, coef0=0.0, shrinking=True, probability=True,tol=0.001, cache_size=200, class_weight=None, verbose=False, max_iter=-1, random_state=None)
clf=svc	
clf.fit(X, y)

preds = clf.predict_proba(X_1)

cantidad_datos=10
print ("--------------------------RESULTADOS--------------------------")
preds_buscado=preds[0:cantidad_datos]
indFor=1
resp=''
for pred in preds_buscado: 
    resp="Prediccion registro N°"+str(indFor)    
    if pred[0]>pred[1]:
        resp+=':No suscrito, con una seguridad del: '+str(round(pred[0]*100,2))+"%"        
    else:
        resp+=':Suscrito, con una seguridad del: '+str(round(pred[1]*100,2))+"%"    
    indFor+=1
    print(resp)
      
print ("")
print ("PRECISION GENERAL PARA LA DATA DE TESTEO INGRESADA")
print (str(round(clf.score(X_1, y_1)*100,2)),"%")
print ("")
















