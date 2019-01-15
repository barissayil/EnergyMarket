from multiprocessing import Process, Value, Lock, Array
from sysv_ipc import MessageQueue, IPC_CREAT
import random
from time import sleep
import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, Semaphore






class Home(Process):

	numberOfHomes=0

	def __init__(self, consumptionRate, productionRate, isGenerous):
		super().__init__()
		Home.numberOfHomes+=1
		self.budget=1000
		self.consumptionRate=consumptionRate
		self.productionRate=productionRate
		self.energy=0
		self.homeNumber=Home.numberOfHomes
		self.messageQueue=MessageQueue(self.homeNumber,IPC_CREAT)
		self.isGenerous=isGenerous
		print("Home{}: My messageQueue is {}".format(self.homeNumber, self.messageQueue))


	def run(self):

		while 1:
			print("Home {}: My budget is {} dollars.".format(self.homeNumber,self.budget))
			self.energy=self.productionRate-self.consumptionRate
			self.decideWhatToDo()
			if self.budget<0:
				print("Home {}: Shit I'm broke!".format(self.homeNumber))
				self.sendMessage('Broke')
				break
			sleep(5)


	def decideWhatToDo(self):

		if self.energy<0:
			self.getEnergy()
			if self.energy<0:
				self.buyEnergy()
		elif self.energy>0:
			if self.isGenerous:
				self.giveEnergy()
			else:
				self.sellEnergy()


	def sendMessage(self, message):

		amount=abs(self.energy)
		message= str(self.homeNumber) + " " + str(amount) + " " + message
		MessageQueue(100).send(str(message).encode())
		print("Home{} sent: {}".format(self.homeNumber,message))


	def receiveMessage(self):

		x, t = self.messageQueue.receive()
		message = x.decode()
		print("Home{} recieved: {}".format(self.homeNumber, message))
		message = int(message)
		return message


	def buyEnergy(self):

		print("Home {}: What's the price? I wanna buy some energy.".format(self.homeNumber))
		self.sendMessage('Buy')
		price=self.receiveMessage()
		print("Home {}: It seems the price is {} dollars.".format(self.homeNumber,price))
		self.budget+=self.energy*price


	def sellEnergy(self):

		print("Home {}: What's the price? I wanna sell some energy.".format(self.homeNumber))
		self.sendMessage('Sell')
		price=self.receiveMessage()
		print("Home {}: It seems the price is {} dollars.".format(self.homeNumber,price))
		self.budget+=self.energy*price

	def getEnergy(self):

		print("Home {}: I wanna get some free energy.".format(self.homeNumber))
		self.sendMessage('Get')
		amount=self.receiveMessage()
		if amount==0:
			print("Home {}: Dammit there's no free energy, I have to buy some.".format(self.homeNumber))
			return
		else:
			print("Home {}: Nice! I got {} free energy.".format(self.homeNumber, amount))
		self.energy+=amount
		if self.energy==0:
			print("Home {}: Perfect! I have all my energy needs covered.".format(self.homeNumber))
		else:
			print("Home {}: Oh, it's not enough. I still have to buy some energy.".format(self.homeNumber))



	def giveEnergy(self):

		print("Home {}: I'm giving away some free energy.".format(self.homeNumber))
		self.sendMessage('Give')
		amount=self.receiveMessage()

		if amount>0:
			print("Home {}: Cool! I gave away {} free energy.".format(self.homeNumber, amount))
		elif amount==0:
			print("Home {}: Oh, no one wants my free energy. I'll have to sell it.".format(self.homeNumber))
			self.sellEnergy()



class Market(Process):

	def __init__(self):

		super().__init__()
		self.price=20
		self.freeEnergy=0
		self.freeEnergyLimit=10
		self.messageQueue=MessageQueue(100,IPC_CREAT)
		print("Market: My messageQueue is {}",format(self.messageQueue))

	def run(self):


		Thread(target=self.updatePrice).start()


		with ThreadPoolExecutor(max_workers=3) as executor:
			executor.submit(self.handleMessages)





	def handleMessages(self):

		while 1:
			message=self.receiveMessage()
			message=message.split()
			homeNumber=int(message[0])
			amount=int(message[1])
			message=message[2]

			if message=='Broke':
				print('Market: Oh no! Home{} went broke.'.format(homeNumber))

			elif message=='Buy':
				with priceLock:
					print('Market: The price of energy is {} dollars.'.format(self.price))
					self.sendMessage(homeNumber, self.price)
				print('Market: Demand is up, increasing the price.')
				with priceLock:
					self.price+=5

			elif message=='Sell':
				with priceLock:
					print('Market: The price of energy is {} dollars.'.format(self.price))
					self.sendMessage(homeNumber, self.price)
				print('Market: Supply is up, decreasing the price.')
				with priceLock:
					self.price-=1

			elif message=='Give':

				print('Market: WOW! Home{} is giving away {} units of energy for free!'.format(homeNumber, amount))


				if self.freeEnergy>=self.freeEnergyLimit:
					print('Market: Woah slow down! I have way too much free energy.')
					self.sendMessage(homeNumber, 0)

				else:
					self.freeEnergy+=amount
					self.sendMessage(homeNumber, amount)

				print('Market: Currently {} units of free energy available'.format(self.freeEnergy))



			elif message=='Get':
				print('Market: LOL! Home{} wants {} units of energy for free!'.format(homeNumber, amount))
				if self.freeEnergy>=amount:
					self.sendMessage(homeNumber, amount)
					self.freeEnergy-=amount
					print('Market: Currently {} units of free energy available'.format(self.freeEnergy))
				else:
					self.sendMessage(homeNumber, self.freeEnergy)
					self.freeEnergy-=0
					print('Market: Currently no free energy is available'.format(self.freeEnergy))




	def updatePrice(self):
		while 1:
			with priceLock:
				self.price=int(self.price-(temperature.value/10-sunny.value)/10)			#If it's hot and sunny then energy is cheap and if it's dark and cold it's expensive.
				print("Market: Updated the price. It is now {}.".format(self.price))
			sleep(10)


	def sendMessage(self, homeNumber, message):

		MessageQueue(homeNumber).send(str(message).encode())
		print("Market sent: {}".format(message))


	def receiveMessage(self):

		x, t = self.messageQueue.receive()
		message = x.decode()
		print("Market recieved: {}".format(message))
		return message






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

			sleep(1)





def clean():									#To clean the message queues.
	clear=MessageQueue(100,IPC_CREAT)
	clear.remove()

	clear=MessageQueue(1,IPC_CREAT)
	clear.remove()

	clear=MessageQueue(2,IPC_CREAT)
	clear.remove()

	clear=MessageQueue(3,IPC_CREAT)
	clear.remove()

	clear=MessageQueue(4,IPC_CREAT)
	clear.remove()

	clear=MessageQueue(5,IPC_CREAT)
	clear.remove()


if __name__=="__main__":


	clean()



	temperature=Value('d', 12.5)
	sunny=Value('i', 1)  					# 1: sunny, 0: cloudy



	# weather=Weather()						#Weather is optional at the moment.
	# weather.start()




	priceLock = Lock()


	market=Market()
	market.start()


	home1=Home(10, 0, True)
	home1.start()


	home2=Home(5, 13, True)
	home2.start()


	# home3=Home(5, 15, False)
	# home3.start()


	# home4=Home(9, 2, True)
	# home4.start()


	# home4=Home(5, 0, True)
	# home4.start()
