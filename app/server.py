import json
import os
import random

import bottle
from bottle import HTTPResponse

turnNumber = 0
direction = -1
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

    response = {"color": "#91E175", "headType": "bwc-ski", "tailType": "skinny"}
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
    global direction
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
    		grid[body["y"]][body["x"]] = "h" if i == 0 else "b"

    #Replace -1's with distance to nearest food.
    changed = True
    while changed:
    	changed = False
    	for y in range(len(grid)):
    		for x in range(len(grid)):
    			if not isinstance(grid[y][x], int):
    				continue
    			#Add neighbouring grids that exist to d, differential list.
    			differential = []
    			if y > 0:
    				differential.append((-1, 0))
    			if y < data["board"]["height"] - 1:
    				differential.append((1, 0))
    			if x > 0:
    				differential.append((0, -1))
    			if x < data["board"]["width"] - 1:
    				differential.append((0, 1))
    			#Condition 1: I am -1 and my neighbour is 0. Change to 1.
    			#Condition 2: I am > 1 and my neighbour is 0. Change to 1.
				#Condition 3: I am -1 and my neighbour is any positive integer. Change to neighbour+1.
				#Condition 4: I am > 2 and my neighbour is any positive integer I am 2 or more
				#				greater above my neighbour. Change to neighbour+1.
    			for d in differential:
    				neighbour = grid[y+d[0]][x+d[1]]
    				if not isinstance(neighbour, int):
    					continue
    				#Condition 1
    				if grid[y][x] == -1 and neighbour == 0:
    					grid[y][x] = 1
    					changed = True
					#Condition 2
    				elif grid[y][x] > 1 and neighbour == 0:
    					grid[y][x] = 1
    					changed = True
    				#Condition 3
    				elif grid[y][x] == -1 and neighbour > 0:
    					grid[y][x] = neighbour + 1
    					changed = True
    				#Condition 4
    				elif grid[y][x] > 2 and neighbour > 0 and grid[y][x] - neighbour > 1:
    					grid[y][x] = neighbour + 1
    					changed = True
    printGrid(grid)

    head = data["you"]["body"][0]

    food = data["board"]["food"]
    closestFood = -1
    closestDistance = -1
    for i in range(len(food)):
    	distance = getDistance(food[i], head)
    	if closestFood == -1 or distance < closestDistance:
    		closestFood = food[i]
    		closestDistance = distance

    # Choose a random direction to move in
    directions = ["up", "right", "down", "left"]
    direction = (direction + 1)%4
    move = directions[direction]

    # Shouts are messages sent to all the other snakes in the game.
    # Shouts are not displayed on the game board.
    shout = "am snek :-) pls 2 meet u"

    response = {"move": move, "shout": shout}
    '''
    return HTTPResponse(
    	status=200,
    	headers={"Content-Type": "application/json"},
    	body=json.dumps(response),
    )
    '''

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
