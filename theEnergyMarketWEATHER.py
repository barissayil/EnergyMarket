from multiprocessing import Process, Value
import sysv_ipc
import random
from time import sleep
import datetime
import concurrent.futures
import sys
import threading

class Home(Process):

	numberOfHomes=0

	def __init__(self,productionRate, consumptionRate):
		super().__init__()
		Home.numberOfHomes+=1
		self.budget=1000
		self.productionRate=productionRate
		self.consumptionRate=consumptionRate
		self.energy=0
		self.homeNumber=Home.numberOfHomes
		self.mq = sysv_ipc.MessageQueue(126)

	def run(self):
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
				self.sendMessageQueue('Nothing') #Je ne comprends pas pk on envoie ca


			sleep(5)

	def sendMessageQueue(self,n):
		self.mq.send(str(n).encode())

	def receiveMessageQueue(self):
		message, t = self.mq.receive()
		value = message.decode()
		value = int(value)
		return value


	def buy(self):
		print("Home {}: What's the price? I wanna buy some energy.".format(self.homeNumber))
		self.sendMessageQueue('Buy')
		price=self.receiveMessageQueue()
		print("Home {}: It seems the price is {} dollars.".format(self.homeNumber,price))
		self.budget+=self.energy*price

	def sell(self):
		print("Home {}: What's the price? I wanna sell some energy.".format(self.homeNumber))
		self.sendMessageQueue('Sell')
		price=self.receiveMessageQueue()
		print("Home {}: It seems the price is {} dollars.".format(self.homeNumber,price))
		self.budget+=self.energy*price




#TODO Protect price + create thread pool
class Market(Process):

	def __init__(self):
		super().__init__()
		self.price=20
		self.mq = sysv_ipc.MessageQueue(126,sysv_ipc.IPC_CREAT)

	def lookAtRequests(self):
		while 1:
			value=self.recieveMessageQueue()
			if (value != ''):
				with concurrent.futures.ThreadPoolExecutor(max_workers = 3) as executor :
					handleRequest(self,value)
					
	def handleRequest(self,msg):
		if value=='Broke':
			print('Market: No more homes alive :(')
			break
		elif value=='Buy':
			print('Market: The price of energy is %s dollars.' %self.price)
			self.sendMessageQueue(self.price,1)
			print('Market: Energy is bought.')
			print("Market: Increasing the price")
			self.price+=5
		elif value=='Sell':
			print('Market: The price of energy is %s dollars.' %self.price)
			self.sendMessageQueue(self.price,1)
			print('Market: Energy is sold.')
			print("Market: Decreasing the price")
			self.price-=2


	def run(self):
		while 1:

			value=self.receiveMessageQueue()



			# self.price-=1							#The price goes down over time if noone buys any energy.
			self.price=int(self.price-temperature.value/10-sunny.value)			#If it's hot and sunny then energy is cheap and if it's dark and cold it's expensive.
			print('Market: The price of energy is now %s dollars.' %self.price)

			#Le market ne doit jamais sleep

	def sendMessageQueue(self, n, h):
		self.mq.send(str(n).encode())

	def receiveMessageQueue(self):
		message, t = self.mq.receive()
		value = message.decode()
		print(value)
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

	weather=Weather()
	weather.start()

	sleep(1)

	market=Market()
	market.start()

	sleep(1)

	home1=Home(0,10)
	home1.start()

	# sleep(1)

	home2=Home(10,8)
	home2.start()
