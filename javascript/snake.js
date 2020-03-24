//modified from http://zetcode.com/javascript/snake/
//First read in the contents of the right JSON file to create the
//right initial state
//alert("hello world");


//some bug with reading json here
//var json_path = document.currentScript.getAttribute('json_path');
//alert("first");

//function loadJSON(filePath, success, error) {
//    var xhr = new XMLHttpRequest();
//    xhr.onreadystatechange = function() {
//	if (xhr.readystate === XMLHttpRequest.DONE) {
//	    if (xhr.status === 200) {
//		if (success)
//		    success(JSON.parse(xhr.responseText));
//	    }
//	    else {
//		if (error)
//		    error(xhr);
//	    }
//	}
//    };
//    xhr.open('GET', filePath, true);
//    xhr.send();
//}

//
//alert('first');
//alert('hi')
//var json_file = JSON.parse('test.json');
//$.getJSON('test.json', function(json) {
//    console.log(json)
//    json_file = json;
//});

//var json_file = JSON.parse('{  "field": [    "########",    "#......#",    "#......#",    "#...S..#",    "#......#",    "#......#",    "#......#",    "########"  ],  "initial_snake_length": 2,  "max_step_limit": 200,  "rewards": {    "timestep": 0,    "good_fruit": 6,    "bad_fruit": -1,    "died": 0,    "lava": -5  }}');
var json_file = JSON.parse('{  "field": [    "########",    "#......#",    "#...S..#",    "#......#",    "#.P....#",    "#...C..#",    "#......#",    "########"  ],  "initial_snake_length": 1,  "max_step_limit": 200,  "rewards": {    "timestep": 0,    "good_fruit": 6,    "bad_fruit": -1,    "died": 0,    "lava": -5  }}');

var dots = json_file.initial_snake_length;

var canvas;
var ctx;

//all the images present
var auto_bus_east;
var auto_bus_north;
var auto_bus_south;
var auto_bus_west;
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
var go = true;

const DELAY = 75;
const C_HEIGHT = 700;
const C_WIDTH = 700;
const DOT_SIZE = C_HEIGHT / json_file.field[0].length;
const MAX_DOTS = json_file.field[0].length * json_file.field.length
const INC_VAL = 10

//keyboard bindings for the arrow keys
const LEFT_KEY = 37;
const RIGHT_KEY = 39;
const UP_KEY = 38;
const DOWN_KEY = 40;

//set what the max size of the snake can be
var x = new Array(MAX_DOTS);
var y = new Array(MAX_DOTS);
var orientation = new Array(MAX_DOTS);    // 0: n, 1: w, 2: s, 3: e
var map = new Array(json_file.field.length)
var accident_tracker = new Array(json_file.field.length)
var next_transition = [1.0, 0.0];

for (var i = 0; i < json_file.field.length; i++) {
    map[i] = json_file.field[i].split("");
    accident_tracker[i] = new Array(json_file.field[i].length);
    for (var j = 0; j < json_file.field[0].length; j++) {
        accident_tracker[i][j] = 0;
    }
}

var transition = new Array(MAX_DOTS)

for (var i = 0; i < transition.length; i++) {
    if (i == 0)
        transition[i] = [1, 0];
    else
        transition[i] = [1, 0];
}



function init() {
    canvas = document.getElementById('myCanvas');
    ctx = canvas.getContext('2d');

    //get all of the images loaded
    loadImages();

    //Find the start of the snake and create initialize it at the given x,y
    for (var i = 0; i < json_file.field[0].length; i++) {
	    for (var j = 0; j < json_file.field.length; j++) {
	        if (json_file.field[i].charAt(j) == 'S') {
                createSnake(i * DOT_SIZE, j * DOT_SIZE);
	        }
	    }
    }

    doDrawing();

    //start the game after everything's loaded up
    //
    setTimeout("gameCycle()", DELAY);
    
}    

function loadImages() {
    auto_bus_east = new Image();
    auto_bus_east.src = '../icon/auto_bus_east.png';
    
    auto_bus_north = new Image();
    auto_bus_north.src = '../icon/auto_bus_north.png';
    
    auto_bus_south = new Image();
    auto_bus_south.src = '../icon/auto_bus_south.png';

    auto_bus_west = new Image();
    auto_bus_west.src = '../icon/auto_bus_west.png';
    
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
    //instantiate the snake given a start (x,y)
    for (var z = 0; z < dots; z++) {
        x[z] = startx - z * DOT_SIZE;
        y[z] = starty;
        orientation[z] = 3;
    }
}

