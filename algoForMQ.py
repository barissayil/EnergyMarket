#How the message queues will be created 

Home():

  init():
    create mq w/ key=0  #common mq to be used for communicating the creation of new homes
    self.sendMessageQueue(0,self.homeNumber)  # tell market that i exist. here key=0, message=self.homeNumber
    create mq w/ key=self.homeNumber
    


    
 Market():
 
  init():
    create mq w/ key=0   #common mq to be used for communicating the creation of new homes
    
    
  run():
    message=receiveMessageQueue(0) #market is constantly checking if there's a massage in mq(0) i.e. a new home is created
    if message!='': #if there's a new home created
      self.numberOfHomes++
      create mq w/ key=self.numberOfHomes
      
      
      
 #Notes:
 #the mq values for both classes are gonna be lists
 #this should work for IPC between all the homes and the market but not between different homes
 #the stuff i wrote in market's run() should be in handleRequest and also the market should launch a new thread with each new message queue to be able to listen to all the homes concurrently
 #i an idea on how to make create the message queues between different homes too, but first we should make this work
 
      




