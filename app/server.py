#Local URL: http://127.0.0.1:8080/
#Heroku URL: http://snookinsnek.herokuapp.com/

import json
import os
import random
from queue import Queue

import bottle
from bottle import HTTPResponse

NEIGHBOUR_OFFSETS = ((-1, 0), (1, 0), (0, -1), (0, 1))

turnNumber = -1
priority = 1

def getDistance(coord1, coord2):
	return abs(coord1["x"] - coord2["x"]) + abs(coord1["y"] - coord2["y"])

def printGrid(grid):
	print("\n")
	for i in range(len(grid)):
		line = ""
		for j in grid[i]:
			line += str(j)
			line += "\t"
		print(line)

@bottle.route("/")
def index():
	return "Your Battlesnake is alive!"

@bottle.post("/ping")
def ping():
	"""
	Used by the Battlesnake Engine to make sure your snake is still working.
	"""
	return HTTPResponse(status=200)

@bottle.post("/start")
def start():
	global turnNumber
	turnNumber = -1
	"""
	Called every time a new Battlesnake game starts and your snake is in it.
	Your response will control how your snake is displayed on the board.
	"""
	data = bottle.request.json
	#print("START:", json.dumps(data))

	response = {"color": "#000000", "headType": "bwc-ski", "tailType": "skinny"}
	return HTTPResponse(
		status=200,
		headers={"Content-Type": "application/json"},
		body=json.dumps(response),
	)


@bottle.post("/move")
def move():
	"""
	Called when the Battlesnake Engine needs to know your next move.
	The data parameter will contain information about the board.
	Your response must include your move of up, down, left, or right.
	"""

	global turnNumber
	global priority

	data = bottle.request.json
	turnNumber += 1
	#print("\nMOVE " + str(turnNumber) + ":", json.dumps(data))

	grid = []
	#Create grid, initialize with -1 on each spot.
	for i in range(data["board"]["height"]):
		grid.append([])
		for j in range(data["board"]["width"]):
			grid[i].append(-1)
	#Add snake parts to grid, as "h" for head and "b" for body and tail.
	for snake in data["board"]["snakes"]:
		for i in range(len(snake["body"])):
			body = snake["body"][i]
			grid[body["y"]][body["x"]] = "b" if i != 0 and grid[body["y"]][body["x"]] != "h" else "h"

	if priority == 1:

		#Keep track of visited coordinates, so as to not re-visit them and maintain time complexity.
		marked = []
		for y in range(data["board"]["height"]):
			marked.append([])
			for x in range(data["board"]["width"]):
				marked[y].append(False)

		#Add food to grid, as 0.
		queue = Queue(data["board"]["width"]*data["board"]["height"])#Set queue maxsize to width*height.
		for food in data["board"]["food"]:
			foodCoords = (food["x"], food["y"])
			grid[foodCoords[1]][foodCoords[0]] = 0
			marked[foodCoords[1]][foodCoords[0]] = True

		#Add food neighbours to queue.
		for food in data["board"]["food"]:
			coord = (food["x"], food["y"])
			for dy, dx in NEIGHBOUR_OFFSETS:
				try:#Add COORDINATE of empty neighbours to queue. Possible exceptions: Out of grid bounds.
					if coord[0]+dx < 0 or coord[1]+dy < 0:
						raise IndexError
					neighbour = grid[coord[1]+dy][coord[0]+dx]
					if neighbour == -1 and not marked[coord[1]+dy][coord[0]+dx]:
						#Add the coordinates for the neighbour to the queue and set the neighbour's value.
						grid[coord[1]+dy][coord[0]+dx] = 1 #Food is 0 and 0+1=1
						queue.put((coord[0]+dx, coord[1]+dy))
						marked[coord[1]+dy][coord[0]+dx] = True
				except:#Every try syntactically needs an except, even if it's useless :(
					pass

		#Now, do Breadth-First Search. Time complexity is O(width*height), or O(area).
		#This is only possible because we set the queue maxsize to width*height and we keep track of visited grid spots.
		#With each queue entry's unmarked neighbours, we set the value and add them to the queue.
		while not queue.empty():
			coord = queue.get()
			for dy, dx in NEIGHBOUR_OFFSETS:
				try:#Add COORDINATE of empty neighbours to queue. Possible exceptions: Out of grid bounds.
					if coord[0]+dx < 0 or coord[1]+dy < 0:
						raise IndexError
					neighbour = grid[coord[1]+dy][coord[0]+dx]
					if neighbour == -1 and not marked[coord[1]+dy][coord[0]+dx]:
						#Add the coordinates for the neighbour to the queue and set the neighbour's value.
						grid[coord[1]+dy][coord[0]+dx] = grid[coord[1]][coord[0]]+1
						queue.put((coord[0]+dx, coord[1]+dy))
						marked[coord[1]+dy][coord[0]+dx] = True
				except IndexError as error:#Every try syntactically needs an except, even if it's useless :(
					pass

	head = data["you"]["body"][0]
	moves = ((head["x"], head["y"]-1, "up"), (head["x"]-1, head["y"], "left"),
		(head["x"]+1, head["y"], "right"), (head["x"], head["y"]+1, "down"))

	validMoves = []
	for move in moves:
		if move[0] >= 0 and move[0] < data["board"]["width"] and move[1] >= 0 and move[1] < data["board"]["height"]:
			validMoves.append(move)

	lowestNumber = -1
	move = "up"
	#Condition 1: lowestNumber is -1 and neighbour is ANY number.
	#Condition 2: neighbour is >= 0 and neighbour is < lowestNumber.
	for validMove in validMoves:
		neighbour = grid[validMove[1]][validMove[0]]
		if not isinstance(neighbour, int):
			continue
		if ((lowestNumber == -1) or (neighbour >= 0 and neighbour < lowestNumber)):
			lowestNumber = neighbour
			move = validMove[2]

	# Shouts are messages sent to all the other snakes in the game.
	# Shouts are not displayed on the game board.
	shout = "am snek :-) pls 2 meet u"

	response = {"move": move, "shout": shout}

	return HTTPResponse(
		status=200,
		headers={"Content-Type": "application/json"},
		body=json.dumps(response),
	)

@bottle.post("/end")
def end():
	"""
	Called every time a game with your snake in it ends.
	"""
	data = bottle.request.json
	#print("END:", json.dumps(data))
	return HTTPResponse(status=200)


def main():
	bottle.run(
		application,
		host=os.getenv("IP", "0.0.0.0"),
		port=os.getenv("PORT", "8080"),
		debug=os.getenv("DEBUG", True),
	)


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == "__main__":
	main()
