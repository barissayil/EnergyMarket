from multiprocessing import Process, Value, Lock, Array
from sysv_ipc import MessageQueue, IPC_CREAT
import random
from time import sleep
import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, Semaphore
import os
import signal

class External(Process):

	def __init__(self,market_PID):
		super().__init__()
		self.marketPID = market_PID
		self.evenement=False
		print(self.marketPID)

	def run(self):
		while 1:
			self.chances_evt=20
			while self.evenement == False :
				sleep(1)
				event = random.randint(0,self.chances_evt)
				if event == 1:
					os.kill(self.marketPID, signal.SIGUSR1)
					self.evenement=True
					print("External: A catastrophe has occurred")
				else:
					self.chances_evt -=1

class Market(Process):

	def __init__(self):

		super().__init__()


	def run(self):
		self.price=20
		self.freeEnergy=0
		self.freeEnergyLimit=10
		self.messageQueue=MessageQueue(100,IPC_CREAT)
		print("Market: My messageQueue is {}",format(self.messageQueue))
		self.eventOccurring=False
		myPID=os.getpid()
		external_process=External(myPID)
		external_process.start()
		Thread(target=self.updatePrice).start()
		print("On arrive la")
		#with ThreadPoolExecutor(max_workers=3) as executor: #TODO A CHANGER ( 3Thread quu lisent en continu)
		#	executor.submit(self.handleMessages) #Idealement 1 thread qui lit et 3 qui traitent l'info
		print("On arrive ici")
		while 1:
			print("On cherche des signaux")
			print(self.eventOccurring)
			signal.signal(signal.SIGUSR1,handler)
			if self.eventOccurring==True:
				print("Event occurr")

			sleep(1)


	def updatePrice(self):
		while 1:
			print("we do some stuffs")
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

def handler(typeOfSignal, frame):

	if (typeOfSignal == signal.SIGUSR1):
		self.eventOccurring = ~self.eventOccurring #TODO implement: price variates over events (for now they are bad)
		#TODO implement more signals, bad events and good events

if __name__=="__main__":


	clean()



	temperature=Value('d', 12.5)
	sunny=Value('i', 1)  					# 1: sunny, 0: cloudy



	# weather=Weather()						#Weather is optional at the moment.
	# weather.start()




	priceLock = Lock()


	market=Market()
	market.start()


	#home1=Home(10, 0, True)
	#home1.start()


	#home2=Home(5, 13, True)
	#home2.start()


	# home3=Home(5, 15, False)
	# home3.start()


	# home4=Home(9, 2, True)
	# home4.start()


	# home4=Home(5, 0, True)
	# home4.start()
