from multiprocessing import Process, Value, Lock
from sysv_ipc import MessageQueue, IPC_CREAT
from random import randint
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from sys import exit
from os import getpid, getppid, kill
from signal import signal, SIGUSR1, SIGUSR2
import numpy as np
import matplotlib.pyplot as plt


#Important: When the graphs appear close them and then press CTRL+Z on the terminal to safely stop the program.





class Home(Process):

	numberOfHomes=0		#A class variable that allows us to keep track of the number of homes during their initialization.

	def __init__(self, consumptionRate, productionRate, isGenerous):

		super().__init__()											#Home is a subclass of Process so we need to call Process' costructor.

		Home.numberOfHomes+=1										#Each time a new homes is instantiated, it's incremented.

		self.budget=1000000											#All homes start with this initial budget. A zero can be removed to finish the simulation 
																	#quicker (in case all the homes consume more than they produce).
		self.consumptionRate=consumptionRate
		
		self.productionRate=productionRate

		self.day=1													#Each home records its current day so that in the terminal we see that they're all on the same day.

		self.energy=0												#All homes start with 0 energy.

		self.homeNumber=Home.numberOfHomes 							#Each home has a unique number.

		self.messageQueue=MessageQueue(self.homeNumber,IPC_CREAT)	#Each home has a unique message queue that is uses to receive messages from Market.

		self.isGenerous=isGenerous									#If a home is generous, it'll try to give its energy away for free at first and only sell if it can't. 
																	#If not generous, it'll directly sell.
		

	def run(self):

		while 1:
			print("Home {}: It is day {}. My budget is {} dollars.".format(self.homeNumber, self.day, self.budget))

			self.energy=self.productionRate-self.consumptionRate		#Homes calculate their energy for the given day.

			self.decideWhatToDo()										#According to whether they have a surplus or deficit of energy and whether or not they are generous, the homes decide on what to do.

			if self.budget<0:											#If their budget goes below zero, they are broke and they stop existing as a process.
				print("Home {}: Shit I'm broke!".format(self.homeNumber))
				self.sendMessage('Broke')
				break
			self.finishCurrentDay()										#When the current they is over they let Market know.

			self.waitForNextDay()										#They wait for Market to tell them when the next day arrives.

			self.day+=1



	def finishCurrentDay(self):	#The home notifies Market that his day is done.

		self.sendMessage('Done')

			
	def waitForNextDay(self):	#The home just waits until it receives a message from Market.

		message=self.receiveMessage()			


	def decideWhatToDo(self):	#The determines what it needs to do. If it needs energy, it'll first try to get it for free. If he can't get enough, it'll buy the remainder.
								#If it has too much energy, if the home is not generous, it'll sell it. If it is generous, first it'll try to give away all of it and only sell what it can't give away.
		
		if self.energy<0:
			self.getEnergy()
			if self.energy<0:
				self.buyEnergy()
		elif self.energy>0:
			if self.isGenerous:
				self.giveEnergy()
				if self.energy>0:
					self.sellEnergy()
			else:
				self.sellEnergy()


	def sendMessage(self, message):	#Each time a home sends a message, it includes its home number, the amount of energy (sell or buy), its current budget, and what it wants to do.

		amount=abs(self.energy)
		message= str(self.homeNumber) + ' ' + str(amount) + ' ' + str(self.budget) + ' ' + message
		MessageQueue(100).send(str(message).encode())
		

	def receiveMessage(self):

		x, t = self.messageQueue.receive()	#Since receive() is blocking, the home waits here until Market sends it a message.
		message = x.decode()
		return message


	def buyEnergy(self):	#If the home decides to buy energy, it sends a message to Market and then waits for Market to tell it the 
							#current price. Then it updates it budget according to the amounf of energy it bought, which equals its energy deficit.			

		print("Home {}: What's the price? I wanna buy some energy.".format(self.homeNumber))
		self.sendMessage('Buy')
		price=int(self.receiveMessage())
		print("Home {}: Bought energy.".format(self.homeNumber))
		self.budget+=self.energy*price


	def sellEnergy(self):	#If the home decides to sell energy, it sends a message to Market and then waits for Market to tell it the 
							#current price. Then it updates it budget according to the amounf of energy it sold, which equals its energy surplus.

		print("Home {}: What's the price? I wanna sell some energy.".format(self.homeNumber))
		self.sendMessage('Sell')
		price=int(self.receiveMessage())
		print("Home {}: Sold energy.".format(self.homeNumber))
		self.budget+=self.energy*price


	def getEnergy(self):	#If the home decides to get free energy, it sends a message to Market and then waits for Market to tell it the 
							#amount of free energy it was allowed to obtain. There are 3 cases. First, it received no energy, in which case it will have to buy all the energy it needs.
							#Second, it received some but not enough energy, in which case it will have to buy the remainder. Third, it received all the energy it needed, in which case the homes is happy.

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


	def giveEnergy(self):	#If the home decides to give away free energy, it sends a message to Market and then waits for Market to tell it the 
							#amount of free energy it was allowed to give away. There are two cases. First, it was allowed to give away some energy. In this case the home will sell the remaining
							#surplus of energy, if any. Second, it couldn't give away any energy at all and will need to sell all of it.

		print("Home {}: I'm giving away some free energy.".format(self.homeNumber))
		self.sendMessage('Give')
		amount=int(self.receiveMessage())
		if amount>0:
			print("Home {}: Cool! I gave away {} free energy.".format(self.homeNumber, amount))
		elif amount==0:
			print("Home {}: Oh, no one wants my free energy. I'll have to sell it.".format(self.homeNumber))




