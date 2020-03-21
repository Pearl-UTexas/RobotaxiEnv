//modified from http://zetcode.com/javascript/snake/

//First read in the contents of the right JSON file to create the
//right initial state
alert("hello world");


//some bug with reading json here
var json_path = document.currentScript.getAttribute('json_path');
alert(json_path);
var json_file = JSON.parse(json_path);
alert(JSON.stringify(json_path));

var dots = json_file.initial_snake_length;

var canvas;
var ctx;

//all the images present
var auto_bus_east;
var auto_bus_north;
var auto_bus_south;
var bad_man;
var body;
var bomb;
var broken_car;
var broken_purple_car;
var bubble;
var bulldozer;
var bulldozer_east;
var bulldozer_north;
var bulldozer_south;
var bus_east;
var bus_north;
var bus_south;
var car;
var car_on_flame;
var chili;
var cool_man;
var cop;
var cop_stop;
var corgi;
var dollar;
var east_coin;
var fist;
var forest;
var garlic;
var gem;
var gorilla;
var hacker;
var heart;
var icons8_semi_truck_96;
var kids;
var lemon;
var mad;
var man;
var man_in_suite;
var moneybag;
var moneybag2;
var monster;
var north_coin;
var nut;
var pickup_east;
var pickup_north;
var pickup_south;
var pit;
var poo;
var power;
var punch;
var purple_car;
var question1;
var question2;
var question3;
var rain;
var road_block;
var road_block_broken;
var road_block_crush_east;
var road_block_crush_north;
var road_block_crush_south;
var robber;
var robot;
var rock;
var scary_tree;
var sheep;
var shepherd;
var snake;
var south_coin;
var squirrel;
var squirrel_south;
var squirrel_west;
var stopped;
var terrorist;
var thief;
var trees;
var truck_east;
var truck_north;
var truck_south;
var wave;
var woman;

//game objects
var cycles = 0;
var score = 0;

var leftDirection = false;
var rightDirection = true;
var upDirection = false;
var downDirection = false;
var inGame = true;

const DOT_SIZE = 50;
const DELAY = 140;
const C_HEIGHT = 400;
const C_WIDTH = 400;
const MAX_DOTS = json_file.field[0].length * json_file.field.length

//keyboard bindings for the arrow keys
const LEFT_KEY = 37;
const RIGHT_KEY = 39;
const UP_KEY = 38;
const DOWN_KEY = 40;

//set what the max size of the snake can be
var x = new Array(MAX_DOTS);
var y = new Array(MAX_DOTS);
var orientation = new Array(MAX_DOTS);    //0: n, 1: w, 2: s, 3: e

function init() {
    canvas = document.getElementById('myCanvas');
    ctx = canvas.getContext('2d');

    //get all of the images loaded
    loadImages();

    //Find the start of the snake and create initialize it at the given x,y
    for (var i = 0; i < json_file.field[0].length; i++) {
	for (var j = 0; j < json_field.length; j++) {
	    if (json_file.field[i].charAt(j) == 'S') {
		createSnake(i * DOT_SIZE, j * DOT_SIZE);
	    }
	}
    }

    doDrawing();
    //start the game after everything's loaded up
    setTimeout("gameCycle()", DELAY);
}    

