from multiprocessing import Process, Value
import sysv_ipc
import random
import time

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
		self.mq = sysv_ipc.MessageQueue(127)

	def run(self):
		while 1:
			print("I'm home number {} and my budget is {} dollars.".format(self.homeNumber,self.budget))
			self.energy=self.productionRate-self.consumptionRate

			if self.energy<0:
				self.buy()
			elif self.energy>0:
				self.sell()


			if self.budget<0:
				print("Shit I'm broke!")
				self.sendMessageQueue(-1)		#Send message queue to Market to let it know that a home has gone bankrupt.
				break
			else:
				self.sendMessageQueue(1)


			time.sleep(5)

	def sendMessageQueue(self,n):
		self.mq.send(str(n).encode())

	def receiveMessageQueue(self):
		message, t = self.mq.receive()
		value = message.decode()
		value = int(value)
		return value


	def buy(self):
		print("Home : Asking the Market price")
		self.sendMessageQueue('Buy')					#Ask the price
		price=self.receiveMessageQueue()
		print("|||||Price is {} dollars.".format(price))
		self.budget+=self.energy*price
		# market.price+=.1							#The price goes up everytime someone buys energy.


	# def sell(self):
	# 	self.budget+=self.energy*market.price
	# 	market.price-=.1							#The price goes down everytime someone sells energy.



class Market(Process):

	def __init__(self):
		super().__init__()
		self.price=20
		self.mq = sysv_ipc.MessageQueue(127,sysv_ipc.IPC_CREAT)

	def run(self):
		while 1:

			value=self.receiveMessageQueue()


			if value==-1:
				print('Market :No more homes alive :(')
				break

			if value=='Buy':
				print("Demand of market price")
				print('Market : The price of energy is %s dollars.' %self.price)
				self.sendMessageQueue(self.price,1)
				print('Market :Energy is bought.')
				print("Market :Refreshing the price")
				self.price+=1




			# self.price-=.2							#The price goes down over time if noone buys any energy.
			print('The price of energy is now %s dollars.' %self.price)


			time.sleep(random.uniform(1,2))

	def sendMessageQueue(self, n, h):
		self.mq.send(str(n).encode())

	def receiveMessageQueue(self):
		message, t = self.mq.receive()
		value = message.decode()
		print(value)
		return value





def EnergyMarket():

	market=Market()
	market.start()

	time.sleep(1)

	home1=Home(0,10)
	home1.start()


EnergyMarket()