class Market(Process):

	def __init__(self, numberOfHomes=5):

		super().__init__()								#Market is a subclass of Process so we need to call Process' costructor.

		self.numberOfHomes=numberOfHomes 				#The market needs to know the number of homes.

		self.initialNumberOfHomes=numberOfHomes 		#This was needed when I was doing the visualization because the one just above changes if some homes go broke.

		self.price=20000								#The price of energy.

		self.priceLock = Lock()							#Since market is multi-threaded, the variable just above needs to be kept safe from the race conditions.

		self.numberOfHomeThatAreDone=0					#The market increments it when it receives the 'Done' message from a home.

		self.numberOfHomeThatAreDoneLock=Lock()			#Same as the previous lock.

		self.aliveHomes=[True]*numberOfHomes 			#This list is modified each time a home goes broke. It is then used to determine for which homes the market should wait.

		self.dayHasStarted=False						#The days actually don't start until Weather and External are done. Only then this becomes true. 
														#When it's false, Market doesn't even handle the messages it receives from homes and waits for it to be true.

		self.gamma=.9999  								#The long-term attenuation coefficient for the price.

		self.f=0										#The internal factor (number of homes buying-selling).

		self.fLock=Lock()								#Some as other locks.

		self.alpha=1									#The modulating coefficient for factor for internal factors.

		self.freeEnergy=0								#This is the energy that the generous homes with energy surplusses give away.

		self.freeEnergyLimit=10							#This is the limit on the latter. If it is attained, energy cannot ve given away and even the generous homes will have to sell their energy surplus.

		self.day=1										#Market records its current day so that in the terminal we see that it is the same as other processes.

		self.messageQueue=MessageQueue(100,IPC_CREAT)	#This is the message queue of the market. All homes send their messages here.

		self.dayArray=np.array([self.day])				#A numpy array for storing all the days staring from 1. Used to produce graphs at the end of the simulation.

		self.priceArray=np.array([self.price])			#Same but for the energy price. The market records it each day and puts its value here.

		self.temperatureArray=np.array([])				#Same but for the temperature.

		self.sunnyArray=np.array([])					#Same, if a day is sunny then market appends 'sunny' to it, if cloudy then 'cloudy'.

		self.macronDays=[]								#Days when Macron increased the tax on energy. It is used to generate a text at the bottom of the graph.

		self.fusionDays=[]								#Days when there was a fusion breakthrough. It is used to generate a text at the bottom of the graph.

		self.budgetsOfHomes=[]							#List of budgets of the homes in each day. Later will be converted to numpy arrays and then used to produce a single graph with all the budgets of all the homes.

		for i in range(self.numberOfHomes):
			self.budgetsOfHomes.append([1000000])		#The method of recording of the budgets of the homes isn't perfect so to compensate the initial value is manually appended.

		MessageQueue(101,IPC_CREAT) 					#Not used for IPC but only for synchronization with Weather.

		MessageQueue(102,IPC_CREAT) 					#Not used for IPC but only for synchronization with External.



	def run(self):

		signal(SIGUSR1, self.handleSignals)				#We define custom handlers to be executed when a SIGUSR1 and SIGUSR2 signals are received.
		signal(SIGUSR2, self.handleSignals)

		external=External()								#External is a child-process of Market.
		external.start()								#We start External.

		Thread(target=self.waitForMessages).start()		#Market waits for messages from homes in a separate thread.
		Thread(target=self.manageTheDay).start()		#This was supposed to be in the main thread but when Market received signals the program crashed. Like this the main thread is left empty and doesn't crush. (But don't know why.)


		#Two choices for the visualization. Make sure not to choose the second one if even a single home produces more energy then they consume for obvious reasons.
		self.waitForGivenSecondsThenShowGraphs(100)			#Between 20 and 200 seconds is recommended.
		# self.showGraphsWhenAllHomesAreBroke()







	def showGraphsWhenAllHomesAreBroke(self):		#Use it only when all homes have energy deficits.

		while self.numberOfHomes!=100:				#When all homes are bankrupt self.numberOfHomes is set to 100 so that everything stops. So this makes the function wait until all the homes go bankrupt.
			sleep(5)								#Without this the program becomes very slow since it checks the above condition as much as it can it the main thread.
			pass
		self.showGraphs()



	def waitForGivenSecondsThenShowGraphs(self, seconds):	#The best function is this one. Waiting 100 seconds is quite sufficient and on my computer is able to simulate more than 200 days (with 5 homes).

		fiveSecondCounter=0
		isOver=False
		
		while not isOver:
			if fiveSecondCounter>=seconds/5:
				isOver=True
				self.showGraphs()
			sleep(5)
			fiveSecondCounter+=1
			pass



	def manageTheDay(self):	#Eveything that happens in a given day except the IPC with homes.

		while 1:
			self.startTheDay()
			# sleep(5)						#Optional. Can be used to make the simulation slower. However, don't try to see the graphs.
			self.goToNextDay()


	def startTheDay(self):	#Each day Market waits for Weather and External to determine the conditions and only then it starts the day.

		for i in range(self.initialNumberOfHomes):
			self.budgetsOfHomes[i].append(0)	#At the start of each day 0 is appended to each sublist of budgetsOfHomes. This way if a given home is bankrupt its budget is correctly inputed.

		self.waitForWeather()
		self.waitForExternal()
		self.dayHasStarted=True 	


	def waitForWeather(self):	#Simply waits for Weather to finish the day.

		MessageQueue(101).receive()

		self.temperatureArray=np.append(self.temperatureArray,temperature.value)	#Records the current day's temperature.

		if sunny.value==1:															#Records the current day's weather.
			self.sunnyArray=np.append(self.sunnyArray,'sunny')
		else:
			self.sunnyArray=np.append(self.sunnyArray,'cloudy')


	def waitForExternal(self):	#Simply waits for External to finish the day.

		MessageQueue(102).receive()


	def updatePrice(self):		#Updates the price at the end of the day according to number of homes buying vs selling, temperature, and weather.

		with self.priceLock:
			self.price=int((self.gamma*self.price+self.alpha*self.f)*((20/temperature.value)**(1./100))*((sunny.value)**(1./10000)))
			self.priceArray=np.append(self.priceArray,self.price)	#Records the current day's energy price.
			with self.fLock:
				self.f=0
			if self.price<100:	#This is only true if we have modified the parameters too much. Normally price never decreases this much. This is in case it does so we at least set it back to 100.
				self.price=100
			print("Market: Updated the price. It is now {}.".format(self.price))


	def showGraphs(self):	#Uses matplotlib.plotly to produce two graphs. One has the energy prices for all days as well as temperature, weather, and external events. 
							#The other has all the homes' budgets.

		for i in range(self.initialNumberOfHomes):	#The homes send one last message even when Market stops so we delete that in order to make arrays for day and budgets the same size.
			del self.budgetsOfHomes[i][-1]

		for i in range(self.initialNumberOfHomes):	#Plots the budget for each home.
			budgetArray=np.asarray(self.budgetsOfHomes[i])	#Numpy'y asarray function converts the list to an array so that we can plot it.
			plt.plot(self.dayArray, budgetArray,label='Home {}'.format(i+1))
		plt.xlabel('Days')
		plt.ylabel('Budget')
		plt.title('The Budgets of Homes as Days Pass')
		plt.legend()



		fig, ax1 = plt.subplots()	#For the second graph, teh scales for prize and temperature are vastly different so we need to use different scales for the y-axes.

		color = 'tab:blue'
		ax1.set_xlabel('Day')
		ax1.set_ylabel('Energy Price', color=color)
		ax1.plot(self.dayArray, self.priceArray, color=color)
		ax1.tick_params(axis='y', labelcolor=color)
		plt.title('The Price of Energy and Various Factors on the Latter as Days Pass')

		ax2 = ax1.twinx()  # Instantiate a second axes that shares the same x-axis.

		color = 'tab:red'
		ax2.set_ylabel('Temperature', color=color)  # We already handled the x-label with ax1.
		ax2.plot(self.dayArray, self.temperatureArray, color=color, linestyle='--')
		ax2.tick_params(axis='y', labelcolor=color)

		ax2 = ax1.twinx()

		color = 'tab:green'
		ax2.plot(self.dayArray, self.sunnyArray,'gD')
		ax2.tick_params(axis='y', labelcolor=color)

		fig.tight_layout()  # Otherwise the right y-label is slightly clipped.

		text='Days when Macron increased the tax on energy: '
		for elem in self.macronDays:
			text+=str(elem)+' '
		text+='\nDays when there was a fusion breakthrough: '
		for elem in self.fusionDays:
			text+=str(elem)+' '

		plt.gcf().text(.02, .02, text, fontsize=10)	#Puts the days when events occurred on the graph.
		plt.show()		#Shows the graphs.


	def handleSignals(self, sig, frame):	#Handles signals coming from External which indicate external events occurring. The first one means Macron increased the energy tax so 
											#the energy prices goes up 10% (can be changed below). The second one means some nuclear fusion breakthrough so the energy price naturally decreases a lot.

		oldPrice=self.price

		if sig == SIGUSR1:
			with self.priceLock:
				self.price=int(self.price*1.10)
				print("Market: Macron has increased the tax on energy! The energy price increased from {} to {}.".format(oldPrice,self.price))
				self.macronDays.append(self.day)	#Records the days when there was a tax increase.

		elif sig == SIGUSR2:
			with self.priceLock:
				self.price=int(self.price/1.5)
				print("Market: INSA students made a breakthrough on nuclear fusion! The energy price decreased from {} to {}.".format(oldPrice,self.price))
				self.fusionDays.append(self.day)	#Records the days when there was a fusion breakthrough.


	def goToNextDay(self):	#Waits until all the homes are done for the day. After, it updates the price and lets Weather and External know that they can start the next day.

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


	def waitForMessages(self):	#Waits for messages from homes and when they arrive assigns a worker thread to handle it.

		with ThreadPoolExecutor(max_workers=4) as executor:
			while 1:
				message=self.receiveMessage()
				executor.submit(self.handleMessage, message)


	def handleMessage(self, message):	#Waits until the day has started and then handles the messages coming from homes. It also records the budgets of each home for the day.

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
			self.numberOfHomes-=1 #lock is actually needed, but come on...
			print('Market: Henceforth there are {} homes.'.format(self.numberOfHomes))

			if self.numberOfHomes==0:	#This means the simulation must stop.
				self.numberOfHomes=100	#This freezes the simulation.

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

			
	def sendMessage(self, homeNumber, message):	#Sends a message to a given home.

		MessageQueue(homeNumber).send(str(message).encode())


	def receiveMessage(self):	#Receives messages from homes.

		x, t = self.messageQueue.receive()
		message = x.decode()
		return message



