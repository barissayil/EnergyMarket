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


import numpy as np
import matplotlib.pyplot as plt


#Important: When the graphs appear close them and then press CTRL+Z on the terminal to safely stop the program.





class Home(Process):

	numberOfHomes=0

	def __init__(self, consumptionRate, productionRate, isGenerous):

		super().__init__()
		Home.numberOfHomes+=1
		self.budget=1000000
		self.consumptionRate=consumptionRate
		self.productionRate=productionRate
		self.day=1
		self.energy=0
		self.homeNumber=Home.numberOfHomes
		self.messageQueue=MessageQueue(self.homeNumber,IPC_CREAT)
		self.isGenerous=isGenerous
		

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
		message= str(self.homeNumber) + ' ' + str(amount) + ' ' + str(self.budget) + ' ' + message
		MessageQueue(100).send(str(message).encode())
		

	def receiveMessage(self):

		x, t = self.messageQueue.receive()
		message = x.decode()
		return message


	def buyEnergy(self):

		print("Home {}: What's the price? I wanna buy some energy.".format(self.homeNumber))
		self.sendMessage('Buy')
		price=int(self.receiveMessage())
		print("Home {}: Bought energy.".format(self.homeNumber))
		self.budget+=self.energy*price


	def sellEnergy(self):

		print("Home {}: What's the price? I wanna sell some energy.".format(self.homeNumber))
		self.sendMessage('Sell')
		price=int(self.receiveMessage())
		print("Home {}: Sold energy.".format(self.homeNumber))
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

	def __init__(self, numberOfHomes=5):

		super().__init__()
		self.numberOfHomes=numberOfHomes
		self.initialNumberOfHomes=numberOfHomes
		self.numberOfHomeThatAreDone=0
		self.numberOfHomeThatAreDoneLock=Lock()
		self.priceLock = Lock()
		self.fLock=Lock()
		self.aliveHomes=[True]*numberOfHomes
		self.dayHasStarted=False
		self.price=20000
		self.gamma=.9999  								# long-term attenuation coefficient for
		self.f=0										# internal factor (amount bought-amount sold)
		self.alpha=3									# modulating coefficient for factor for internal factors
		self.freeEnergy=0
		self.freeEnergyLimit=10
		self.day=1
		self.messageQueue=MessageQueue(100,IPC_CREAT)
		self.dayArray=np.array([self.day])
		self.priceArray=np.array([self.price])
		self.temperatureArray=np.array([])
		self.sunnyArray=np.array([])
		self.macronDays=[]		#Days when Macron increased the tax on energy.
		self.fusionDays=[]		#Days when there was a fusion breakthrough.
		self.budgetsOfHomes=[]
		for i in range(self.numberOfHomes):
			self.budgetsOfHomes.append([1000000])
		MessageQueue(101,IPC_CREAT) #for weather
		MessageQueue(102,IPC_CREAT) #for external



	def run(self):

		signal(SIGUSR1, self.handleSignals)
		signal(SIGUSR2, self.handleSignals)

		external=External()
		external.start()

		Thread(target=self.waitForMessages).start()
		Thread(target=self.manageTheDay).start()

		self.waitForGivenSecondsThenShowGraphs(20)	
		# self.showGraphsWhenAllHomesAreBroke()







	def showGraphsWhenAllHomesAreBroke(self):

		while self.numberOfHomes!=100:
			sleep(5)
			pass
		self.showGraphs()



	def waitForGivenSecondsThenShowGraphs(self, seconds):

		fiveSecondCounter=0
		isOver=False
		
		while not isOver:
			if fiveSecondCounter>=seconds/5:
				isOver=True
				self.showGraphs()
			sleep(5)
			fiveSecondCounter+=1
			pass



	def manageTheDay(self):

		while 1:
			self.startTheDay()
			self.goToNextDay()


	def startTheDay(self):

		for i in range(self.initialNumberOfHomes):
			self.budgetsOfHomes[i].append(0)

		self.waitForWeather()
		self.waitForExternal()
		self.dayHasStarted=True


	def waitForWeather(self):

		MessageQueue(101).receive()

		self.temperatureArray=np.append(self.temperatureArray,temperature.value)

		if sunny.value==1:
			self.sunnyArray=np.append(self.sunnyArray,'sunny')
		else:
			self.sunnyArray=np.append(self.sunnyArray,'cloudy')


	def waitForExternal(self):

		MessageQueue(102).receive()


	def updatePrice(self):

		with self.priceLock:
			self.price=int((self.gamma*self.price+self.alpha*self.f)*((20/temperature.value)**(1./10))*((sunny.value)**(1./1000)))	#SUNNY? DAMN NEGATIVE NALJSKLA
			self.priceArray=np.append(self.priceArray,self.price)
			with self.fLock:
				self.f=0
			if self.price<100:
				self.price=100
			print("Market: Updated the price. It is now {}.".format(self.price))


	def showGraphs(self):

		for i in range(self.initialNumberOfHomes):
			del self.budgetsOfHomes[i][-1]

		for i in range(self.initialNumberOfHomes):
			budgetArray=np.asarray(self.budgetsOfHomes[i])
			plt.plot(self.dayArray, budgetArray,label='Home {}'.format(i+1))
		plt.xlabel('Days')
		plt.ylabel('Budget')
		plt.title('The Budgets of Homes as Days Pass')
		plt.legend()



		fig, ax1 = plt.subplots()

		color = 'tab:blue'
		ax1.set_xlabel('Day')
		ax1.set_ylabel('Energy Price', color=color)
		ax1.plot(self.dayArray, self.priceArray, color=color)
		ax1.tick_params(axis='y', labelcolor=color)
		plt.title('The Price of Energy and Various Factors on the Latter as Days Pass')

		ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

		color = 'tab:red'
		ax2.set_ylabel('Temperature', color=color)  # we already handled the x-label with ax1
		ax2.plot(self.dayArray, self.temperatureArray, color=color, linestyle='--')
		ax2.tick_params(axis='y', labelcolor=color)

		ax2 = ax1.twinx()

		color = 'tab:green'
		ax2.plot(self.dayArray, self.sunnyArray,'gD')
		ax2.tick_params(axis='y', labelcolor=color)

		fig.tight_layout()  # otherwise the right y-label is slightly clipped

		text='Days when Macron increased the tax on energy: '
		for elem in self.macronDays:
			text+=str(elem)+' '
		text+='\nDays when there was a fusion breakthrough: '
		for elem in self.fusionDays:
			text+=str(elem)+' '

		plt.gcf().text(.02, .02, text, fontsize=10)
		plt.show()


	def handleSignals(self, sig, frame):

		oldPrice=self.price

		if sig == SIGUSR1:
			with self.priceLock:
				self.price=int(self.price*1.10)
				print("Market: Macron has increased the tax on energy! The energy price increased from {} to {}.".format(oldPrice,self.price))
				self.macronDays.append(self.day)

		elif sig == SIGUSR2:
			with self.priceLock:
				self.price=int(self.price/1.5)
				print("Market: INSA students made a breakthrough on nuclear fusion! The energy price decreased from {} to {}.".format(oldPrice,self.price))
				self.fusionDays.append(self.day)


	def goToNextDay(self):

		while self.numberOfHomeThatAreDone!=self.numberOfHomes:
			pass

		self.numberOfHomeThatAreDone=0
		self.day+=1
		self.dayArray=np.append(self.dayArray,self.day)
		self.dayHasStarted=False
		print('\nMarket: IT IS DAY {}!'.format(self.day))
		self.updatePrice()
		for i in range (1,len(self.aliveHomes)+1):						
			if self.aliveHomes[i-1]:
				self.sendMessage(i,'Go')

		MessageQueue(200).send('Go'.encode())
		MessageQueue(300).send('Go'.encode())


	def waitForMessages(self):

		with ThreadPoolExecutor(max_workers=4) as executor:
			while 1:
				message=self.receiveMessage()
				executor.submit(self.handleMessage, message)


	def handleMessage(self, message):

		while not self.dayHasStarted:
			pass 

		print('Market: Handling the message "{}".'.format(message))
			
		message=message.split()
		homeNumber=int(message[0])
		amount=int(message[1])
		budget=int(message[2])
		message=message[3]

		if budget<0:
			budget=0

		self.budgetsOfHomes[homeNumber-1][self.day]=budget

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


	def receiveMessage(self):

		x, t = self.messageQueue.receive()
		message = x.decode()
		return message



