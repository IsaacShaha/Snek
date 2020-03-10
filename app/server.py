import json
import os
import random

import bottle
from bottle import HTTPResponse

turnNumber = 0
priority = "food"

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
	#Add food to grid, as 0.
	for food in data["board"]["food"]:
		grid[food["y"]][food["x"]] = 0
	#Add snake parts to grid, as "h" for head and "b" for body and tail.
	for snake in data["board"]["snakes"]:
		for i in range(len(snake["body"])):
			body = snake["body"][i]
			grid[body["y"]][body["x"]] = "b" if i != 0 and grid[body["y"]][body["x"]] != "h" else "h"

	#Replace -1's with distance to nearest food.
	changed = True
	direction = 0
	count = 0
	while changed:
		count += 1
		changed = False
		if direction == 0:
			yRange = range(len(grid))
			xRange = range(len(grid))
		elif direction == 1:
			yRange = range(len(grid)-1, -1, -1)
			xRange = range(len(grid[0])-1, -1, -1)
		direction = (direction + 1) % 2
		for y in yRange:
			for x in xRange:
				if not isinstance(grid[y][x], int):
					continue
				#Add neighbouring grids that exist to d, differential list.
				differential = []
				if y - 1 >= 0:
					differential.append((-1, 0))
				if y + 1 < data["board"]["height"]:
					differential.append((1, 0))
				if x - 1 >= 0:
					differential.append((0, -1))
				if x + 1 < data["board"]["width"]:
					differential.append((0, 1))
				#Condition 1: I am -1 and my neighbour is >= 0. Change to neighbour+1.
				#Condition 2: My neighbour is >= 0 and I am 2 or more greater than my neighbour. Change to neighbour+1.
				for d in differential:
					neighbour = grid[y+d[0]][x+d[1]]
					if not isinstance(neighbour, int):
						continue
					if (grid[y][x] == -1 and neighbour >= 0) or (neighbour >= 0 and grid[y][x] - neighbour >= 2):
						grid[y][x] = neighbour + 1
						changed = True

	head = data["you"]["body"][0]
	moves = ((head["x"], head["y"]-1, "up"), (head["x"]-1, head["y"], "left"),
		(head["x"]+1, head["y"], "right"), (head["x"], head["y"]+1, "down"))

	validMoves = []
	for move in moves:
		if move[0] >= 0 and move[0] < data["board"]["width"] and move[1] >= 0 and move[1] < data["board"]["height"]:
			validMoves.append(move)

	lowestNumber = -1
	move = "up"
	#Condition 1: lowestNumber is -1 and neighbour is any number.
	#Condition 2: lowestNumber is >= 0 and neighbour is a nonnegative number and neighbour is < lowestNumber.
	for validMove in validMoves:
		neighbour = grid[validMove[1]][validMove[0]]
		if not isinstance(neighbour, int):
			continue
		if (lowestNumber == -1) or (lowestNumber >= 0 and neighbour >= 0 and neighbour < lowestNumber):
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
