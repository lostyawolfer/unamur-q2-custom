from game_state import *

game = Game()
game.readfile('maps/test.lon')
print(game)
print(game.entities)


for i in range(2):
    new_player_name = input("[new player] what's your name?: ")
    new_player_heroes = []
    for j in range(4):
        new_hero_name = input(f"{new_player_name}, name your hero #{j+1}: ")
        new_hero_class = input(f"{new_player_name}, what's {new_hero_name}'s class?: ")
        new_player_heroes.append(Hero(new_hero_name, game.spawn[i], HeroClass[new_hero_class]))
    new_player = Player(new_player_name, new_player_heroes)
    game.reg_player(new_player)

print(game.entities)