class External(Process):

	def __init__(self):

		super().__init__()
		MessageQueue(300,IPC_CREAT)
		self.day=1


	def run(self):

		self.marketPID=getppid()
		while 1:
			print('External: It is day {}.'.format(self.day))
			self.determineTheExternalFactors()
			MessageQueue(102).send('Done'.encode())
			MessageQueue(300).receive()
			self.day+=1


	def determineTheExternalFactors(self):

		if randint(1,100)<=5:
			kill(self.marketPID,SIGUSR1)
			print('External: Macron increased the tax on energy!')

		elif randint(1,100)<=1:
			kill(self.marketPID,SIGUSR2)
			print('External: Fusion breakthrough!')



class Weather(Process):

	def __init__(self):

		super().__init__()
		MessageQueue(200,IPC_CREAT)
		self.day=1
		self.numberOfConsecutiveCloudyDays=0
		

	def run(self):

		while 1:
			print('Weather: It is day {}.'.format(self.day))
			self.determineWeatherConditions()
			MessageQueue(101).send('Done'.encode())
			MessageQueue(200).receive()
			self.day+=1


	def determineWeatherConditions(self):

		
		if sunny.value==1:
			if randint(1,100)<=70:	#if yesterday was sunny, there's a 70% chance today is as well.
				sunny.value=1
				print("Weather: Today it's sunny :D!")
			else:
				sunny.value=10
				print("Weather: Today it's cloudy :(.")
				self.numberOfConsecutiveCloudyDays+=1
		else:
			if randint(1,100)<=98-2*self.numberOfConsecutiveCloudyDays: 	#if yesterday the beginning of the cloudy days, there's a 98% chance today is cloudy as well. with each consecutive clody day
																			#the chance for the next day to be cloudy decreases by 2%.
				sunny.value=10
				print("Weather: Today it's cloudy :(.")
				self.numberOfConsecutiveCloudyDays+=1
			else:
				sunny.value=1
				print("Weather: Today it's sunny :D!")

		temperature.value+=np.random.normal(scale=.1)
		print("Weather: Today it's {}°C.".format(temperature.value))




if __name__=="__main__":


	temperature=Value('d', 20)
	sunny=Value('i', 1)  					# 1: sunny, 10: cloudy
	
	weather=Weather()
	market=Market()							#by default there are 5 homes, if more or less homes is desired, put it as an argument, e.g., if you only want a single home write Market(1)
	home1=Home(10, 5, True)
	home2=Home(10, 20, True)
	home3=Home(10, 12, False)
	home4=Home(9, 2, True)
	home5=Home(2, 0, True)
	# home6=Home(15, 20, True)
	# home7=Home(10, 20, False)
	# home8=Home(20, 0, False)
	# home9=Home(2, 2, True)
	# home10=Home(5, 3, True)

	weather.start()
	market.start()
	home1.start()
	home2.start()
	home3.start()
	home4.start()
	home5.start()
	# home6.start()
	# home7.start()
	# home8.start()
	# home9.start()
	# home10.start()
