from multiprocessing import Process, Value, Lock
from sysv_ipc import MessageQueue, IPC_CREAT
from random import randint
from time import sleep
import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from sys import exit
from os import getpid, getppid, kill
from signal import signal, SIGUSR1, SIGUSR2





class Home(Process):

	numberOfHomes=0

	def __init__(self, consumptionRate, productionRate, isGenerous):
		super().__init__()
		Home.numberOfHomes+=1
		self.budget=10000000
		self.consumptionRate=consumptionRate
		self.productionRate=productionRate
		self.day=1
		self.energy=0
		self.homeNumber=Home.numberOfHomes
		self.messageQueue=MessageQueue(self.homeNumber,IPC_CREAT)
		self.isGenerous=isGenerous
		# print("Home{}: My messageQueue is {}".format(self.homeNumber, self.messageQueue))
		

	def run(self):

		while 1:
			print("Home {}: It is day {}. My budget is {} dollars.".format(self.homeNumber, self.day, self.budget))
			self.energy=self.productionRate-self.consumptionRate
			self.decideWhatToDo()
			if self.budget<0:
				print("Home {}: Shit I'm broke!".format(self.homeNumber))
				self.sendMessage('Broke')
				break
			self.finishCurrentDay()
			self.waitForNextDay()
			self.day+=1


	def finishCurrentDay(self):
		self.sendMessage('Done')

			
	def waitForNextDay(self):
		message=self.receiveMessage()


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
		# print("Home{} sent: {}".format(self.homeNumber,message))
		

	def receiveMessage(self):

		x, t = self.messageQueue.receive()
		message = x.decode()
		# print("Home{} recieved: {}".format(self.homeNumber, message))
		return message


	def buyEnergy(self):

		print("Home {}: What's the price? I wanna buy some energy.".format(self.homeNumber))
		self.sendMessage('Buy')
		price=int(self.receiveMessage())
		print("Home {}: It seems the price is {} dollars.".format(self.homeNumber,price))
		self.budget+=self.energy*price


	def sellEnergy(self):

		print("Home {}: What's the price? I wanna sell some energy.".format(self.homeNumber))
		self.sendMessage('Sell')
		price=int(self.receiveMessage())
		print("Home {}: It seems the price is {} dollars.".format(self.homeNumber,price))
		self.budget+=self.energy*price

	def getEnergy(self):

		print("Home {}: I wanna get some free energy.".format(self.homeNumber))
		self.sendMessage('Get')
		amount=int(self.receiveMessage())
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
		amount=int(self.receiveMessage())

		if amount>0:
			print("Home {}: Cool! I gave away {} free energy.".format(self.homeNumber, amount))
		elif amount==0:
			print("Home {}: Oh, no one wants my free energy. I'll have to sell it.".format(self.homeNumber))
			self.sellEnergy()