function doDrawing() {
    
    //first clear what was already present in the canvas
    ctx.clearRect(0, 0, C_WIDTH * 2, C_HEIGHT);

    ctx.fillStyle = 'black';
    ctx.textBaseline = 'middle'; 
    ctx.textAlign = 'center'; 

    //add font functionality later
    ctx.font = 'normal bold 40px serif';

    //create basic rendering of the right side of the screen
    ctx.fillText('EARNINGS', C_WIDTH + 200, C_HEIGHT / 2 + 100)

    ctx.fillStyle = '#A0522D';
    ctx.fillRect(C_WIDTH + 138, C_HEIGHT / 2 + 125, 125, 50)

    ctx.fillStyle = 'black';
    if (score < 0)
        ctx.fillText('-$' + (-1 * score), C_WIDTH + 200, C_HEIGHT / 2 + 150)
    else
        ctx.fillText('$' + score, C_WIDTH + 200, C_HEIGHT / 2 + 150)

    ctx.fillText('Time', C_WIDTH + 200, C_HEIGHT / 2 + 225)
    ctx.font = 'normal bold 24px serif';
    ctx.fillText(cycles + "/" + json_file.max_step_limit, C_WIDTH + 200, C_HEIGHT / 2 + 260)

    //render all of the bus
    for (var z = dots - 1; z >= 0; z--) {
        if (orientation[z] == 0) {
            ctx.drawImage(auto_bus_north, x[z] + transition[z][0], y[z] + transition[z][1])
        }
        if (orientation[z] == 1) {
            ctx.drawImage(auto_bus_west,  x[z] + transition[z][0], y[z] + transition[z][1])
        }
        if (orientation[z] == 2) {
            ctx.drawImage(auto_bus_south, x[z] + transition[z][0], y[z] + transition[z][1])
        }
        if (orientation[z] == 3) {
            ctx.drawImage(auto_bus_east,  x[z] + transition[z][0], y[z] + transition[z][1])
        }
    }

    //render the other images/obstacles over the bus
    for (var i = 0; i < map[0].length; i++) {
        for (var j = 0; j < map.length; j++) {
            //check for dot first because of runtime efficency
            if (map[i][j] != '.') {
                //draw whatever extra images you want
                if (map[i][j] == '#') {
                    ctx.drawImage(forest, i * DOT_SIZE, j * DOT_SIZE);
                }
                if (map[i][j] == 'P') {
                    if (accident_tracker[i][j] == 0)
                        ctx.drawImage(man, i * DOT_SIZE, j * DOT_SIZE);
                    else
                        ctx.drawImage(dollar, i * DOT_SIZE, j * DOT_SIZE);
                }
                if (map[i][j] == 'o') {
                    ctx.drawImage(road_block, i * DOT_SIZE, j * DOT_SIZE);
                }
                if (map[i][j] == 'C') {
                    if (accident_tracker[i][j] == 0)
                        ctx.drawImage(purple_car, i * DOT_SIZE, j * DOT_SIZE);
                    else
                        ctx.drawImage(broken_purple_car, i * DOT_SIZE, j * DOT_SIZE);
                }
            }
        }
    }
    
}

function timestepExceeded() {
    //render the ran out of steps scene
    ctx.clearRect(0, 0, C_WIDTH * 2, C_HEIGHT);
    ctx.fillStyle = 'black';
    ctx.textBaseline = 'middle'; 
    ctx.textAlign = 'center'; 
    ctx.font = 'normal bold 50px serif';

    //basically putting the minus sign in the right spot
    ctx.fillText('Finished ' + cycles + ' moves!', C_WIDTH, C_HEIGHT/2);
    if (score < 0)
        ctx.fillText('Score: -$' + (-1 * score), C_WIDTH, C_HEIGHT/2 + 45);
    else
        ctx.fillText('Score: $' + score, C_WIDTH, C_HEIGHT/2 + 45);

}

function reset() {

    //every sprite aside from the first dot gets updated by a frame
    for (var z = dots; z > 0; z--) {
        x[z] = x[(z - 1)];
        y[z] = y[(z - 1)];
        orientation[z] = orientation[(z - 1)];
        transition[z] = transition[(z - 1)];
        var temp_sum = Math.abs(transition[z][0] + transition[z][1]);
        transition[z] = [transition[z][0] * (1 / temp_sum), transition[z][1] * (1 / temp_sum)]
    }

    //update timestep
    score += json_file.rewards.timestep;
    cycles += 1;
    if (next_transition[0] == -1) {      
        leftDirection = true;
        upDirection = false;
        downDirection = false;   
    }
    else if (next_transition[0] == 1) {
        rightDirection = true;
        upDirection = false;
        downDirection = false;
    }
    else if (next_transition[1] == -1) {
        upDirection = true;
        rightDirection = false;
        leftDirection = false;
    }
    else if (next_transition[1] == 1) {
        downDirection = true;        
        rightDirection = false;
        leftDirection = false;
    }        
    transition[0] = [Math.sign(next_transition[0]), Math.sign(next_transition[1])]
}

function update_increments() {
    for (var i = 0; i < dots; i++) {
        //going up
        if (transition[i][0] == 0 && transition[i][1] < 0) {
            transition[i][1] -= INC_VAL;
        }
        //going down
        if (transition[i][0] == 0 && transition[i][1] > 0) {
            transition[i][1] += INC_VAL;
        }
        //going to the right
        if (transition[i][0] > 0 && transition[i][1] == 0) {
            transition[i][0] += INC_VAL;
        }
        //going to the left
        if (transition[i][0] < 0 && transition[i][1] == 0) {
            transition[i][0] -= INC_VAL;
        }
    }
}