class External(Process):

	def __init__(self):

		super().__init__()			#External is a subclass of Process so we need to call Process' costructor.

		MessageQueue(300,IPC_CREAT)	#Not used for IPC but only for synchronization with Market.

		self.day=1					#External records its current day so that in the terminal we see that it is the same as other processes.


	def run(self):

		self.marketPID=getppid()
		while 1:
			print('External: It is day {}.'.format(self.day))
			self.determineTheExternalFactors()						#Each day, external determines if an external event has occurred.

			MessageQueue(102).send('Done'.encode())					#After, it lets the market know that it can start the day.

			MessageQueue(300).receive()								#Then it waits for market to tell him that he can start the next day.

			self.day+=1


	def determineTheExternalFactors(self):

		if randint(1,100)<=2:										#Each day there's a 5% chance that Macron will increase the tax on energy.
			kill(self.marketPID,SIGUSR1)
			print('External: Macron increased the tax on energy!')

		elif randint(1,100)<=1:										#Each day there's about a 1% chance that there'll be a fusion breakthrough. If the above event occurs this one doesn't so as to not overwhel the market process.
			kill(self.marketPID,SIGUSR2)
			print('External: Fusion breakthrough!')



class Weather(Process):

	def __init__(self):

		super().__init__()						#Weather is a subclass of Process so we need to call Process' costructor.

		MessageQueue(200,IPC_CREAT)				#Not used for IPC but only for synchronization with Market.

		self.day=1								#Weather records its current day so that in the terminal we see that it is the same as other processes.

		self.numberOfConsecutiveCloudyDays=0	#As the number of consecutive cloudy days increase the chance for a sunny day also increases.
		

	def run(self):

		while 1:
			print('Weather: It is day {}.'.format(self.day))
			self.determineWeatherConditions()						#Each day, Weather determines the temperature and whether or not it's sunny.

			MessageQueue(101).send('Done'.encode())					#After, it lets the market know that it can start the day.

			MessageQueue(200).receive()								#Then it waits for market to tell him that he can start the next day.

			self.day+=1


	def determineWeatherConditions(self):

		
		if sunny.value==1:	#If yesterday was sunny.
			if randint(1,100)<=70:	#If yesterday was sunny, there's a 70% chance today is as well.
				sunny.value=1
				print("Weather: Today it's sunny :D!")
			else:
				sunny.value=10
				print("Weather: Today it's cloudy :(.")
				self.numberOfConsecutiveCloudyDays+=1
		else:	#If yesterday was cloudy.
			if randint(1,100)<=98-2*self.numberOfConsecutiveCloudyDays: 	#If yesterday the beginning of the cloudy days, there's a 98% chance today is cloudy as well. With each consecutive clody day
																			#the chance for the next day to be cloudy decreases by 2%.
				sunny.value=10
				print("Weather: Today it's cloudy :(.")
				self.numberOfConsecutiveCloudyDays+=1
			else:
				sunny.value=1
				print("Weather: Today it's sunny :D!")

		temperature.value+=np.random.normal(scale=.2)					#Wheater changes the temperature according to a Gaussian distribution with scale .2.
		print("Weather: Today it's {}°C.".format(temperature.value))




