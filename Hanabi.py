"""
@author: Weibo zhao
"""
import time

import HanabiClasses
from HanabiClasses import *
from AI import *


class Error(Exception):
    pass


def Menu(options):
    """
    Menu displays a menu of options, ask the user to choose an item
    and returns the number of the menu item chosen.
    """

    # Display menu options
    for i in range(len(options)):
        print("{:d}. {:s}".format(i + 1, options[i]))
    # Get a valid menu choice
    choice = 0
    while not (np.any(choice == np.arange(len(options)) + 1)):
        try:
            choice = float(input("Please choose a menu item: "))
            if choice > len(options) or choice < 0:
                print('Please, provide a correct integer input value between 0 and {}'.format(len(options)))
        except:
            print('Please, provide a correct number input value')

    return choice


def start():
    global default, PvA

    cardsDistribution = [1, 1, 1, 2, 2, 3, 3, 4, 4, 5]

    print("How do you want to play the game?")
    choicePvA = ["Player & AI (test playing with the AI)",
                 "Player & Player (in case you would like to test the game engine independently of the AI)"]
    PvAOption = Menu(choicePvA)

    if PvAOption == 1:
        PvA = True
    elif PvAOption == 2:
        PvA = False

    # default set up?
    print("Do you want to use the default game configuration?")
    choiceSetUp = ["Default set-up", "Manual set-up"]
    defaultOption = Menu(choiceSetUp)

    if defaultOption == 1:
        default = True
    elif defaultOption == 2:
        default = False

    if default:
        name1 = input("Name of first player: ")
        if PvA:
            name2 = "AI"
        else:
            name2 = input("Name of second player: ")
        numberOfCards = 4
        numberOfColors = 2
        maxHTokens = 8
        maxPTokens = 3
        green = ';'.join([str(1), str(32), str(28)])
        print("")
        print('\x1b[%smDefault configurations: \x1b[0m' % (green))
        print("\x1b[%sm-4 cards in hand\x1b[0m" % (green))
        print("\x1b[%sm-2 colors in the game\x1b[0m" % (green))
        print("\x1b[%sm-Card distribution: [1, 1, 1, 2, 2, 3, 3, 4, 4, 5].\x1b[0m" % (green))
        print("\x1b[%sm-total number of cards in the DeskCards: 20\x1b[0m" % (green))
        print("\x1b[%sm-Max number of Hint tokens: 8\x1b[0m" % (green))
        print("\x1b[%sm-Max number of Penalty tokens: 3\x1b[0m" % (green))


    else:
        name1 = input("Name of first player: ")
        if PvA:
            name2 = "AI"
        else:
            name2 = input("Name of second player: ")
        numberOfCards = int(input("How many cards per player? "))
        numberOfColors = int(input("How many colors? min 1 color;max 5 colors"))
        while numberOfColors <= 0 or numberOfColors > 5:
            numberOfColors = int(input("How many colors? min 1 color;max 5 colors"))
        print("Card distribution: [1, 1, 1, 2, 2, 3, 3, 4, 4, 5].")
        maxHTokens = int(input("Choose max number of Hint Tokens: "))
        maxPTokens = int(input("Choose max number of Penalty Tokens: "))

    # create Player objects
    Player1 = Player(name1, 1, numberOfCards)
    Player2 = Player(name2, 2, numberOfCards)

    # create DeskCards object
    DeskCards = HanabiClasses.DeskCards(numberOfColors, cardsDistribution)

    # create Played Pile object
    PlayedCards = HanabiClasses.PlayedCards(numberOfColors)

    # create Discard Pile object
    DiscardCards = HanabiClasses.DiscardCards([])

    # create Tokens objects
    hintTokens = HintTokens(maxHTokens, maxHTokens)
    penaltyTokens = PenaltyTokens(0, maxPTokens)

    # create final variables for state
    turn = 1
    parent = []

    # create a list of states and store the starting state
    states = []
    Player1.drawHand(DeskCards)
    Player2.drawHand(DeskCards)
    initialState = State(Player1, Player2, DeskCards, PlayedCards, DiscardCards, hintTokens, penaltyTokens, turn, parent, PvA)
    states.append(initialState)

    return states


