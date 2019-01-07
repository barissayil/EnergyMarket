from multiprocessing import Process, Value, Lock, Array
from sysv_ipc import MessageQueue, IPC_CREAT
import random
from time import sleep
import datetime
from concurrent.futures import ThreadPoolExecutor
import sys
from threading import Thread


mutex = Lock()

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
		self.messageQueueList=[]
		self.messageQueueList.append(MessageQueue(1000))
		print("Home {}'s messageQueueList: {}".format(self.homeNumber, self.messageQueueList))
		self.sendMessage(0, self.homeNumber)
		

	def run(self):





		theMQhasBeenCreated = 0
		while theMQhasBeenCreated == 0:
			try:
				self.messageQueueList.append(MessageQueue(self.homeNumber))
			except:
				print("Mq not exists yet")
				sleep(2)
			else:
				theMQhasBeenCreated = 1
				print("Home: MQ created !")
		sleep(5)
		print("Home {}: Starting to send requests to Market !".format(self.homeNumber))
		while 1:
			self.decideWhatToDo()

			if self.budget<0:
				print("Home {}: Shit I'm broke!".format(self.homeNumber))
				self.sendMessage(1, 'Broke')
				break

			sleep(5)

	def decideWhatToDo(self):
		print("Home {}: My budget is {} dollars.".format(self.homeNumber,self.budget))
		self.energy=self.productionRate-self.consumptionRate
		if self.energy<0:
			self.buy()
		elif self.energy>0:
			self.sell()

	def sendMessage(self, index, message):
		self.messageQueueList[index].send(str(message).encode())
		print("Home{} sent: {}".format(self.homeNumber,message))


	def receiveMessage(self, index):
		x, t = self.messageQueueList[index].receive()
		message = x.decode()
		print("Home{} recieved: {}".format(self.homeNumber,message))
		if message != "Buy" or message != "Nothing":
			message = int(message)
		return message


	def buy(self):
		print("Home {}: What's the price? I wanna buy some energy.".format(self.homeNumber))
		self.sendMessage(1, 'Buy')
		price=self.receiveMessage(1)
		print("Home {}: It seems the price is {} dollars.".format(self.homeNumber,price))
		self.budget+=self.energy*price


	def sell(self):
		print("Home {}: What's the price? I wanna sell some energy.".format(self.homeNumber))
		self.sendMessage(1, 'Sell')
		price=self.receiveMessage(1)
		print("Home {}: It seems the price is {} dollars.".format(self.homeNumber,price))
		self.budget+=self.energy*price


class Market(Process):

	def __init__(self):
		super().__init__()
		self.price=20
		self.messageQueueList=[]
		self.messageQueueList.append(MessageQueue(1000,IPC_CREAT))
		print("The market's messageQueueList: {}".format(self.messageQueueList))
		self.mqExists=False

	def lookAtRequests(self):
		print("Look at request launched")
		while self.mqExists == False:
			sleep(1)
			print("Market: No MQ yet")
		print("Market: Found MQ")
		while 1:
			for x in range(1,len(self.messageQueueList)):
				print(x)
				print(self.messageQueueList[x])
				value=self.receiveMessage(x)
				if value != '':
					with ThreadPoolExecutor(max_workers = 3) as executor:
						print("demand received")
						executor.submit(self.handleMessage,value,x)

	def handleMessage(self,message,channel):
		if message=='Broke':
			print('Market: No more homes alive :(')

		elif message=='Buy':
			with mutex:
				print('Market: The price of energy is %s dollars.' %self.price)
				self.sendMessage(self.price,channel)
			print('Market: Energy is bought, increasing the price.')
			with mutex:
				self.price+=5

		elif message=='Sell':
			print('Market: The price of energy is %s dollars.' %self.price)
			with mutex:
				self.sendMessage(self.price,channel)
			print('Market: Energy is sold, decreasing the price.')
			with mutex:
				self.price-=2

	def dealWithNewHome(self):
			print("new MQ while loop")
			x = self.receiveMessage(0)

			print("Market received demand of new MQ")
			homeNb = int(x)
			print("Home",homeNb,"demands a MQ")
			self.messageQueueList.append(MessageQueue(homeNb,IPC_CREAT))
			print("Modified the messageQueueList")
			print(self.messageQueueList)
			self.mqExists = True
			print(self.mqExists)
			sleep(1)

	def run(self):
		print("Creation du thread newMQ")
		newHomeThread = Thread(target=self.dealWithNewHome ,args= ())
		newHomeThread.start()
		newHomeThread.join()
		print("Creation du thread requestLook")
		requestLook = Thread(target=self.lookAtRequests , args=())
		requestLook.start()
		print("Lancements termines ! ")
		print('Market: The price of energy is now %s dollars.' %self.price)
		sleep(10)

	def sendMessage(self, message, index):
		self.messageQueueList[index].send(str(message).encode())
		print("Market sent: {}".format(message))

	def receiveMessage(self, index):
		x, t = self.messageQueueList[index].receive()
		message = x.decode()
		print("Market recieved: {}".format(message))
		return message




if __name__=="__main__":

	market=Market()
	market.start()

	home1=Home(0,10)
	home1.start()
