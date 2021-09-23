"""	Version echa a partir de Octubre 2019 retomando de nuevo el Proyecto Forja.
	Los datos del 'captor objetivo_2' se envian todos desde el automata a la Rpi
	en un solo topico conjunto. En el NX1 se concatenan, y aqui se "desconcatenan".
	En este caso la suma de los datos totales y demas se hace en el automata, por tanto
	los resultados que aqui llegan solamente se meten como dato y se suben.'"""



""" Informacion Sobre import y variables globales

#import Subscriptor_declaraciones
#from Subscriptor_declaraciones import*

Con import anado el modulo importado al espacio de memoria de este programa, por tanto para llamar a sus funciones
tengo que anadir el modulo del que uso esa funcion. p.e: Subscriptor_declaraciones.inicializaciones().
Con el 'from' importo todo lo de dentro del fichero a mi espacio de memoria, por tanto ya no tengo que decir la funcion
que uso de que fichero es. Ademas no tengo problema con las variables, cosa que con el import asecas si. PERO hay que usar
el from con moderacion y solo si se le llama muchas veces al fichero importado.
Eso SI, al importar, despues de comenzar el programa, las variables cambiadas en los suprogramas NO se cambian en el principal"""

import ssl
import sys

import paho.mqtt.client		#"""Para uso del protocolo MQTT"""
import requests				#"""Para los API REQUEST"""

from time import sleep
import json
import random
import RPi.GPIO as gpio		#importar libreria para uso de gpio con python


"""*****************Declaracion de variables GLOBALES**********************"""

client = paho.mqtt.client.Client(client_id='Rpi_Subscriptor', clean_session=False)  #Hago el cliente global para la funcion de interrupcion
topicos = ("Proyecto_Forja/Captor/Objetivo_1/Presion","Proyecto_Forja/Captor/Objetivo_1/Temperatura", 'Proyecto_Forja/Captor/Objetivo_2/Piezas_Buenas', 'Proyecto_Forja/Captor/Objetivo_2/Piezas_Malas/malas', 'Proyecto_Forja/Captor/Objetivo_2/Piezas_Malas/geometria','Proyecto_Forja/Captor/Objetivo_2/Piezas_Malas/orientacion','Proyecto_Forja/Captor/Objetivo_2/Piezas_Malas/color', 'Proyecto_Forja/Captor/Objetivo_2/Piezas_Totales', 'Proyecto_Forja/Captor/Objetivo_2/t_ciclo', 'Proyecto_Forja/Captor/Objetivo_3/OEE/disponibilidad','Proyecto_Forja/Captor/Objetivo_3/OEE/rendimiento','Proyecto_Forja/Control_Remoto/Permiso_CR', 'Proyecto_Forja/Control_Remoto/General_Proceso','Proyecto_Forja/Control_Remoto/Prensa_Hidraulica', 'Proyecto_Forja/Control_Remoto/Zona_2/Cinta', 'Proyecto_Forja/Control_Remoto/Zona_2/Camara', 'Proyecto_Forja/Control_Remoto/Prensa_Mecanica', 'Proyecto_Forja/Captor/Objetivo_2/resultados_ciclo')
			#'topicos' es una TUPLA, NO se puede modificar

firebase_url = 'https://ugle-forja-rtd.firebaseio.com/'

flag_inic = 'FALSE'
actualizacion = 'FALSE'
location = 'UGLE-Zumarraga'

Rpi_Conectada = 11		#Salida 11 de la board (GPIO 17  en el mapping). El "Output Relay 1" de Iono esta mapeada a esta salida

#Captor/Objetivo_1
dat_temperatura=25.2	#(C)
dat_presion=0	#(bar)
#Captor/Objetivo_2
dat_tciclo=0	#(s)
dat_pzas_totales=0
dat_pzas_buenas=0 
dat_pzas_malas=dat_pzas_totales-dat_pzas_buenas #empezamos a contar piezas buenas y malas desde 0
dat_pzas_malas_geometria=0
dat_pzas_malas_color=0
dat_pzas_malas_orientacion=0

dat_resultados_ciclo = "0-0-0-0"	#De primeras por si acaso hacemos que sea 0 todo

#Captor/Objetivo_3
dat_OEE=0	#(%)
dat_disponibilidad=0	#estos datos los cogere pero no los incluire en json
dat_rendimiento=0

#Control_Remoto
dat_permiso="True"
dat_general_proceso="Esperando_Ini"
dat_prensa_hidraulica="Arriba"
dat_camara="Off"
dat_cinta="Parada"
dat_prensa_mecanica="Posicion_Ini"

