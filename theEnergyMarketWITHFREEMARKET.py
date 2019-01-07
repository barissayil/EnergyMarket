from multiprocessing import Process, Value, Lock, Array
from sysv_ipc import MessageQueue, IPC_CREAT
import random
from time import sleep
import datetime
from concurrent.futures import ThreadPoolExecutor
import sys
from threading import Thread, Semaphore

class Home(Process):

	numberOfHomes=0

	def __init__(self, productionRate, consumptionRate, Generous):
		sleep(1)
		super().__init__()
		self.generous= Generous
		Home.numberOfHomes+=1
		self.budget=1000
		self.productionRate=productionRate
		self.consumptionRate=consumptionRate
		self.energy=0
		self.homeNumber=Home.numberOfHomes
		self.name="Home{}".format(self.homeNumber)
		self.messageQueue=MessageQueue(self.homeNumber,IPC_CREAT)
		self.marketMessageQueue=MessageQueue(100)
		self.freeMessageQueue=MessageQueue(200)
		print("{}'s messageQueue: {}".format(self.name, self.messageQueue))

	def run(self):

		while 1:

			self.decideWhatToDo()
			sleep(1)

			if self.budget<0:
				print("Home {}: Shit I'm broke!".format(self.homeNumber))
				self.sendMessage('Broke')
				break

	def decideWhatToDo(self):
		print("Home {}: My budget is {} dollars.".format(self.homeNumber,self.budget))
		self.energy=self.productionRate-self.consumptionRate
		if self.energy<0:
			self.buy("Free")
			self.buy("Pay")
		elif self.energy>0:
			self.sell("Free")
			self.sell("Pay")

	def sendMessage(self, message, market):

		if market=='Pay':
			message= str(self.homeNumber) + " " + message
			self.marketMessageQueue.send(str(message).encode())
			print("Home{} sent: {}".format(self.homeNumber,message))

		elif market == "Free":
			self.freeMessageQueue.send(str(message).encode())
			print("Home{} sent: {}".format(self.homeNumber,message))

	def receiveMessage(self,Market):
		if Market == "Pay":
			x, t = self.messageQueue.receive()
			message = x.decode()
			print("Home{} recieved: {} price".format(self.homeNumber, message))
			message = int(message)

		elif Market == "Free":
			x, t = self.freeMessageQueue.receive()
			message = x.decode()
			print("Home{} recieved: {} of free energy".format(self.homeNumber, message))
			message = int(message)
		return message

	def buy(self,Method):
		if Method == "Pay":
			print("Home {}: What's the price? I wanna buy some energy.".format(self.homeNumber))
			self.sendMessage('Buy',Method)
			price=self.receiveMessage(Method)
			print("Home {}: It seems the price is {} dollars.".format(self.homeNumber,price))
			self.budget+=self.energy*price

		elif Method == "Free":
			amount= self.receiveMessage(Method)
			self.energy= self.energy - int(amount)

	def sell(self, Method):
		if Method == "Pay":
			print("Home {}: What's the price? I wanna sell some energy.".format(self.homeNumber))
			self.sendMessage('Sell',Method)
			price=self.receiveMessage(Method)
			print("Home {}: It seems the price is {} dollars.".format(self.homeNumber,price))
			self.budget+=self.energy*price
		elif Method == "Free":
			print("I gave free energy "+str(self.energy)+" units")
			self.sendMessage(self.energy,"Free")

	# def handleMessage(self):
class Market(Process):

	def __init__(self):
		super().__init__()
		self.price=20
		self.messageQueue=MessageQueue(100,IPC_CREAT)
		print("Market: My messageQueue is {}",format(self.messageQueue))

	def lookAtRequests(self):
		print("Market: Look at requests launched")
		while 1:
			print("Market: Currently dealing with this: {}".format(self.messageQueue))
			message=self.receiveMessage()
			self.handleMessage(message)

	def handleMessage(self,message):

		message=message.split()
		homeNumber=int(message[0])
		message=message[1]

		if message=='Broke':
			print('Market: No more homes alive :(')

		elif message=='Buy':
			with priceLock:
				print('Market: The price of energy is {} dollars.'.format(self.price))
				self.sendMessage(homeNumber, self.price)
			print('Market: Energy is bought, increasing the price.')
			with priceLock:
				self.price+=5

		elif message=='Sell':
			print('Market: The price of energy is {} dollars.'.format(self.price))
			with priceLock:
				self.sendMessage(homeNumber, self.price)
			print('Market: Energy is sold, decreasing the price.')
			with priceLock:
				self.price-=2

	def run(self):
		print("Market: Creating requestsThread")
		self.lookAtRequests()
		print('Market: The price of energy is now %s dollars.' %self.price)


	def sendMessage(self, homeNumber, message):
		MessageQueue(homeNumber).send(str(message).encode())
		print("Market sent: {}".format(message))

	def receiveMessage(self):
		x, t = self.messageQueue.receive()
		message = x.decode()
		print("Market recieved: {}".format(message))
		return message

def cleaning():			#To clean the message queues.
	clear=MessageQueue(100,IPC_CREAT)
	clear.remove()

	clear=MessageQueue(1,IPC_CREAT)
	clear.remove()

	clear=MessageQueue(2,IPC_CREAT)
	clear.remove()


if __name__=="__main__":

	cleaning()
	priceLock = Lock()

	market=Market()
	market.start()

	MessageQueue(200,IPC_CREAT)

	home1=Home(0,10,True)
	home1.start()

	home2=Home(10,8,True)
	home2.start()
