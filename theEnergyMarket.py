from multiprocessing import Process, Value
import sysv_ipc
import random
from time import sleep

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
			print("Home {}: My budget is {} dollars.".format(self.homeNumber,self.budget))
			self.energy=self.productionRate-self.consumptionRate

			if self.energy<0:
				self.buy()
			elif self.energy>0:
				self.sell()


			if self.budget<0:
				print("Home {}: Shit I'm broke!".format(self.homeNumber))
				self.sendMessageQueue('Broke')		#Send message queue to Market to let it know that a home has gone bankrupt.
				break
			else:
				self.sendMessageQueue('Nothing')


			sleep(5)

	def sendMessageQueue(self,n):
		self.mq.send(str(n).encode())

	def receiveMessageQueue(self):
		message, t = self.mq.receive()
		value = message.decode()
		value = int(value)
		return value


	def buy(self):
		print("Home {}: What's the price?".format(self.homeNumber))
		self.sendMessageQueue('Buy')					#Ask the price
		price=self.receiveMessageQueue()
		print("Home {}: It seems the price is {} dollars.".format(self.homeNumber,price))
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


			if value=='Broke':
				print('Market: No more homes alive :(')
				break

			if value=='Buy':
				print('Market: The price of energy is %s dollars.' %self.price)
				self.sendMessageQueue(self.price,1)
				print('Market: Energy is bought.')
				print("Market: Increasing the price")
				self.price+=5


			self.price-=1							#The price goes down over time if noone buys any energy.
			print('Market: The price of energy is now %s dollars.' %self.price)

			sleep(random.uniform(1,2))

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

	sleep(1)

	home1=Home(0,10)
	home1.start()


if __name__=="__main__":
	EnergyMarket()