def playRound(states, parameter):
    # if the state is the last one it is the init
    global human, activePlayer, otherPlayer
    if isinstance(states, list):
        initialState = states[-1]
    else:
        initialState = states

    if initialState.turn == 1:
        activePlayer = initialState.Player1
        otherPlayer = initialState.Player2
        human = True
    elif initialState.turn == 2:
        activePlayer = initialState.Player2
        otherPlayer = initialState.Player1
        if initialState.PvA:
            human = False
        else:
            human = True

    actionOptions = ["Play a card", "Give a hint", "Discard a card", "Quit"]

    # ask for user input if human
    # get input from computer if AI

    fo = open('AI steps.txt', 'a+')

    while True:

        # AI: disable human = true, if you want to test with AI
        # human = True
        if human:
            print("{}'s turn, choose an action: ".format(activePlayer.name))
            choiceAction = Menu(actionOptions)
        else:
            begin = time.time()

            solver = Solver(2)

            space = BeliefSpace(states[-1], len(initialState.AI.cards))
            choiceAction, parameter = solver.search_tree(space.states, states[-1])
            end = time.time()
            print("spent time is ", int((end - begin) * 1000))

            # Record the action time and action code
            if choiceAction == 1:
                action = 'Play'
            elif choiceAction == 2:
                action = 'Hint'
            else:
                action = 'Discard'
            fo.write(str(int((end - begin) * 1000)) + 'ms -- AI action:' + action + '\n')

        # PLAY
        if choiceAction == 1:
            if human:
                cardChoice = int(getCard(activePlayer, None, "play"))
            else:
                cardChoice = parameter
            if cardChoice != len(activePlayer.cards):
                newState = Actions.play(initialState, cardChoice)
                break
        # HINT
        elif choiceAction == 2:
            if human:
                cardChoice = int(getCard(activePlayer, otherPlayer, "hint"))
                if cardChoice != len(activePlayer.cards):
                    hintType, hint = getHint(activePlayer, otherPlayer, cardChoice)
                    if hintType != "Back":
                        newState = Actions.hint(initialState, hintType, hint)
                        break
            else:
                hintType, hint = parameter
                newState = Actions.hint(initialState, hintType, hint)
                break

        # DISCARD
        elif choiceAction == 3:
            if human:
                cardChoice = int(getCard(activePlayer, None, "discard"))
            else:
                cardChoice = parameter

            if cardChoice != len(activePlayer.cards):
                newState = Actions.discard(initialState, cardChoice)
                break

        # QUIT
        elif choiceAction == 4:
            raise Error("Program will terminate")

    if newState == None:
        print("Choose another option!")
        newState = initialState

    if isinstance(states, list):
        states.append(newState)
    else:
        states = newState

    return states

def getCard(activePlayer, otherPlayer, action):
    if action == "hint":
        print("{}, what card do you want to {}?".format(activePlayer.name, action))
        cardOptions = []
        for i in range(len(otherPlayer.cards)):
            word2 = str(otherPlayer.cards[i].number)
            word1 = otherPlayer.cards[i].color

            if otherPlayer.cards[i].colorHinted:
                word1 = word1 + "*"
            if otherPlayer.cards[i].numberHinted:
                word2 = word2 + "N"

            cardInHand = ("Position of the card in hand: {}, color: {}, number: {}".format(i + 1, word1, word2))
            cardOptions.append(cardInHand)
        cardOptions.append("Back")
        choiceCard = Menu(cardOptions)
        return choiceCard - 1
    else:
        print("{}, what card do you want to {}?".format(activePlayer.name, action))
        cardOptions = []
        for i in range(len(activePlayer.cards)):
            word1 = "?"
            word2 = "?"
            if activePlayer.cards[i].colorHinted:
                word1 = activePlayer.cards[i].color
            if activePlayer.cards[i].numberHinted:
                word2 = str(activePlayer.cards[i].number)
            cardInHand = ("Position of the card in hand: {}, color: {}, number: {}".format(i + 1, word1, word2))
            cardOptions.append(cardInHand)
        cardOptions.append("Back")
        choiceCard = Menu(cardOptions)
        return choiceCard - 1


def getHint(activePlayer, otherPlayer, cardChoice):
    global hintType, hint
    cardHinted = otherPlayer.cards[cardChoice]
    print("")
    print("{}, what hint would you like to give? (All cards that share that attribute will also be hinted)".format(
        activePlayer.name))
    hintOptions = ["color" + " ({})".format(cardHinted.color), "number" + " ({})".format(cardHinted.number), "Back"]
    choiceHint = Menu(hintOptions)

    if choiceHint == 1:
        hintType = "color"
        hint = cardHinted.color
    elif choiceHint == 2:
        hintType = "number"
        hint = cardHinted.number
    elif choiceHint == 3:
        hintType = "Back"
        hint = None

    return hintType, hint





def playGame(states):
    global finalScoce, finalScore
    if states is None:
        states = start()

    fo = open('AI steps.txt', 'a+')

    while True:
        if states[-1].human:
            states[-1].display()
        else:
            print("")
            print("\033[34m*********************\033[0m")
            print("\033[34m*    AI Playing     *\033[0m")
            print("\033[34m*********************\033[0m")
        try:
            # AI: action and parameter must be defined when the AI is playing
            states = playRound(states, None)
            print("Round over.")

        except Error:
            print("User has chosen to Quit.")
            print("Program stop")
            break

        gameEnd, message, finalScore = states[-1].checkGoal()
        if gameEnd:
            print("")
            print("\033[32m******************************************\033[0m")
            print(message)
            print("\033[32m******************************************\033[0m")
            break
    try:
        fo.write('score: ' + str(finalScore) + '\n')
        fo.close()
    except:
        print('Program stop')

    return states


if __name__ == "__main__":
    playGame(None)