if __name__=="__main__":


	#INTRODUCTION
	#This is a simulation of an energy market using concurrent execution features of Python. There are 4 kinds of processes: Market, Home, Weather, External.

	#This can be thought of as a small village. There can a a single home or 10 or anywhere between. More than 10 home is also possible but since my computer isn't very powerful I didn't try it.
	#All homes have an energy comsumption per day. This doesn't change. Some homes also have a small nuclear reactor that produces some energy for them, this is also constant.
	#If homes produce less energy than they produce, they try to get some energy for free and if that fails they buy it on the market.
	#Some homes are generous and will try to give their surplus of energy, others will sell any surplus immediately.
	
	#The climate here is constant and the temperature changes little. There are sunny and cloudy days.

	#There are some external events that occur as well. For instance every day there's a a very small chance that a breakthrough in nuclear fusion will be developped. Also a sightly bigger
	#chance that Macron will increase the tax on energy.

	#Market manages everything that happens. If a home wants to buy/sell energy it will tell it the price. Each day it updates the price according to external and internal factors such as temperature and 
	#a increase on the price of energy. It also syncronizes all the other processes. Each day it waits until Weather and External are done, then deals with all the homes. After a day is over it tells
	#all other processes that they can proceed to the next day.

	#There is also the option to have some visualization. Check the run() method of Market class for more info.



	# Two shared states that are handled by the weather process. Even though in general shared states need synchronization, multiprocessing.Value is automatically 
	# synchronized by Python so that race conditions do not occur. In other words, temperature and sunny are process and thread-safe.
	temperature=Value('d', 20)				# It's a wrapper for the temperature in celcius.
	sunny=Value('i', 1)  					# It's a wrapper for whether it's sunny or cloudy. 1: sunny, 10: cloudy
	

	# We instantiate all the processes we want in the simulation:
	weather=Weather()						# No arguments.

	market=Market(10)							# Market takes the number of homes as an argument. However, by default there are 5 homes so if that is the number of homes desired, it can be left out.
											# If more or less homes is desired put it as an argument, e.g., for a single home write Market(1)

	home1=Home(10, 5, True)					# Homes take the arguments consumptionRate, productionRate, and isGenerous.
	home2=Home(10, 11, True)
	home3=Home(10, 12, False)
	home4=Home(9, 2, True)
	home5=Home(2, 0, True)
	home6=Home(15, 13, True)
	home7=Home(10, 1, False)
	home8=Home(20, 0, False)
	home9=Home(2, 2, True)
	home10=Home(5, 3, True)


	# We start the processes that we have instantiated above.
	weather.start()
	market.start()
	home1.start()
	home2.start()
	home3.start()
	home4.start()
	home5.start()
	home6.start()
	home7.start()
	home8.start()
	home9.start()
	home10.start()
