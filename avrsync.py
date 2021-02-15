
import asyncio
from datetime import datetime

import snapcast.control
import denonavr


def isClientActive(server, clientName):
    stream = server.stream('cosy')
    client = [c for c in server.clients if c.friendly_name == clientName][0]

    stream = server.stream(client.group.stream)
    
    print(stream.status)
    print(client.muted)

    return stream.status == 'playing' and not client.muted

def readSourceStatus(avr, source):
    print(avr.power)
    print(avr.input_func)

    if avr.power == 'OFF':
        return 'available'
    elif avr.power == 'ON' and avr.input_func == source:
        return 'ready'
    return 'busy'

class Monitor:
  def __init__(self):
    self.idle_since = None
    self.loop = asyncio.get_event_loop()
    self.avr = denonavr.DenonAVR('Fenrir')
    self.snapserver = self.loop.run_until_complete(snapcast.control.create_server(self.loop, 'cosy'))
    

  def sync(self):
    self.avr.update()
    avr = self.avr
    sourceStatus = readSourceStatus(avr, 'DVD/Blu-ray') 
    print(sourceStatus)
    if sourceStatus == 'busy':
        self.idle_since = None
        return
    self.snapserver.synchronize(
        self.loop.run_until_complete(
            self.snapserver.status()
        )
    )
    clientActive = isClientActive(self.snapserver, 'cosy')
    print(f"clientActive: {clientActive}")

    if clientActive:
        if sourceStatus == 'available':
            avr.input_func = 'DVD/Blu-ray'
        self.idle_since = None

    elif sourceStatus == 'ready':
        if self.idle_since is None:
            self.idle_since = datetime.now()
            print(f"starting idle timer at: {self.idle_since}")
        elif (datetime.now() - self.idle_since).total_seconds() > 60:
            avr.power_off()
            self.idle_since = None
        else:
            print(f"idle for {(datetime.now() - self.idle_since).total_seconds()}")

if __name__ == '__main__':
  from time import sleep

  monitor = Monitor()
  while True:
    sleep(0.2)
    monitor.sync()