function move() {
    //check if the snake is within the bounds to move a step in a given direction
    //going to the left
    if (transition[0][0] < 0) {
        orientation[0] = 1;
        update_increments();
        if (Math.abs(transition[0][0]) > DOT_SIZE) {
            reset();
            x[0] -= DOT_SIZE;
        }
    }

    //going to the right
    if (transition[0][0] > 0) {
        orientation[0] = 3;
        update_increments();
        if (Math.abs(transition[0][0]) > DOT_SIZE ) {
            reset();
            x[0] += DOT_SIZE;
        }
    }

    //going up
    if (transition[0][1] < 0) {
        orientation[0] = 0;
        update_increments();
        if (Math.abs(transition[0][1]) > DOT_SIZE) {
            reset();
            y[0] -= DOT_SIZE;
        }
    }

    //going down
    if (transition[0][1] > 0) {
        orientation[0] = 2;
        update_increments();
        if (Math.abs(transition[0][1]) > DOT_SIZE ) {
            reset();
            y[0] += DOT_SIZE;
        }
    }

}    

function checkCollision() {
    for (var z = dots; z > 0; z--) {
	    //z > 4 check is present to check if it's even possible for a collision to happen
        if ((z > 4) && (x[0] == x[z]) && (y[0] == y[z])) {
            cycles = json_file.max_step_limit;
        }
    }

    //make sure to check if in game so as to not violate array ranges
    var tempX = x[0] / DOT_SIZE;
    var tempY = y[0] / DOT_SIZE;
           
    if (tempX == 1 && leftDirection || tempX == json_file.field[0].length - 2 && rightDirection){
        //console.log('1',tempX,tempY) 
        transition[0][0] = 0;
        
        leftDirection = false;
        rightDirection = false;
        if (tempY < json_file.field[0].length / 2) { transition[0][1] = 1; downDirection =true;}
        else{  transition[0][1] = -1; upDirection=true;}
        next_transition = transition[0];
    }
    
    if (tempY == 1 && upDirection || tempY == json_file.field[0].length - 2 && downDirection){
        //console.log('2',tempX,tempY) 
        transition[0][1] = 0;
        upDirection = false;
        downDirection = false;
        if ( tempX < json_file.field[0].length / 2) {  transition[0][0] = 1; rightDirection = true;}
        else{ transition[0][0] = -1; leftDirection = true;}
        next_transition = transition[0];
    }

    if (map[tempX][tempY] == 'C' && accident_tracker[tempX][tempY] == 0) {
        //bus is on a car tile
        score += json_file.rewards.bad_fruit;
        accident_tracker[tempX][tempY] = 7;         //7 denotes the amount of cycles for this entity to fade away
    }
    else if (map[tempX][tempY] == 'P' && accident_tracker[tempX][tempY] == 0) {
        //bus picked up a person
        score += json_file.rewards.good_fruit;
        accident_tracker[tempX][tempY] = 7;
    }
    else if (map[tempX][tempY] == '#' && accident_tracker[tempX][tempY] == 0) {
        //bus hit a forest
        score += json_file.rewards.died;
        accident_tracker[tempX][tempY] = '#';
        
    }

    //iterate thorugh the entire map to check if any can be removed due to fade time elapsing
    for (var i = 0; i < map.length; i++) {
        for (var j = 0; j < map[0].length; j++) {
            if (accident_tracker[i][j] != 0) {
                if (accident_tracker[i][j] == 1) {
                    map[i][j] = '.';
                }
                accident_tracker[i][j] -= 1;
            }
        }
    }

}

function gameCycle() {
    if (cycles < json_file.max_step_limit) {
        doDrawing();
        //if (go || transition[0][0] == 0 || transition[0][1] == 0) {
        
        move();
        checkCollision();
        
        //}
        setTimeout("gameCycle()", DELAY);
    }
    else {
        // Timestep is too much
        timestepExceeded();
    }
}

onkeydown = function(e) {
    // Change direction of the bus when key is pressed

    var key = e.keyCode;
    var tempX = x[0] / DOT_SIZE;
    var tempY = y[0] / DOT_SIZE;
    go = true;
    //console.log(tempX, tempY)
    //get key input to make the bus move in a certain direction
    if ((key == LEFT_KEY) && (!rightDirection) && (tempX > 1)) {      
        next_transition =  [-1, 0];    
    }
    else if ((key == RIGHT_KEY) && (!leftDirection) && (tempX < json_file.field[0].length -2)) {
        next_transition =  [1, 0];
    }
    else if ((key == UP_KEY) && (!downDirection) && (tempY > 1)) {
        next_transition =  [0, -1];
    }
    else if ((key == DOWN_KEY) && (!upDirection) && (tempY < json_file.field[0].length -2)) {
        next_transition =  [0, 1];

    }        
};   



//Makes sure the bus doesn't move if a key isn't pressed down
// Bus moves on its own
//onkeyup = function(e) {
//    go = true;
//};
