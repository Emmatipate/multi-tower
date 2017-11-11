#!/usr/bin/env python3
from aiohttp import web
import vec
import entities
import socketio
import asyncio
import threading
import time
import urllib.parse
import random
import json
import pdb

TICK_TIME = 0.1

SPAWN_DISTANCE = 50

async def run(app):
    try:
        while True:
            await timer_tick()
            await asyncio.sleep(TICK_TIME, loop=app.loop)
    except asyncio.CancelledError:
        pass

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

board_lock = threading.Lock()

# player_name -> Entity
castles = {}

# uuid -> Entity
board_entities = {}

# pos -> [uuid]
board = {}

# name -> Player
players = {}

# uuid -> (Entity, ticks since last fired)
towers = {}

async def update_player(player):
    player.spawn_timer -= 1
    if player.spawn_timer <= 0:
        player.spawn_timer = 0

        castle = castles[player.name]

        # TODO: find optimal side to spawn on given target
        spawn_x = castle.x + 1
        spawn_y = castle.y

        minion = entities.Entity(x, y, "minion", player.name)
        board_add_entity(tower)

        await broadcast_message('entity_created', tower.to_list())


async def timer_tick():
    board_lock.acquire()
    await send_tick()
    for player_name in players:
        await update_player(players[player_name])
    for uid in towers:
        tower, ticks = towers[uid]
        ticks += TICK_TIME * TOWER_FREQUENCIES[tower.typ]
        if ticks >= 1 / TICK_TIME:
            await fire_tower(tower)
            ticks = 0
        towers[uid] = (tower, ticks)

    board_lock.release()


async def fire_tower(tower):
    pos = tower.position_tuple()


def is_castle_position_free(pos):
    x, y = pos
    for castle in castles.values():
        if x == castle.x and y == castle.y:
            return False
    return True


def find_player(sid):
    for player in players.values():
        if sid in player.sids:
            return player


def board_add_entity(entity):
    pos = entity.position_tuple()
    uid = entity.uid
    if pos in board:
        board[pos].append(uid)
    else:
        board[pos] = [pos]
    board_entities[uid] = entity


def board_move_entity(uid, dest_pos):
    board_remove_entity(uid)
    board_add_entity(uid, dest_pos)
    x, y = dest_pos
    board_entities[uid].x = x
    board_entities[uid].y = y


def board_remove_entity(uid):
    found_pos = None
    for pos, ids in board.items():
        if uid in ids:
            found_pos = pos
    assert found_pos is not None
    board[found_pos].remove(uid)
    if not board[found_pos]:
        del board[found_pos]
    del board_entities[uid]


def generate_castle_position():
    if not castles:
        return (0, 0)
    it = 0
    while True:
        r1 = random.randint(-1 - it, 1 + it)
        r2 = random.randint(-1 - it, 1 + it)
        direction = (r1*SPAWN_DISTANCE, r2*SPAWN_DISTANCE)
        for castle in castles.values():
            pos = castle.position_tuple()
            new_pos = vec.add(direction, pos)
            if is_castle_position_free(pos):
                return new_pos
        it += 1
        # print(castles)


async def send_tick():
    await broadcast_message('tick', '')


async def assign_castle(player_name):
    x, y = generate_castle_position()
    castle = entities.Entity(x, y, 'castle', player_name)
    castles[player_name] = castle
    board_add_entity(castle)
    await broadcast_message('entity_created', [castle.uid, x, y, 'castle', 100, 1, player_name])


async def broadcast_message(message_type, data, sid=None):
    await sio.emit(message_type, data=json.dumps(data), room=sid)


async def index(request):
    """Serve the client-side application."""
    with open('../public/index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')


async def send_world_to_player(sid):
    for castle in castles.values():
        await broadcast_message('entity_created', castle.to_list(), sid)
        print("sent world to", sid)


@sio.on('connect')
async def connect(sid, environ):
    board_lock.acquire()
    query = urllib.parse.parse_qs(environ['QUERY_STRING'])
    print("connect ", sid, query)
    name = query['name'][0]

    print('NAME: ', name)
    print('PLAYERS: ', players)
    if name not in players:
        players[name] = entities.Player(name, [sid])
        await assign_castle(name)
        await broadcast_message('new_player', name)
    else:
        players[name].sids.append(sid)
    await send_world_to_player(sid)
    board_lock.release()


@sio.on('request_tower')
async def on_request_tower(sid, data):
    print("Tower requested: ", data)

    x, y, typ = data
    player = find_player(sid)
    tower = entities.Entity(x, y, typ, player.name)
    board_add_entity(tower)
    towers[tower.uid] = (tower, 0)

    await broadcast_message('entity_created', tower.to_list())


@sio.on('disconnect')
def disconnect(sid):
    board_lock.acquire()
    player = find_player(sid)
    player.sids.remove(sid)
    board_lock.release()
    print('disconnect ', sid)


app.router.add_get('/', index)
app.router.add_static('/', '../public')


async def start_background_tasks(app):
    app['ticker'] = app.loop.create_task(run(app))


async def cleanup(app):
    app['ticker'].cancel()
    await app['ticker']


def start_server():
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup)
    web.run_app(app)


if __name__ == '__main__':
    start_server()

