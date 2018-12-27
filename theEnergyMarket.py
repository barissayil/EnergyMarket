from multiprocessing import Process, Value
import sysv_ipc
import random
import time

class Home(Process):



	def __init__(self,productionRate, consumptionRate):
		super().__init__()
		numberOfHomes.value+=1
		self.budget=100
		self.productionRate=productionRate
		self.consumptionRate=consumptionRate
		self.energy=0
		self.homeNumber=numberOfHomes.value
		self.mq = sysv_ipc.MessageQueue(self.homeNumber, sysv_ipc.IPC_CREAT)



	def run(self):
		while 1:
			print("I'm home number {} and my budget is {} dollars.".format(self.homeNumber,self.budget))
			time.sleep(random.uniform(1,2))
			self.energy=self.productionRate-self.consumptionRate
			if self.energy<0:
				self.buy()
			if self.budget<0:
				print("Shit I'm broke!")
				self.mq.send(str(0).encode())
				break
			else:
				self.mq.send(str(1).encode())


	def buy(self):
		self.budget+=self.energy*price.value
		price.value+=.1							#The price goes up everytime someone buys energy.



class Market(Process):

	def __init__(self):
		super().__init__()

	def run(self):
		while 1:

			if numberOfHomes.value==1:
				mq = sysv_ipc.MessageQueue(numberOfHomes.value)


			message, t = mq.receive()
			value = message.decode()
			value = int(value)


			if value==0:
				print('No more homes alive :(')
				break



			time.sleep(random.uniform(1,2))
			price.value-=.2							#The price goes down over time if noone buys any energy.
			print('The price of energy is %s dollars.' %price.value)







def EnergyMarket():

	market=Market()
	home1=Home(0,10)

	market.start()
	home1.start()


price=Value('d',2.0)
numberOfHomes=Value('i',0)
EnergyMarket()