#Este es el objeto modelo de Python de nuestros datos que luego convertiremos en json
datos_iniciales_json_minified={"Proyecto_Forja":{"Captor":{"Objetivo_1":{"Temperatura":25,"Presion":0.5},"Objetivo_2":{"t_ciclo":5,"Piezas_Totales":0,"Piezas_Buenas":0,"Piezas_Malas":{"malas":0,"geometria":0,"color":0,"orientacion":0}},"Objetivo_3":{"OEE":85}},"Control_Remoto":{"Permiso_CR":"Espera_Ini","General_Proceso":"Esperando_Ini","Prensa_Hidraulica":"Arriba","Zona_2":{"Cinta":"OFF","Camara":"Mala"},"Prensa_mecanica":"Parada"}}}
#Al hacer "json.dumps()" parseamos el objeto de python en un string json
json_data_string=json.dumps(datos_iniciales_json_minified,indent=4,sort_keys=True,separators=(', ',': '))
#Al hacer "json.load()" convertimos el string json en un objeto python para poder manipularlo correctamente en python
objeto_datos_python=json.loads(json_data_string)
json_firebase_string=""

"""*******************************************************"""


"""*******************Funciones de programa, tanto 'Callbacks' como definidas**************************"""
def on_connect(client, userdata, flags, rc): 
	global topicos
	global Rpi_Conectada
	
	gpio.output(Rpi_Conectada,True)
	print('connected (%s)' % client._client_id)             #el 'client_id' indica quien soy yo, mi nombre
	i=0
	for i in range(len(topicos)):							#con esto me subscribo a todos los topicos guardados en la tupla
		client.subscribe(topic=topicos[i], qos=2)
		print("\nSubscrito a %s" %topicos[i])
 
def on_message(client, userdata, message):	#Esta funcion solo se ejecuta al recibir mensaje mediante el network loop y es tratada como si una
											#interrupcion fuera en el programa principal"""
	#Declaracion de las variables GLOBALES que va a usar la funcion
	
	#Captor/Objetivo_1
	global dat_temperatura
	global dat_presion
	#Captor/Objetivo_2
	global dat_tciclo
	global dat_pzas_totales
	global dat_pzas_buenas
	global dat_pzas_malas
	global dat_pzas_malas_geometria
	global dat_pzas_malas_color
	global dat_pzas_malas_orientacion
	
	global dat_resultados_ciclo
	
	#Captor/Objetivo_3
	global dat_OEE
	global dat_disponibilidad
	global dat_rendimiento
	#Control_Remoto
	global dat_permiso
	global dat_general_proceso
	global dat_prensa_hidraulica
	global dat_camara
	global dat_cinta
	global dat_prensa_mecanica

	#Declaracion de variables LOCALES de la funcion
	mensaje_r=message.payload
	topico_r=message.topic
	
	global actualizacion
    
	print('------------------------------')                 
	print('topic: \n%s' % topico_r)
	print('payload: %s' % mensaje_r)

	if topico_r == topicos[0]:		#Proyecto_Forja/Captor/Objetivo_1/Presion
		dat_presion=mensaje_r
		actualizacion='TRUE'	#A fecha 20191126 se generan random por la Rpi y se envian cada ciclo de actualizacion
	
	elif topico_r == topicos[1]:	#Proyecto_Forja/Captor/Objetivo_1/Temperatura
		dat_temperatura=mensaje_r
		actualizacion='TRUE'	#A fecha 20191126 se generan random por la Rpi y se envian cada ciclo de actualizacion
	
	elif topico_r == topicos[2]:	#Proyecto_Forja/Captor/Objetivo_2/Piezas_Buenas
		dat_pzas_buenas=mensaje_r
		actualizacion='TRUE'
		
	elif topico_r == topicos[3]:	#Proyecto_Forja/Captor/Objetivo_2/Piezas_Malas/malas
		dat_pzas_malas=mensaje_r
		actualizacion='TRUE'
		
	elif topico_r == topicos[4]:	#Proyecto_Forja/Captor/Objetivo_2/Piezas_Malas/geometria
		dat_pzas_malas_geometria=mensaje_r
		actualizacion='TRUE'
	
	elif topico_r == topicos[5]:	#Proyecto_Forja/Captor/Objetivo_2/Piezas_Malas/orientacion
		dat_pzas_malas_orientacion=mensaje_r
		actualizacion='TRUE'
	
	elif topico_r == topicos[6]:	#Proyecto_Forja/Captor/Objetivo_2/Piezas_Malas/color
		dat_pzas_malas_color=mensaje_r
		actualizacion='TRUE'
	
	elif topico_r == topicos[7]:	#Proyecto_Forja/Captor/Objetivo_2/Piezas_Totales
		dat_pzas_totales=mensaje_r
		actualizacion='TRUE'
		
	elif topico_r == topicos[8]:	#Proyecto_Forja/Captor/Objetivo_2/t_ciclo
		dat_tciclo=mensaje_r
		actualizacion='TRUE'
		
	elif topico_r == topicos[9]:	#Proyecto_Forja/Captor/Objetivo_3/OEE/disponibilidad
		dat_disponibilidad=mensaje_r
		actualizacion='TRUE'
	
	elif topico_r == topicos[10]:	#Proyecto_Forja/Captor/Objetivo_3/OEE/rendimiento
		dat_rendimiento=float(mensaje_r)
		actualizacion='TRUE'
	
	elif topico_r == topicos[11]:	#Proyecto_Forja/Control_Remoto/Permiso_CR
		dat_permiso=mensaje_r
		actualizacion='TRUE'
	
	elif topico_r == topicos[12]:	#Proyecto_Forja/Control_Remoto/General_Proceso
		dat_general_proceso=mensaje_r
		actualizacion='TRUE'
		
	elif topico_r == topicos[13]:	#Proyecto_Forja/Control_Remoto/Prensa_Hidraulica
		dat_prensa_hidraulica=mensaje_r
		actualizacion='TRUE'
		
	elif topico_r == topicos[14]:	#Proyecto_Forja/Control_Remoto/Zona_2/Cinta
		dat_cinta=mensaje_r
		actualizacion='TRUE'
	
	elif topico_r == topicos[15]:	#Proyecto_Forja/Control_Remoto/Zona_2/Camara
		dat_camara=mensaje_r
		actualizacion='TRUE'
		
	elif topico_r == topicos[16]:	#Proyecto_Forja/Control_Remoto/Prensa_Mecanica
		dat_prensa_mecanica=mensaje_r
		actualizacion='TRUE'
		
	elif topico_r == topicos[17]:	#Proyecto_Forja/Captor/Objetivo_2/resultados_ciclo
		dat_resultados_ciclo=mensaje_r
		actualizacion = 'TRUE'


	#else: print("\n El topico del mensaje recibido no corresponde a ningun topico subscrito \n")
	"""Este ultimo 'else' no tiene sentido porque al programa nunca le llegara un mensaje de un topico al que no esta
	   subscrito, por tanto nunca entraria en el mesaje, ya que siempre que ejecute 'on_message' sera porque le ha llegado
	   algo de algun topico al que esta subscrito."""

		
