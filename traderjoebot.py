#!/usr/bin/python

# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function
import sys
import socket
import json
import time
order_no = 1
# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name="TRADERJOE"
# This variable dictates whether or not the bot is connecting to the prod
# or test exchange. Be careful with this switch!
test_mode = False
tickers = {'valbz':[], 'vale': [], 'xlf': [], 'bond': [],  'gs': [], 'ms': [], 'wfc': []}
# This setting changes which test exchange is connected to.
# 0 is prod-like
# 1 is slower
# 2 is empty

test_exchange_index=0
prod_exchange_hostname="production"

port=25000 + (test_exchange_index if test_mode else 0)
exchange_hostname = "test-exch-" + team_name if test_mode else prod_exchange_hostname

# ~~~~~============== NETWORKING CODE ==============~~~~~
def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile('rw', 1)

def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write("\n")

def read_from_exchange(exchange):
    return json.loads(exchange.readline())

    
#~~~~~================Strategies(Development)=========~~~~~~~

def buyBonds(exchange):
    global order_no
    order_no+=1
    write_to_exchange(exchange, {"type": "add", "order_id": order_no, "symbol": "BOND", "dir": "SELL", "price": 1001, "size": 16})
    order_no+=1
    write_to_exchange(exchange, {"type": "add", "order_id": order_no, "symbol": "BOND", "dir": "BUY", "price": 999, "size": 16})
            
def incoming(exchange):
    global order_no
    print("incoming message...")
    sizeLim = 0
    while(sizeLim < 500):
        message = read_from_exchange(exchange)
        if not message:
            break
        type = message['type']
        
        if type == 'fill' and message['symbol']=='BOND':
            buyBonds(exchange)
        if type == "close":
            print("Closing Server...")
            return
        if type == 'trade':
            symbol = message["symbol"]
            price = message["price"]
            if symbol  == 'VALBZ': 
                tickers['valbz'].append(price) 
            elif symbol == 'VALE': 
                tickers['vale'].append(price) 
        if type == 'reject' or type =='ack':
            print(message)

        sizeLim +=1

def meanCost(a):
    return sum(a)//len(a)

def ADRStrat(a, b):
    meanVale = meanCost(a)
    meanValbz = meanCost(b)
    if meanValbz - meanVale >= 2:
        return [True, meanVale, meanValbz]

def playbook(exchange, tickers):
    global order_no
    if(len(tickers['vale']) >= 2 and len(tickers['valbz']) >= 2):
        x = tickers['vale'][-2:]
        y = tickers['valbz'][-2:]
        costs = ADRStrat(x, y)
        if costs!=None and costs[0] == True:
            order_no+=1
            write_to_exchange(exchange, {"type" : "add", "order_id": order_no, "symbol": "VALE", "dir" : "BUY", "price": costs[1], "size": 1})
            order_no+=1
            write_to_exchange(exchange, {"type" : "convert", "order_id": order_no, "symbol": "VALE", "dir" : "SELL", "size": 1})
            order_no+=1
            write_to_exchange(exchange, {"type" : "add", "order_id": order_no, "symbol": "VALBZ", "dir" : "SELL", "price": costs[2]+1, "size": 1})


# ~~~~~============== MAIN LOOP ==============~~~~~
def main():
    global order_no
    exchange = connect()
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    hello_from_exchange = read_from_exchange(exchange)
    print("The exchange replied:", hello_from_exchange, file=sys.stderr)
    write_to_exchange(exchange, {"type": "add", "order_id": order_no, "symbol": "BOND", "dir": "SELL", "price": 1001, "size": 10})
    order_no+=1
    write_to_exchange(exchange, {"type": "add", "order_id": order_no, "symbol": "BOND", "dir": "BUY", "price": 999, "size": 10})
    order_no+=1
    while(True):
        incoming(exchange)
        playbook(exchange,tickers)
            
if __name__ == "__main__":
    main()