function loadImages() {
    auto_bus_east = new Image();
    auto_bus_east.src = '../icon/auto_bus_east.png';
    
    auto_bus_north = new Image();
    auto_bus_north.src = '../icon/auto_bus_north.png';
    
    auto_bus_south = new Image();
    auto_bus_south.src = '../icon/auto_bus_south.png';
    
    bad_man = new Image();
    bad_man.src = '../icon/bad_man.png';
    
    body = new Image();
    body.src = '../icon/body.png';
    
    bomb = new Image();
    bomb.src = '../icon/bomb.png';
    
    broken_car = new Image();
    broken_car.src = '../icon/broken_car.png';
    
    broken_purple_car = new Image();
    broken_purple_car.src = '../icon/broken_purple_car.png';
    
    bubble = new Image();
    bubble.src = '../icon/bubble.png';
    
    bulldozer = new Image();
    bulldozer.src = '../icon/bulldozer.png';
    
    bulldozer_east = new Image();
    bulldozer_east.src = '../icon/bulldozer_east.png';
    
    bulldozer_north = new Image();
    bulldozer_north.src = '../icon/bulldozer_north.png';
    
    bulldozer_south = new Image();
    bulldozer_south.src = '../icon/bulldozer_south.png';
    
    bus_east = new Image();
    bus_east.src = '../icon/bus_east.png';
    
    bus_north = new Image();
    bus_north.src = '../icon/bus_north.png';
    
    bus_south = new Image();
    bus_south.src = '../icon/bus_south.png';
    
    car = new Image();
    car.src = '../icon/car.png';
    
    car_on_flame = new Image();
    car_on_flame.src = '../icon/car_on_flame.png';
    
    chili = new Image();
    chili.src = '../icon/chili.png';
    
    cool_man = new Image();
    cool_man.src = '../icon/cool_man.png';
    
    cop = new Image();
    cop.src = '../icon/cop.png';
    
    cop_stop = new Image();
    cop_stop.src = '../icon/cop_stop.png';
    
    corgi = new Image();
    corgi.src = '../icon/corgi.png';
    
    dollar = new Image();
    dollar.src = '../icon/dollar.png';
    
    east_coin = new Image();
    east_coin.src = '../icon/east_coin.png';
    
    fist = new Image();
    fist.src = '../icon/fist.png';
    
    forest = new Image();
    forest.src = '../icon/forest.png';
    
    garlic = new Image();
    garlic.src = '../icon/garlic.png';
    
    gem = new Image();
    gem.src = '../icon/gem.png';
    
    gorilla = new Image();
    gorilla.src = '../icon/gorilla.png';
    
    hacker = new Image();
    hacker.src = '../icon/hacker.png';
    
    heart = new Image();
    heart.src = '../icon/heart.png';
    
    icons8_semi_truck_96 = new Image();
    icons8_semi_truck_96.src = '../icon/icons8-semi-truck-96.png';
    
    kids = new Image();
    kids.src = '../icon/kids.png';
    
    lemon = new Image();
    lemon.src = '../icon/lemon.png';
    
    mad = new Image();
    mad.src = '../icon/mad.png';
    
    man = new Image();
    man.src = '../icon/man.png';
    
    man_in_suite = new Image();
    man_in_suite.src = '../icon/man_in_suite.png';
    
    moneybag = new Image();
    moneybag.src = '../icon/money-bag.png';
    
    moneybag2 = new Image();
    moneybag2.src = '../icon/money-bag2.png';
    
    monster = new Image();
    monster.src = '../icon/monster.png';
    
    north_coin = new Image();
    north_coin.src = '../icon/north_coin.png';
    
    nut = new Image();
    nut.src = '../icon/nut.png';
    
    pickup_east = new Image();
    pickup_east.src = '../icon/pickup_east.png';
    
    pickup_north = new Image();
    pickup_north.src = '../icon/pickup_north.png';
    
    pickup_south = new Image();
    pickup_south.src = '../icon/pickup_south.png';
    
    pit = new Image();
    pit.src = '../icon/pit.png';
    
    poo = new Image();
    poo.src = '../icon/poo.png';
    
    power = new Image();
    power.src = '../icon/power.png';
    
    punch = new Image();
    punch.src = '../icon/punch.png';
    
    purple_car = new Image();
    purple_car.src = '../icon/purple_car.png';
    
    question1 = new Image();
    question1.src = '../icon/question1.png';
    
    question2 = new Image();
    question2.src = '../icon/question2.png';
    
    question3 = new Image();
    question3.src = '../icon/question3.png';
    
    rain = new Image();
    rain.src = '../icon/rain.png';
    
    road_block = new Image();
    road_block.src = '../icon/road_block.png';
    
    road_block_broken = new Image();
    road_block_broken.src = '../icon/road_block_broken.png';
    
    road_block_crush_east = new Image();
    road_block_crush_east.src = '../icon/road_block_crush_east.png';
    
    road_block_crush_north = new Image();
    road_block_crush_north.src = '../icon/road_block_crush_north.png';
    
    road_block_crush_south = new Image();
    road_block_crush_south.src = '../icon/road_block_crush_south.png';
    
    robber = new Image();
    robber.src = '../icon/robber.png';
    
    robot = new Image();
    robot.src = '../icon/robot.png';
    
    rock = new Image();
    rock.src = '../icon/rock.png';
    
    scary_tree = new Image();
    scary_tree.src = '../icon/scary_tree.png';
    
    sheep = new Image();
    sheep.src = '../icon/sheep.png';
    
    shepherd = new Image();
    shepherd.src = '../icon/shepherd.png';
    
    snake = new Image();
    snake.src = '../icon/snake.png';
    
    south_coin = new Image();
    south_coin.src = '../icon/south_coin.png';
    
    squirrel = new Image();
    squirrel.src = '../icon/squirrel.png';
    
    squirrel_south = new Image();
    squirrel_south.src = '../icon/squirrel_south.png';
    
    squirrel_west = new Image();
    squirrel_west.src = '../icon/squirrel_west.png';
    
    stopped = new Image();
    stopped.src = '../icon/stopped.png';
    
    terrorist = new Image();
    terrorist.src = '../icon/terrorist.png';
    
    thief = new Image();
    thief.src = '../icon/thief.png';
    
    trees = new Image();
    trees.src = '../icon/trees.png';
    
    truck_east = new Image();
    truck_east.src = '../icon/truck_east.png';
    
    truck_north = new Image();
    truck_north.src = '../icon/truck_north.png';
    
    truck_south = new Image();
    truck_south.src = '../icon/truck_south.png';
    
    wave = new Image();
    wave.src = '../icon/wave.png';
    
    woman = new Image();
    woman.src = '../icon/woman.png';
}

