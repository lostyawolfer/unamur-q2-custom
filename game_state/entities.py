import math
from enum import Enum, auto
from pathlib import Path
from .position import Position, OutOfMapError, convert_string as str_to_pos


class EntityCreationError(Exception):
    pass

class EntityExistsError(EntityCreationError):
    pass

class BadEntityNameError(EntityCreationError):
    pass

class GameInitializedTwiceError(Exception):
    pass


def is_legal_position(pos: Position) -> bool:
    game = Game()
    if not (game.map_size.x >= pos.x >= 1): return False
    if not (game.map_size.y >= pos.y >= 1): return False
    return True


# ----------------------


class Effect(Enum):
    ENERGIZED = auto()
    STUNNED = auto()
    IMMUNISED = auto()
    OVIBUS = auto()


class Entity:
    effects: list[Effect]
    def __init__(self, name, pos, max_health, damage):
        if not (name.isalpha() and name.islower()): raise BadEntityNameError
        self.name = name
        self.pos = pos
        self.max_health = max_health
        self.health = max_health
        self.damage = damage
        self.effects = []
    def __repr__(self):
        return f'{self.name} @ {self.pos} - {self.health}/{self.max_health}'

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
    def __init__(self, name: str, pos: Position, health: int, damage: int, damage_range: int):
        super().__init__(name, pos, health, damage)
        self.damage_range = damage_range
    def __repr__(self):
        return f'creature | {super().__repr__()}'


class HeroClass(Enum):
    # (display, health, damage, abilities)
    barbarian = ('B', 15, 2, ['energise', 'stun'])
    healer = ('H', 10, 2, ['invigorate', 'immunise'])
    mage = ('M', 10, 2, ['fulgura', 'ovibus'])
    rogue = ('R', 10, 3, ['reach', 'burst'])

    display: str
    base_health: int
    base_damage: int
    abilities: list[str]

    def __init__(self, display, health, damage, abilities):
        self.display = display
        self.base_health = health
        self.base_damage = damage
        self.abilities = abilities



class Hero(Entity):
    level: int
    hcls: HeroClass
    def __init__(self, name: str, spawnpos: Position, hcls: HeroClass):
        super().__init__(name, spawnpos, hcls.base_health, hcls.base_damage)
        self.level = 1
        self.hcls = hcls

    def __repr__(self):
        return f'hero | {super().__repr__()} - {self.hcls}'

    def level_up(self):
        self.level += 1
        self.max_health = math.ceil(self.max_health * 1.4)
        self.damage = math.ceil(self.damage * 1.6)

    @property
    def owned_abilities(self) -> list[str]:
        return self.hcls.abilities[:self.level-1]


class Player:
    name: str
    heroes: list[Hero]
    turns_on_spur: int
    def __init__(self, name: str, heroes: list[Hero]):
        self.name = name
        self.heroes = heroes
        self.turns_on_spur = 0

    def increment_spur(self):
        self.turns_on_spur += 1

    def reset_spur(self):
        self.turns_on_spur = 0



class Game:
    _instance = None
    _initialized = False
    map_size: Position
    win_condition: int
    spawn: list[Position]
    spur: list[Position]

    entities: list[Entity] = []
    creatures: list[Creature] = []
    heroes: list[Creature] = []
    players: list[Player] = []

    def __new__(cls, *args, **kwargs):
        if not cls._instance: cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return f'map {self.map_size} - wc {self.win_condition} - spawn {self.spawn} - spur {self.spur}'


    def reg_creature(self, creature: Creature):
        self.creatures.append(creature)
        self.entities.append(creature)

    def reg_player(self, player: Player):
        self.heroes += player.heroes
        self.entities += player.heroes
        self.players.append(player)


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

        map_size = str_to_pos(data['map'][0])
        win_condition = (data['map'][0].split()[2])
        spawn = [str_to_pos(pos) for pos in data['spawn']]
        spur = [str_to_pos(pos) for pos in data['spur']]
        creature_list = data['creatures']
        self.init(map_size, win_condition, spawn, spur)
        for i in creature_list:
            self.reg_creature(Creature(name=i.split()[0],
                     pos=Position(i.split()[1], i.split()[2]),
                     health=int(i.split()[3]),
                     damage=int(i.split()[4]),
                     damage_range=int(i.split()[5])))


def get_hero_owner(hero: Hero) -> Player | None:
    game = Game()
    for player in game.players:
        for phero in player.heroes:
            if hero == phero:
                return player
    return None