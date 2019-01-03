from multiprocessing import Process, Value, Lock, Array
import sysv_ipc
import random
from time import sleep
import datetime
from concurrent.futures import ThreadPoolExecutor
import sys
from threading import Thread


mutex = Lock()

class Home(Process):

	numberOfHomes=0

	def __init__(self,productionRate, consumptionRate,shared_nb_homes,shared_homeKEYs):
		super().__init__()
		shared_nb_homes.value +=1
		Home.numberOfHomes+=1
		self.budget=1000
		self.productionRate=productionRate
		self.consumptionRate=consumptionRate
		self.energy=0
		self.homeNumber=Home.numberOfHomes
		shared_homeKEYs[self.homeNumber-1] = (130+self.homeNumber)
		print("Nb of Homes has been added :")
		print(shared_nb_homes.value)
		print("Home KEYs has been updated :")
		for w in range(len(shared_homeKEYs)):
			print(shared_homeKEYs[w])
		#TODO ajouter code pour quand on CTRL+C ca ferme la mq
	def init_Queue(self):
		self.mq = sysv_ipc.MessageQueue(shared_homeKEYs[self.homeNumber-1])

	def run(self):
		go = 0
		while (go == 0):
			try:
				self.mq
			except:
				print("Mq not exists yet")
				sleep(2)
			else:
				go = 1

		while 1:
			print("Home {}: My budget is {} dollars.".format(self.homeNumber,self.budget))
			self.energy=self.productionRate-self.consumptionRate

			if self.energy<0:
				self.buy()
			elif self.energy>0:
				self.sell()


			if self.budget<0:
				print("Home {}: Shit I'm broke!".format(self.homeNumber))
				self.sendMessageQueue('Broke')
				break
			else:
				self.sendMessageQueue('Nothing')


			sleep(5)

	def sendMessageQueue(self,n):
		self.mq.send(str(n).encode())
		print("Home{} sent: {}".format(self.homeNumber,n))


	def receiveMessageQueue(self):
		message, t = self.mq.receive()
		value = message.decode()
		print("Home{} recieved: {}".format(self.homeNumber,value))
		if((value != "Buy") or (value != "Nothing")):
			value = int(value)
		return value


	def buy(self):
		print("Home {}: What's the price? I wanna buy some energy.".format(self.homeNumber))
		self.sendMessageQueue('Buy')
		temporary=self.receiveMessageQueue()
		if((temporary != "Buy") or (temporary != "Nothing")):
			price=temporary
			print("Home {}: It seems the price is {} dollars.".format(self.homeNumber,price))
			self.budget+=self.energy*price
		else :
			print("There is an error, anyway...")

	def sell(self):
		print("Home {}: What's the price? I wanna sell some energy.".format(self.homeNumber))
		self.sendMessageQueue('Sell')
		price=self.receiveMessageQueue()
		print("Home {}: It seems the price is {} dollars.".format(self.homeNumber,price))
		self.budget+=self.energy*price




#TODO Protect price + create thread pool
class Market(Process):

	def __init__(self,shared_temp,shared_sunny,shared_nb_Homes,shared_homeKEYs):
		super().__init__()
		self.price=20
		print("Market :For the moment there is :")
		print(shared_nb_Homes.value)
		print("Market updated list of KEYs")
		for w in range(len(shared_homeKEYs)):
			print(shared_homeKEYs[w])
		self.shared_nb_Homes = shared_nb_Homes
		self.shared_homeKEYs = shared_homeKEYs
		self.mqExists = False

	def lookAtRequests(self):
		print("Look at request launched")
		while(self.mqExists == False):
			sleep(5)

		while 1:
			for x in range(0,self.shared_nb_Homes.value):
				value=self.receiveMessageQueue(x)
				if (value != ''):
					with ThreadPoolExecutor(max_workers = 3) as executor :
						self.handleRequest(value)

	def handleRequest(self,msg):
		if msg=='Broke':
			print('Market: No more homes alive :(')

		elif msg=='Buy':
			#TODO protect price when reading and create a copy !!!
			#PAS SUR DE MUTEX OU SEMAPHORE
			with mutex:
				print('Market: The price of energy is %s dollars.' %self.price)
				self.sendMessageQueue(self.price)
			print('Market: Energy is bought.')
			print("Market: Increasing the price")
			with mutex:
				self.price+=5 #TODO Empecher le market de descendre en dessous de 0

		elif msg=='Sell':
			#TODO protect price when reading and create a copy !!!
			print('Market: The price of energy is %s dollars.' %self.price)
			self.sendMessageQueue(self.price)
			print('Market: Energy is sold.')
			print("Market: Decreasing the price")
			self.price-=2


	def run(self):

		requestLook = Thread(target=self.lookAtRequests(), args= ())
		requestLook.start()
		print("Before entering the loop")
		while 1:
			sleep(5)
			print("Entering the loop...")
			for z in range(self.shared_nb_Homes.value):
				try:
					self.mq[z]
				except IndexError:
					self.mq[-1]=sysv_ipc.MessageQueue(self.shared_homeKEYs[z],sysv_ipc.IPC_CREAT)
					self.mqExists = True
		#TODO bouger ligne 120	#The price goes down over time if noone buys any energy.			self.price=int(self.price-temperature.value/10-sunny.value)			#If it's hot and sunny then energy is cheap and if it's dark and cold it's expensive.
		print('Market: The price of energy is now %s dollars.' %self.price)


	def sendMessageQueue(self, n):
		self.mq.send(str(n).encode())
		print("Market sent: {}".format(n))

	def receiveMessageQueue(self,indice):
		message, t = self.mq[indice].receive()
		value = message.decode()
		print("Market recieved: {}".format(value))
		return value


class Weather(Process):
	def __init__(self):
		super().__init__()


	def run(self):
		while 1:
			current=datetime.datetime.now()			#We get the current date and time and use them to get the temperature.

			if current.month==1:
				temperature.value=3
			elif current.month==2:
				temperature.value=5
			elif current.month==3:
				temperature.value=8
			elif current.month==4:
				temperature.value=11
			elif current.month==5:
				temperature.value=16
			elif current.month==6:
				temperature.value=19
			elif current.month==7:
				temperature.value=22
			elif current.month==8:
				temperature.value=22
			elif current.month==9:
				temperature.value=18
			elif current.month==10:
				temperature.value=13
			elif current.month==11:
				temperature.value=8
			elif current.month==12:
				temperature.value=4



			#...
			#...
			#Do something similar with hour.






			print("Weather: The datetime is {}.".format(current))


			sunny.value=random.randint(0,2)					#50% sunny 50% cloudy
															#or we could do something similar to temperature where we use the months and hours to determine the probability
															#but for now it's ok
			if sunny.value:
				print("Weather: The temperature is {}°C and it is sunny.".format(temperature.value))
			else:
				print("Weather: The temperature is {}°C and it is cloudy.".format(temperature.value))

			sleep(10)




if __name__=="__main__":

	temperature=Value('d', 12.5)

	sunny=Value('i', 1)  # 1: sunny, 0: cloudy
	nb_Homes=Value("i",0)
	homeKEYs=Array("i",[0]*10)
	weather=Weather()
	weather.start()

	sleep(1)
	market=Market(temperature,sunny,nb_Homes,homeKEYs)
	market.start()
	sleep(1)

	home1=Home(0,10,nb_Homes,homeKEYs)
	home1.start()






	# sleep(1)

	#home2=Home(10,8)
	#home2.start()