function createSnake(startx, starty) {
    for (var z = 0; z < dots; z++) {
        x[z] = startx - z * DOT_SIZE;
        y[z] = starty;
	orientation[z] = 3;
    }
}

function doDrawing() {
    
    ctx.clearRect(0, 0, C_WIDTH, C_HEIGHT);
    
    if (inGame) {
	for (var i = 0; i < json_file.field[0].length; i++) {
	    for (var j = 0; j < json_field.length; j++) {
		//check for dot first because of runtime efficency
		if (json_file.field[i].charAt(j) != '.') {
		    //draw whatever extra images you want
		    if (json_file.field[i].charAt(j) == '#') {
			ctx.drawImage(trees, i * DOT_SIZE, j * DOT_SIZE);
		    }
		    if (json_file.field[i].charAt(j) == '0') {
			ctx.drawImage(man, i * DOT_SIZE, j * DOT_SIZE);
		    }
		    if (json_file.field[i].charAt(j) == 'o') {
			ctx.drawImage(road_block, i * DOT_SIZE, j * DOT_SIZE);
		    }
		    if (json_file.field[i].charAt(j) == '!') {
			ctx.drawImage(car, i * DOT_SIZE, j * DOT_SIZE);
		    }
		}
	    }
	}

        for (var z = 0; z < dots; z++) {
	    if (orientation[z] == 0) {
		ctx.drawImage(auto_bus_north, x[z], y[z])
	    }
	    if (orientation[z] == 1) {
		ctx.drawImage(auto_bus_east, x[z], y[z])
	    }
	    if (orientation[z] == 2) {
		ctx.drawImage(auto_bus_south, x[z], y[z])
	    }
	    if (orientation[z] == 3) {
		ctx.drawImage(auto_bus_east, x[z], y[z])
	    }
        }    
    }
    else {
        gameOver();
    }        
}

function gameOver() {
    
    ctx.fillStyle = 'white';
    ctx.textBaseline = 'middle'; 
    ctx.textAlign = 'center'; 
    ctx.font = 'normal bold 18px serif';
    
    ctx.fillText('Game over', C_WIDTH/2, C_HEIGHT/2);
}

function move() {
    //every sprite aside from the first dot gets updated by a frame
    for (var z = dots; z > 0; z--) {
        x[z] = x[(z - 1)];
        y[z] = y[(z - 1)];
	orientation[z] = orientation[(z - 1)];
    }

    //update the head of the snake (both position and orientation)
    if (leftDirection) {
        x[0] -= DOT_SIZE;
	orientation[0] = 1;
    }

    if (rightDirection) {
        x[0] += DOT_SIZE;
	orientation[0] = 3;
    }

    if (upDirection) {
        y[0] -= DOT_SIZE;
	orientation[0] = 0;
    }

    if (downDirection) {
        y[0] += DOT_SIZE;
	orientation[0] = 2;
    }
}    

function checkCollision() {

    for (var z = dots; z > 0; z--) {
	//z > 4 check is present to check if it's even possible for
	//a collision to happen
        if ((z > 4) && (x[0] == x[z]) && (y[0] == y[z])) {
            inGame = false;
        }
    }

    if (y[0] >= C_HEIGHT) {
        inGame = false;
    }

    if (y[0] < 0) {
       inGame = false;
    }

    if (x[0] >= C_WIDTH) {
      inGame = false;
    }

    if (x[0] < 0) {
      inGame = false;
    }
}

function gameCycle() {
    if (inGame) {
	cycles += 1;
	score += json_file.rewards.timestep;
        move();
        checkCollision();
        doDrawing();
	if (cycles < json_file.max_step_limit) {
	    setTimeout("gameCycle()", DELAY);
	}
    }
}

onkeydown = function(e) {
    
    var key = e.keyCode;
    
    if ((key == LEFT_KEY) && (!rightDirection)) {
        leftDirection = true;
        upDirection = false;
        downDirection = false;
    }

    if ((key == RIGHT_KEY) && (!leftDirection)) {
        rightDirection = true;
        upDirection = false;
        downDirection = false;
    }

    if ((key == UP_KEY) && (!downDirection)) {
        upDirection = true;
        rightDirection = false;
        leftDirection = false;
    }

    if ((key == DOWN_KEY) && (!upDirection)) {
        
        rightDirection = false;
        leftDirection = false;
    }        
};    
