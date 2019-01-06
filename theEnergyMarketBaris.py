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
		sleep(1)
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
		sleep(1)
		self.connectedToMarket=False
		while not self.connectedToMarket:
			message=self.receiveMessage(0)
			if message==self.homeNumber:
				self.messageQueueList.append(MessageQueue(self.homeNumber))
				self.connectedToMarket=True


		while self.connectedToMarket:
			self.buyOrSell()

			if self.budget<0:
				print("Home {}: Shit I'm broke!".format(self.homeNumber))
				self.sendMessage(1, 'Broke')
				break

			sleep(5)

	def buyOrSell(self):
		print("Home {}: My budget is {} dollars.".format(self.homeNumber,self.budget))
		self.energy=self.productionRate-self.consumptionRate
		if self.energy<0:
			self.buy()
		elif self.energy>0:
			self.sell()

	def sendMessage(self, index, message):
		self.messageQueueList[index].send(str(message).encode())
		print("Home{} sent: {}".format(self.homeNumber,message))
		sleep(5)


	def receiveMessage(self, index):
		message, t = self.messageQueueList[index].receive()
		value = message.decode()
		print("Home{} recieved: {}".format(self.homeNumber,value))
		value = int(value)
		return value


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


	# def handleMessage(self):



class Market(Process):

	def __init__(self):
		super().__init__()
		self.price=20
		self.messageQueueList=[]
		self.messageQueueList.append(MessageQueue(1000,IPC_CREAT))
		print("Market: My messageQueueList is {}",format(self.messageQueueList))

	def lookAtRequests(self):
		print("Market: Look at requests launched")
		while 1:
			for index in range(len(self.messageQueueList)):
				print("Market: Currently dealing with this: {}".format(self.messageQueueList[index]))
				message=self.receiveMessage(index)
				if message != '':
					with ThreadPoolExecutor(max_workers = 3) as executor:
						print("Market: ThreadPoolExecutor: demand received")
						executor.submit(self.handleMessage,message,index)
			sleep(1)

	def handleMessage(self,message,index):
		if message=='Broke':
			print('Market: No more homes alive :(')

		elif message=='Buy':
			with mutex:
				print('Market: The price of energy is %s dollars.' %self.price)
				self.sendMessage(self.price,index)
			print('Market: Energy is bought, increasing the price.')
			with mutex:
				self.price+=5

		elif message=='Sell':
			print('Market: The price of energy is %s dollars.' %self.price)
			with mutex:
				self.sendMessage(self.price,index)
			print('Market: Energy is sold, decreasing the price.')
			with mutex:
				self.price-=2

		else:
			self.dealWithNewHome(message)

	def dealWithNewHome(self, message):
			print("Market: New home!")
			self.sendMessage(message, 0)
			self.messageQueueList.append(MessageQueue(message,IPC_CREAT))
			print("Market: My messageQueueList is {}",format(self.messageQueueList))

	def run(self):
		print("Market: Creating requestsThread")
		requestsThread = Thread(target=self.lookAtRequests, args=())
		requestsThread.start()
		print('Market: The price of energy is now %s dollars.' %self.price)
		sleep(100)

	def sendMessage(self, message, index):
		self.messageQueueList[index].send(str(message).encode())
		print("Market sent: {}".format(message))
		sleep(5)

	def receiveMessage(self, index):
		message, t = self.messageQueueList[index].receive()
		value = message.decode()
		print("Market recieved: {}".format(value))
		return value




if __name__=="__main__":

	market=Market()
	market.start()

	home1=Home(0,10)
	home1.start()