def on_disconnect(client, userdata, rc):
	global Rpi_Conectada
	
	gpio.output(Rpi_Conectada,False)
	print('\n Cliente " %s " desconectado del host  \n' % client._client_id )
	print "Programa de Forja detenido\n"
	sys.exit(0)

 
def inicializaciones():
	"""Declaracion de las variables GLOBALES a usar por la funcion"""
	global flag_inic
	global json_data_string
	global location
	global Rpi_Conectada
	
	gpio.setmode(gpio.BOARD)
	gpio.setup(Rpi_Conectada,gpio.OUT)
	
	random.seed()	#Para cambiar la semilla. Si no se dice nada por default coge el tiempo del sistema
	
	print "\nPrograma Raspberry de forja en Ejecucion \n"
	
	#Inicializacion de funciones del protocolo MQTT
	client.on_connect = on_connect                  #Funcion que se ejecuta cuando el broker responde a la peticion de conexion del cliente
	client.on_disconnect = on_disconnect            #Funcion que se ejecuta cuando el cliente se desconecta del broker
	client.on_message = on_message                  #Funcion llamada caundo el cliente al que se le asigna la funcion ("client") recibe un mensaje
                                                    #sobre un "topico" al que esta subscrito
	client.connect(host='localhost', port=1883)     #El cliente se conecta al 'Broker' mencionado, que en este caso esta en el localhost
	client.loop_start()
	
	print("\n%s" %json_data_string)
	json_firebase_string=json.dumps(objeto_datos_python)
	result_put = requests.put(firebase_url+location+".json/", json_firebase_string)
	#print result_put.url
	if(result_put.status_code==200):
		print("\nDatos cargados con exito a la base de datos. Status code: %s\n" %result_put.status_code)
	else:
		print('\n Ha Habido algun problema al comunicar con el servidor. Status code : %s' %result_put.status_code)
	
	