class Market(Process):

	def __init__(self, numberOfHomes):

		super().__init__()
		self.numberOfHomes=numberOfHomes
		self.numberOfHomeThatAreDone=0
		self.numberOfHomeThatAreDoneLock=Lock()
		self.priceLock = Lock()
		self.fLock=Lock()
		self.aliveHomes=[True]*numberOfHomes
		self.dayHasStarted=False
		self.price=20000
		self.gamma=.999999  # long-term attenuation coefficient for
		self.f=0		# internal factor (amount bought-amount sold)
		self.alpha=5	# modulating coefficient for factor for internal factors
		self.freeEnergy=0
		self.freeEnergyLimit=10
		self.day=1
		self.messageQueue=MessageQueue(100,IPC_CREAT)
		MessageQueue(101,IPC_CREAT) #for weather
		MessageQueue(102,IPC_CREAT) #for external
		# print("Market: My messageQueue is {}",format(self.messageQueue))



	def run(self):
		# print('Market: My PID is {}.'.format(getpid()))


		signal(SIGUSR1, self.handleSignals)
		signal(SIGUSR2, self.handleSignals)

		external=External()
		external.start()

		Thread(target=self.waitForMessages).start()
		Thread(target=self.manageTheDay).start()


		


	def manageTheDay(self):
		while 1:
			self.startTheDay()
			self.goToNextDay()



	def startTheDay(self):
		print('Market: Waiting to start the day.')
		self.waitForWeather()
		self.waitForExternal()
		print('Market: The day has started.')
		self.dayHasStarted=True


		
	def waitForWeather(self):
		print('Market: Waiting for weather.')
		MessageQueue(101).receive()
		print('Market: Weather is done.')

	def waitForExternal(self):
		print('Market: Waiting for external.')
		MessageQueue(102).receive()
		print('Market: External is done.')




	def updatePrice(self):
		with self.priceLock:
			self.price=int(self.gamma*self.price+self.alpha*self.f)
			with self.fLock:
				self.f=0
			if self.price<100:
				self.price=100
			print("Market: Updated the price. It is now {}.".format(self.price))

		
	def handleSignals(self, sig, frame):
		oldPrice=self.price
		if sig == SIGUSR1:
			with self.priceLock:
				self.price=int(self.price*1.3)
				print("Market: Signal from External received. Macron has increased the tax on energy! The energy price increased from {} to {}.".format(oldPrice,self.price))
		elif sig == SIGUSR2:
			with self.priceLock:
				self.price=int(self.price/2)
				print("Market: Signal from External received. INSA students found a way to perform efficient nuclear fusion! The energy price decreased from {} to {}.".format(oldPrice,self.price))




	def goToNextDay(self):

		print("numberOfHomeThatAreDone:{}, numberOfHomes:{}".format(self.numberOfHomeThatAreDone,self.numberOfHomes))

		while self.numberOfHomeThatAreDone!=self.numberOfHomes:
			pass

		print("numberOfHomeThatAreDone:{}, numberOfHomes:{}".format(self.numberOfHomeThatAreDone,self.numberOfHomes))

		self.numberOfHomeThatAreDone=0
		self.day+=1
		self.dayHasStarted=False
		print('\n\nMarket: IT IS DAY {}!'.format(self.day))
		self.updatePrice()
		for i in range (1,len(self.aliveHomes)+1):						
			if self.aliveHomes[i-1]:
				self.sendMessage(i,'Go')

		MessageQueue(200).send('Done'.encode())
		MessageQueue(300).send('Done'.encode())



	def waitForMessages(self):

		print('Market: Waiting for messages from homes.')

		with ThreadPoolExecutor(max_workers=3) as executor:
			while 1:
				message=self.receiveMessage()
				executor.submit(self.handleMessage, message)


	def handleMessage(self, message):

		print(self.dayHasStarted)

		while not self.dayHasStarted:
			pass 

		print(self.dayHasStarted)

		print('Market: Handling the message "{}".'.format(message))
			
		message=message.split()
		homeNumber=int(message[0])
		amount=int(message[1])
		message=message[2]

		if message=='Broke':
			print('Market: Oh no! Home{} went broke.'.format(homeNumber))
			self.aliveHomes[homeNumber-1]=False
			print(self.aliveHomes)
			self.numberOfHomes-=1 #lock
			print('Market: Henceforth there are {} homes.'.format(self.numberOfHomes))

			if self.numberOfHomes==0:
				self.numberOfHomes=100 #i would love to find out a way to make the program stop at this point

		elif message=='Buy':
			with self.priceLock:
				print('Market: The price of energy is {} dollars.'.format(self.price))
				self.sendMessage(homeNumber, self.price)
			print('Market: Demand is up, increasing the price.')


			with self.fLock:
				self.f+=1


		elif message=='Sell':
			with self.priceLock:
				print('Market: The price of energy is {} dollars.'.format(self.price))
				self.sendMessage(homeNumber, self.price)
			print('Market: Supply is up, decreasing the price.')


			with self.fLock:
				self.f-=1
			
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

		elif message=='Done':
			with self.numberOfHomeThatAreDoneLock:
				self.numberOfHomeThatAreDone+=1
				print('Market: Home{} is done. {} homes remain.'.format(homeNumber, self.numberOfHomes-self.numberOfHomeThatAreDone))

			





	def sendMessage(self, homeNumber, message):

		MessageQueue(homeNumber).send(str(message).encode())
		# print("Market sent: {}".format(message))


	def receiveMessage(self):

		x, t = self.messageQueue.receive()
		message = x.decode()
		# print("Market recieved: {}".format(message))
		return message



class External(Process):

	def __init__(self):
		super().__init__()
		MessageQueue(300,IPC_CREAT)
		self.day=1


	def run(self):
		self.marketPID=getppid()
		# print("External: Market's PID is {}.".format(self.marketPID))


		while 1:
			print('External: It is day {}.'.format(self.day))

			self.determineTheExternalFactors()

			# print('EXTERNAL: DONE')
			MessageQueue(102).send('Done'.encode())
			MessageQueue(300).receive()
			self.day+=1


	def determineTheExternalFactors(self):

		if randint(1,100)<=90:
			kill(self.marketPID,SIGUSR1)
			print('External: Macron!')

		if randint(1,100)<=5:
			kill(self.marketPID,SIGUSR2)
			print('External: Fusion!')



class Weather(Process):
	def __init__(self):
		super().__init__()
		MessageQueue(200,IPC_CREAT)
		self.day=1
		

	def run(self):
		while 1:
			print('Weather: It is day {}.'.format(self.day))

			self.determineWeatherConditions()

			# print('WEATHER: DONE')
			MessageQueue(101).send('Done'.encode())
			MessageQueue(200).receive()
			self.day+=1

	def determineWeatherConditions(self):
		sunny.value=randint(0,2)					#50% sunny 50% cloudy
		if sunny.value:
			print("Weather: The temperature is {}°C and it is sunny.".format(temperature.value))
		else:
			print("Weather: The temperature is {}°C and it is cloudy.".format(temperature.value))





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

	clear=MessageQueue(101,IPC_CREAT)
	clear.remove()

	clear=MessageQueue(102,IPC_CREAT)
	clear.remove()

	clear=MessageQueue(200,IPC_CREAT)
	clear.remove()

	clear=MessageQueue(300,IPC_CREAT)
	clear.remove()


if __name__=="__main__":


	clean()



	temperature=Value('d', 12.5)
	sunny=Value('i', 1)  					# 1: sunny, 0: cloudy



	weather=Weather()

	market=Market(3)

	home1=Home(10, 0, True)
	home2=Home(11, 5, True)
	home3=Home(10, 3, False)
	# home4=Home(9, 2, True)






	weather.start()

	market.start()
	
	home1.start()
	home2.start()
	home3.start()
	# home4.start()
