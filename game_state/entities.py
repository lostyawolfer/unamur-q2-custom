import math
from enum import Enum, auto


STATS = {
    'barbarian': {
        'health': 15,
        'damage': 2,
        'abilities': ['energise', 'stun'],
        'display': 'B'
    },
    'healer': {
        'health': 10,
        'damage': 2,
        'abilities': ['invigorate', 'immunise'],
        'display': 'H'
    },
    'mage': {
        'health': 10,
        'damage': 2,
        'abilities': ['fulgura', 'ovibus'],
        'display': 'M'
    },
    'rogue': {
        'health': 10,
        'damage': 3,
        'abilities': ['reach', 'burst'],
        'display': 'R'
    }
}


entities = []
heroes = []
creatures = []
players = []

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Position:
    x: int
    y: int

    def __repr__(self):
        return f'({self.x}, {self.y})'


class OutOfMapError(ValueError):
    def __init__(self, pos: Position):
        super().__init__(f'({pos.x}, {pos.y}) is outside the map')

class Entity:
    name: str
    pos: Position
    max_health: int
    health: int
    damage: int
    effects: list[Effect]
    def __init__(self, name, pos, max_health, health, damage):
        if not (name.isalpha() and name.islower()): raise BadEntityNameError
        for entity in entities:
            if entity.name == name: raise EntityExistsError
        self.name = name
        self.pos = pos
        self.max_health = max_health
        self.health = health
        self.damage = damage
        entities.append(self)

    def delete(self):
        entities.remove(self)

    def heal(self, amount: int):
        if amount < 0: raise ValueError('cannot inflict negative healing')
        self.health = min(self.health+amount, self.max_health)

    def hurt(self, amount: int):
        if amount < 0: raise ValueError('cannot inflict negative damage')
        self.health = max(self.health-amount, 0)

    def move(self, pos: Position):
        if not is_legal_position(pos): raise OutOfMapError(pos)
        self.pos = pos

    def apply_effect(self, effect: Effect):
        if effect in self.effects: raise ValueError(f"{self.name} already has {effect}")
        self.effects.append(effect)

    def remove_effect(self, effect: Effect):
        if effect not in self.effects: raise ValueError(f"{self.name} already doesn't have {effect}")
        self.effects.remove(effect)

    def clear_effects(self):
        self.effects = []

class Creature(Entity):
    range: int
    def __init__(self, name: str, pos: Position, health: int, damage: int, range: int):
        super().__init__(name, pos, health, health, damage)
        self.range = range
        creatures.append(self)

    def delete(self):
        creatures.remove(self)
        super().delete()



class GameNotInitializedError(Exception):
    pass


class GameInitializedTwiceError(Exception):
    pass


class Game:
    _instance = None
    _initialized = False
    map_size: Position
    win_condition: int
    spawn: list[Position]
    spur: list[Position]

    def __new__(cls, *args, **kwargs):
        if not cls._instance: cls._instance = super().__new__(cls)
        return cls._instance

    def __getattribute__(self, name):
        if name in ("_instance", "_initialized", "init", "readfile"):
            return super().__getattribute__(name)
        if not super().__getattribute__("_initialized"):
            raise GameNotInitializedError
        return super().__getattribute__(name)

    def __repr__(self):
        return f'map {self.map_size} - wc {self.win_condition} - spawn {self.spawn} - spur {self.spur}'

    def init(self, map_size, win_condition, spawn, spur):
        if self._initialized: raise GameInitializedTwiceError
        self.map_size = map_size
        self.win_condition = win_condition
        self.spawn = spawn
        self.spur = spur
        self._initialized = True

    def readfile(self, path: Path | str):
        if type(path) == str: path = Path(path)
        with open(path) as filedata:
            file = filedata.readlines()

        data = {}
        sect_name = ''
        for line in file:
            if line[-2] == ':':
                sect_name = line[:-2]
                data[sect_name] = []
            else:
                data[sect_name].append(line[:-1])
        print(data)

        def str_to_pos(pos: str) -> Position:
            pos = pos.split(' ')
            pos = [int(i) for i in pos]
            return Position(pos[0], pos[1])

        map_size = str_to_pos(data['map'][0])
        win_condition = (data['map'][0].split()[2])
        spawn = [str_to_pos(pos) for pos in data['spawn']]
        spur = [str_to_pos(pos) for pos in data['spur']]
        creature_list = data['creatures']
        self.init(map_size, win_condition, spawn, spur)
        for i in creature_list:
            Creature(name=i.split()[0],
                     pos=Position(i.split()[1], i.split()[2]),
                     health=int(i.split()[3]),
                     damage=int(i.split()[4]),
                     range=int(i.split()[5]),
                     )


def is_legal_position(pos: Position) -> bool:
    game = Game()
    if not (game.map_size.x >= pos.x >= 1): return False
    if not (game.map_size.y >= pos.y >= 1): return False
    return True

class HeroClass(Enum):
    # (display, health, damage, abilities)
    BARBARIAN = ('B', 15, 2, ['energise', 'stun'])
    HEALER = ('H', 10, 2, ['invigorate', 'immunise'])
    MAGE = ('M', 10, 2, ['fulgura', 'ovibus'])
    ROGUE = ('R', 10, 3, ['reach', 'burst'])

    hcls: str
    display: str
    base_health: int
    base_damage: int
    abilities: list[str]

    def __init__(self, display, health, damage, abilities):
        self.display = display
        self.base_health = health
        self.base_damage = damage
        self.abilities = abilities


class Effect(Enum):
    ENERGIZED = auto()
    STUNNED = auto()
    IMMUNISED = auto()
    OVIBUS = auto()


class EntityCreationError(Exception):
    pass

class EntityExistsError(EntityCreationError):
    pass

class BadEntityNameError(EntityCreationError):
    pass


class Hero(Entity):
    level: int
    hcls: HeroClass
    def __init__(self, name: str, spawnpos: Position, hcls: HeroClass):
        super().__init__(name, spawnpos, hcls.base_health, hcls.base_health, hcls.base_damage)
        self.level = 1
        heroes.append(self)

    def delete(self):
        heroes.remove(self)
        super().delete()

    def level_up(self):
        self.level += 1
        self.max_health = math.ceil(self.max_health * 1.4)
        self.damage = math.ceil(self.damage * 1.6)

    @property
    def owned_abilities(self) -> list[str]:
        return self.hcls.abilities[:self.level-1]


def clear_all_effects():
    for entity in entities:
        entity.clear_effects()


def remove_effect_from_all(effect: Effect):
    for entity in entities:
        try:
            entity.remove_effect(effect)
        except ValueError:
            pass


class Player:
    name: str
    heroes: list[Hero] = []
    turns_on_spur: int = 0
    def __init__(self, name: str):
        self.name = name
        players.append(self)

    def add_hero(self, hero: Hero):
        self.heroes.append(hero)

    def increment_spur(self):
        self.turns_on_spur += 1

    def reset_spur(self):
        self.turns_on_spur = 0


def get_hero(name: str) -> Hero | None:
    for hero in heroes:
        if hero.name == name: return hero
    return None


def get_creature(name: str) -> Creature | None:
    for creature in creatures:
        if creature.name == name: return creature
    return None


def get_hero_owner(hero: Hero) -> Player | None:
    for player in players:
        if hero in player.heroes: return player
    return None