def actualizar_datos_json():
	global objeto_datos_python
	global json_data_string
	global json_firebase_string
	
	#Captor/Objetivo_1
	global dat_temperatura
	global dat_presion
	
	#Captor/Objetivo_2
	global dat_tciclo
	global dat_pzas_totales
	global dat_pzas_buenas
	global dat_pzas_malas
	global dat_pzas_malas_geometria
	global dat_pzas_malas_color
	global dat_pzas_malas_orientacion
	
	global dat_resultados_ciclo
	
	#Captor/Objetivo_3
	global dat_OEE
	global dat_disponibilidad
	global dat_rendimiento
	
	#Control_Remoto
	global dat_permiso
	global dat_general_proceso
	global dat_prensa_hidraulica
	global dat_camara
	global dat_cinta
	global dat_prensa_mecanica
	
	#dat_presion y dat_temperatura vienen del automata por tanto eso es lo que se sube
	#A fecha 20191126 se generan random por la Rpi y se envian cada ciclo de actualizacion
	dat_temperatura = random.uniform(100,150)	#grados
	dat_presion = random.uniform(0,200)	#bar
	objeto_datos_python['Proyecto_Forja']['Captor']['Objetivo_1']['Temperatura']=dat_temperatura
	objeto_datos_python['Proyecto_Forja']['Captor']['Objetivo_1']['Presion']=dat_presion

	#Aqui tengo que 'desconcatenar' los datos recibidos que han venido concatenados
	"""dat_resultados_ciclo = pzas_buenas-pzas_malas-pzas_totales-t_ciclo"""
		
	resultados_ciclo_lista=dat_resultados_ciclo.split('-')
	dat_pzas_buenas=resultados_ciclo_lista[0]
	dat_pzas_malas=resultados_ciclo_lista[1]
	dat_pzas_totales=resultados_ciclo_lista[2]
	dat_tciclo=resultados_ciclo_lista[3]
	
	print(resultados_ciclo_lista)
		
	objeto_datos_python['Proyecto_Forja']['Captor']['Objetivo_2']['t_ciclo']=dat_tciclo
	objeto_datos_python['Proyecto_Forja']['Captor']['Objetivo_2']['Piezas_Totales']=dat_pzas_totales
	objeto_datos_python['Proyecto_Forja']['Captor']['Objetivo_2']['Piezas_Buenas']=dat_pzas_buenas
	objeto_datos_python['Proyecto_Forja']['Captor']['Objetivo_2']['Piezas_Malas']['malas']=dat_pzas_malas
	objeto_datos_python['Proyecto_Forja']['Captor']['Objetivo_2']['Piezas_Malas']['geometria']=dat_pzas_malas_geometria
	objeto_datos_python['Proyecto_Forja']['Captor']['Objetivo_2']['Piezas_Malas']['color']=dat_pzas_malas_color
	objeto_datos_python['Proyecto_Forja']['Captor']['Objetivo_2']['Piezas_Malas']['orientacion']=dat_pzas_malas_orientacion
	
	#dat_OEE=float(dat_rendimiento)*float(dat_disponibilidad)
	#print "OEE:  " + str(dat_OEE)
	objeto_datos_python['Proyecto_Forja']['Captor']['Objetivo_3']['OEE']=dat_OEE	#El OEE es un valor float sacado de otros calculos con otros parametros
	
	objeto_datos_python['Proyecto_Forja']['Control_Remoto']['Permiso_CR']=dat_permiso
	objeto_datos_python['Proyecto_Forja']['Control_Remoto']['General_Proceso']=dat_general_proceso
	objeto_datos_python['Proyecto_Forja']['Control_Remoto']['Prensa_Hidraulica']=dat_prensa_hidraulica
	objeto_datos_python['Proyecto_Forja']['Control_Remoto']['Zona_2']['Camara']=dat_camara
	objeto_datos_python['Proyecto_Forja']['Control_Remoto']['Zona_2']['Cinta']=dat_cinta
	objeto_datos_python['Proyecto_Forja']['Control_Remoto']['Prensa_mecanica']=dat_prensa_mecanica
	
	json_data_string=json.dumps(objeto_datos_python,indent=4,sort_keys=True,separators=(', ',': '))
	json_firebase_string=json.dumps(objeto_datos_python)
 


def main():         #define todas las funcionalidades con "def" para asi si se quiere importarlas desde otro fichero
	"""Declaracion de las variables GLOBALES que va a usar la funcion"""
	global actualizacion
	global objeto_datos_python
	global json_data_string
	global firebase_url
	global json_firebase_string
	
	inicializaciones()
	
	while True:     #Programa principal
		while actualizacion != 'TRUE':
			sleep(0.1) #Esperamos a que haya algun dato que actualizar
		actualizar_datos_json()
		print("\n Los datos Json han sido actualizados, aqui estan los nuevos datos: \n")
		print("%s\n" %json_data_string)
		actualizacion='FALSE'
		result_put = requests.put(firebase_url+location+".json/", json_firebase_string)
		#print result_put.url
		if(result_put.status_code==200):
			print("\nDatos cargados con exito a la base de datos. Status code: %s\n" %result_put.status_code)
		else:
			print('\n Ha Habido algun problema al comunicar con el servidor. Status code : %s' %result_put.status_code)

"""*****************************************************"""


if __name__ == '__main__':
    try:
        main()
    
    except KeyboardInterrupt:   #Esto se ejecuta cuando se crea la excepcion 'ctl+c'
		client.loop_stop()      #Funcion para parar el flujo netwoork loop que se esta ejecutando en background
		client.disconnect()

