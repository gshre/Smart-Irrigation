
import asyncio
import websockets
import time
from datetime import datetime

Timer=[]
Sprk=0
Drip=0
val_1=0
val_2=0
Val_source=""
Time=0
target = {}
client=[]
class handler:
    global Sprk,Drip,Timer
    def __init__(self):
        self.ws = None
    CONNECTION_TYPE=""
    async def on_recieve(self, ws,data):
            global Sprk,Drip,Timer,val_1,val_2,Time,Val_source
            if data[1:] in "target":
                self.CONNECTION_TYPE="target"
                print("target registered")
                val_1=0
                val_2=0
                target[data[1:]]=self
            if data[1:] in "client":
                self.CONNECTION_TYPE="client"
                print("client registered")
                client.append(self)    
            print(client)
            print(target)
            self.ws = ws
            while True:
                try:
                    data=await ws.recv()
                except:
                    print ("Connection with ",self.CONNECTION_TYPE," Lost")
                    if self.CONNECTION_TYPE=="client":
                        client.remove(self)  
                    break

                print("recieving",self.CONNECTION_TYPE,data)
                data=data.split()
                if self.CONNECTION_TYPE == "client":
                    if data[0]=='0':
                        print("Initial Data Request")
                        txt=""
                        for x in Timer:
                            txt+=' '+conv_min_time(int(x))
                        await self.on_send("1 "+txt)
                        await self.on_send("2 "+str(Sprk)+' '+str(Drip)) 
                        await self.on_send("3 1 0 "+str(val_1)+" "+Val_source)
                        await self.on_send("3 1 2 "+str(val_2)+" "+Val_source)
                        await self.on_send("3 2 "+str(Time))
                        try:
                            await target['target'].on_send("0")
                        except:
                            await self.on_send("target not connected")
                        if 'target' in target:
                            await self.on_send("4")
                    if data[0]=='1':
                        print("Timer Updation Request")
                        if(data[1]!="00:00"):
                            Timer.append(conv_time_min(data[1]))
                            await self.on_send("1 "+data[1])
                            try:
                                await target['target'].on_send("1 "+str(conv_time_min(data[1]))+';')  
                            except:
                                await self.on_send("target not connected")
                        else:
                            await self.on_send("Error")
                        Timer.sort()  
                        write_conf()      
                    if data[0]=='2':
                        print("Timer Deletion Request")
                        print(Timer)
                        Timer.remove(conv_time_min(data[1])) 
                        try:
                            await target['target'].on_send("6")
                        except:
                            await self.on_send("target not connected")
                        write_conf()
                    if data[0]=='3':
                        if 'target' in target:
                            if data[1]=='1':
                                Sprk=int(data[2]) 
                                print("Sprnkler Timer Updated") 
                                await target['target'].on_send('2 '+str(Sprk)+' '+str(Drip))  
                            if data[1]=='2':
                                Drip=int(data[2]) 
                                await target['target'].on_send('2 '+str(Sprk)+' '+str(Drip))   
                                print("Dripper Timer Updated") 
                        else:
                            await self.on_send("Target Not Connected")  
                        write_conf()
                    if data[0]=='4':
                        if 'target' in target:
                            if data[1]=='1':
                                print("Valve 1 Open")
                                await target['target'].on_send('4 1 '+data[2])
                            if data[1]=='2':  
                                print("Valve 2 Open",target['target'])
                                await target['target'].on_send('4 2 '+data[2]) 
                        else:
                            await self.on_send("Target Not Connected")  
                    if data[0]=='5':
                        try:
                            await target['target'].on_send("3") 
                            await target['target'].ws.close() 
                        except:
                            await self.on_send("target not connected") 

                if 'target' in self.CONNECTION_TYPE:
                    if data[0] =='0':
                        print("Target Booted Requesting data")
                        txt=""
                        Time=conv_min_time(0)
                        for x in Timer:
                            txt+=' '+str(x)
                        await self.on_send("1 "+txt+';')
                        await self.on_send("2 "+str(Sprk)+' '+str(Drip)) 
                        ct=datetime.now()
                        ct=ct.strftime("%H:%M")
                        await self.on_send("5 "+str(conv_time_min(ct)))
                        await self.send_to_all("4")
                    if data[0] == '1':
                        print("Target Update") 
                        if data[1]=='1':
                            Val_source=data[4]
                            print("Valve Open")
                            if(data[2]=='0'):
                                val_1=int(data[3])
                            if(data[2]=='2'):
                                val_2=int(data[3])    
                            print("va",val_1,val_2,data[3])    
                            await self.send_to_all("3 1 "+data[2]+" "+data[3]+" "+data[4])
                        if data[1]=='2':
                            print("Timer Running")
                            Time=conv_min_time(int(data[2]))
                            await self.send_to_all("3 2 "+Time)
                    if data[0]=='__ping__':
                        await self.on_send("0")        
                               


    async def on_send(self,data):
        print("sending to ",self.CONNECTION_TYPE,data)
        try:
            await self.ws.send(data)  
        except:
             print ("Connection with ",self.CONNECTION_TYPE," Lost")
             if self.CONNECTION_TYPE=="client":
                client.remove(self)  
             if self.CONNECTION_TYPE=="target":
                target.pop('target') 
    def get_connection_type(self):
        print(self.CONNECTION_TYPE)
        return self.CONNECTION_TYPE    
    async def send_to_all(self,data):
        for x in client:
            await x.on_send(data)    
       
def write_conf():
    try:
        f=open("timer_conf.conf","w+")
        f.write(str(Sprk)+" "+str(Drip)+"\n")
        for x in Timer:
            f.write(str(x)+" ")
        f.write("\n")
        f.close() 
    except:
        print("Something went wrong")
     
def read_conf():
     global Sprk,Drip,Timer
     try:
        f=open("timer_conf.conf","r")
        txt=list(map(int,f.readline().split()))
        print(txt)
        Sprk=txt[0]
        Drip=txt[1]
        Timer=list(map(int,f.readline().split()))
        f.close()
     except:
        print("No Configuration")
                
def conv_time_min(str):
    h=int(str[:2])
    m=int(str[3:])
    print(h)
    print(m)
    return (h*60)+m
def conv_min_time(str1):
    h=str1//60
    m=str1%60
    if(m<10):
       m='0'+str(m)
    else:
       m=str(m)   
    if(h<10):
       h='0'+str(h) 
    else:
       h=str(h) 
    print(h)
    print(m)
    return h+':'+m  

async def spawn(ws, data):
    print('ws', hash(ws))
    hand = handler()
    print('handler', hash(hand))
    await hand.on_recieve(ws, data)

read_conf()
start_server = websockets.serve(spawn, "192.168.0.108", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

