"""
@author: weibo zhao
"""
import numpy as np
from random import *
import copy

global red, blue, green, yellow, white
red = ';'.join([str(1), str(31), str(28)])
blue = ';'.join([str(1), str(34), str(28)])
green = ';'.join([str(0), str(30), str(42)])
yellow = ';'.join([str(1), str(30), str(43)])
white = ';'.join([str(1), str(30), str(47)])


class State:
    def __init__(self, Player1, Player2, DeskCards, PlayedCards, DiscardCards, hintTokens, penaltyTokens, turn, parent,
                 PvA):
        self.Player1 = Player1
        self.Player = self.Player1
        self.Player2 = Player2
        self.AI = self.Player2
        self.DeskCards = DeskCards
        self.PlayedCards = PlayedCards
        self.DiscardCards = DiscardCards
        self.hintTokens = hintTokens
        self.penaltyTokens = penaltyTokens
        # above is class  below is basic data type
        self.turn = turn
        self.score = 0
        self.maxScore = DeskCards.numberOfColors * 5
        self.PvA = PvA

        if PvA:
            if turn == 1:
                self.human = True
            else:
                self.human = False
        else:
            self.human = True

        # this is used in action class
        self.parent = parent
        self.depth = 0
        self.value = 0

    def switchTurn(self):
        self.turn = self.turn % 2 + 1
        if self.PvA:
            self.human = not self.human

    def updateScore(self):
        self.score = 0
        for s in self.PlayedCards.piles:
            self.score = len(s) + self.score

    def display(self):

        # show score, tokens and cards left in DeskCards
        self.updateScore()
        print("")
        print("---------------------------------Token and DeskCards information------------------------------------------")
        print("")
        print(
            "Score : {}. Hint tokens left : {}/{}, Penalty tokens used : {}/{}. Cards left in the DeskCards : {}.\n".format(
                self.score, self.hintTokens.tokenNumber, self.hintTokens.tokenMax,
                self.penaltyTokens.tokenNumber, self.penaltyTokens.tokenMax, len(self.DeskCards.cards)))

        colorsList = ["red", "blue", "green", "yellow", "white"]
        colorsVisualList = [red, blue, green, yellow, white]

        # show cards in the played pile
        if self.PlayedCards.numberOfColors > 0:
            print("Played Cards : \x1b[%sm %s \x1b[0m" % (red, self.PlayedCards.convertList(0)), end=" ")
        if self.PlayedCards.numberOfColors >= 2:
            print('\x1b[%sm %s \x1b[0m' % (blue, self.PlayedCards.convertList(1)), end=" ")
        if self.PlayedCards.numberOfColors >= 3:
            print('\x1b[%sm %s \x1b[0m' % (green, self.PlayedCards.convertList(2)), end=" ")
        if self.PlayedCards.numberOfColors >= 4:
            print('\x1b[%sm %s \x1b[0m' % (yellow, self.PlayedCards.convertList(3)), end=" ")
        if self.PlayedCards.numberOfColors == 5:
            print('\x1b[%sm %s \x1b[0m' % (white, self.PlayedCards.convertList(4)))
        print("")

        # show cards in the discarded pile
        print("Discarded Cards : ", end=" ")
        discardedPrint = self.DiscardCards.convertList()
        for card in discardedPrint:
            print(card, end="")
        print("")
        print("")

        players = [self.Player1, self.Player2]
        # show cards in the other player's hand
        otherPlayer = players[self.turn % 2]
        print("Cards in the other player hand:")

        for card in otherPlayer.cards:
            indexColor = colorsList.index(card.color)
            color = colorsVisualList[indexColor]
            number = str(card.number)
            if card.colorHinted:
                color += "*"
            if card.numberHinted:
                number += "N"
            print('\x1b[%sm %s \x1b[0m' % (color, number), end=" ")
        print("")

        # show cards in your own hand
        activePlayer = players[self.turn - 1]
        print("Cards in your hand:")
        for card in activePlayer.cards:
            indexColor = colorsList.index(card.color)
            number = "?"
            color = ';'.join([str(7), str(30), str(47)])
            if card.numberHinted:
                number = str(card.number)
                number += "N"
            if card.colorHinted:
                color = colorsVisualList[indexColor]
                color += "*"

            print('\x1b[%sm %s \x1b[0m' % (color, number), end=" ")
        print("")
        print("")

    def checkGoal(self):
        global color, message, finalMessage
        self.updateScore()
        score = self.score
        maxScore = self.maxScore
        cardsLeft = len(self.DeskCards.cards)
        penalty = self.penaltyTokens.tokenNumber
        maxPenalty = self.penaltyTokens.tokenMax

        if score >= maxScore:
            outcome = True
            message = "Congratulations! You've reached the maximum score of {}, game will terminate".format(maxScore)
            color = green
        elif cardsLeft == 0:
            outcome = True
            message = "Game Over! There are no cards left in the DeskCards. Your final score is {}, game will terminate".format(
                score)
            color = red
        elif penalty == maxPenalty:
            outcome = True
            message = "Game Over! You've reached the maximum of {} penalty tokens. Your final score is {}, game will " \
                      "terminate".format(
                penalty, score)
            color = red
        elif self.noMoreFirework():
            outcome = True
            message = "Game Over! You cannot build any more fireworks with the cards that are left! Your final score " \
                      "is {}, game will terminate".format(
                score)
            color = red
        else:
            outcome = False
            finalMessage = None

        if outcome == True:
            finalMessage = ('\x1b[%sm %s \x1b[0m' % (color, message))

        return outcome, finalMessage, score

    def noMoreFirework(self):
        DiscardCards = self.DiscardCards
        PlayedCards = self.PlayedCards
        cardsDistribution = self.DeskCards.cardsDistribution
        numberOfColors = self.DeskCards.numberOfColors
        colors = np.array(["red", "blue", "green", "yellow", "white"])[:numberOfColors]
        outcome = True
        for i in range(len(colors)):
            pile = PlayedCards.piles[i]
            color = colors[i]
            if len(pile) == 0:
                nextNumber = 1
            else:
                nextNumber = pile[-1].number + 1
            if nextNumber > 5:
                continue
            totalAmount = cardsDistribution.count(nextNumber)
            discardedAmount = 0
            for card in DiscardCards.cards:
                if card.color == color and card.number == nextNumber:
                    discardedAmount += 1
            if totalAmount == discardedAmount:
                pass
            else:
                outcome = False
                break

        return outcome


class Actions:

    def __init__(self):
        self.PlayedCards = None
        self.DeskCards = None
        self.DiscardCards = None
        self.penaltyTokens = None
        self.hintTokens = None
        self.Player2 = None
        self.turn = None
        self.human = None
        self.depth = None
        self.Player1 = None


    def hint(self, hintType, hint):
        # hintType: String. Can be "number" or "color"
        # hint: String ("red","green",...) or Int ("1","2","3","4" or "5")

        # initializing variables (extracted from state)
        global otherPlayer
        newState = copy.deepcopy(self)
        newState.parent = self
        newState.depth = self.depth + 1
        human = newState.human

        if newState.turn == 1:
            otherPlayer = newState.Player2
        elif newState.turn == 2:
            otherPlayer = newState.Player1
        hintTokens = newState.hintTokens

        if hintTokens.tokenNumber == 0:
            if human:
                print("\033[31mError. Number of Hint Tokens is 0. You need discard to get hit token first.\033[0m")
            return None

        if otherPlayer.allHintsGiven(hint, hintType):
            if human:
                print("\033[31mError. Hint already given. You cannot make that hint.\033[0m")
            return None

        for i in range(len(otherPlayer.cards)):
            if hintType == "color":
                if otherPlayer.cards[i].color == hint:
                    otherPlayer.cards[i].colorHinted = True
            elif hintType == "number":
                if otherPlayer.cards[i].number == hint:
                    otherPlayer.cards[i].numberHinted = True

        hintTokens.tokenRemove(human)
        if human:
            print("You gave the hint: {}.".format(hint))

        newState.switchTurn()

        return newState

    def discard(initialState, cardPosition):
        # cardPosition: Int. Index of the card you want to discard from your hand.

        # initializing variables (extracted from state)
        global activePlayer
        newState = copy.deepcopy(initialState)
        newState.parent = initialState
        newState.depth = initialState.depth + 1
        human = newState.human

        if newState.turn == 1:
            activePlayer = newState.Player1
        elif newState.turn == 2:
            activePlayer = newState.Player2
        hintTokens = newState.hintTokens


        DeskCards = newState.DeskCards
        DiscardCards = newState.DiscardCards

        if hintTokens.tokenNumber == hintTokens.tokenMax:
            if human:
                print("\033[31mError. Number of Hint Tokens is maxed. You need to use hint token first.\033[0m")
            return None

        discardedCard = activePlayer.cards[cardPosition]
        DiscardCards.addCard(discardedCard)
        if human:
            print("You've discarded a card. Color: {}, number: {}.".format(discardedCard.color, discardedCard.number))

        if len(DeskCards.cards) > 0:
            activePlayer.draw(DeskCards, cardPosition)
        else:
            activePlayer.cards.pop(cardPosition)
        hintTokens.tokenAdd(human)

        newState.switchTurn()

        return newState

    def play(self, cardPosition):
        # cardPosition: Int. Index of the card you want to play from your hand.

        # initializing variables (extracted from state)
        global activePlayer
        newState = copy.deepcopy(self)
        newState.parent = self
        newState.depth = self.depth + 1
        human = newState.human

        if newState.turn == 1:
            activePlayer = newState.Player1
        elif newState.turn == 2:
            activePlayer = newState.Player2
        DeskCards = newState.DeskCards

        playedCard = activePlayer.cards[cardPosition]

        # check if the card was correct somehow
        # use functions from the playPile
        verif = newState.PlayedCards.addCard(playedCard, human)

        if verif == False:
            newState.penaltyTokens.tokenAdd(human)
            newState.DiscardCards.addCard(playedCard)
            if human:
                red = ';'.join([str(1), str(31), str(28)])
                message = ("\033[31mYou got a penalty token!\033[0m")
                print("\x1b[%sm %s \x1b[0m" % (red, message))

        if len(DeskCards.cards) > 0:
            activePlayer.draw(DeskCards, cardPosition)
        else:
            activePlayer.cards.pop(cardPosition)

        newState.switchTurn()

        return newState

    def switchTurn(self):
        pass


class Card:

    # Initialization functions

    def __init__(self, color, number):
        self.color = color
        self.number = number
        self.colorHinted = False
        self.numberHinted = False

    # Visualization functions

    def sayInfo(self):
        print("Color: {}, number: {}.".format(self.color, self.number))

    def storeInfo(self):
        return ("Color: {}, number: {}.".format(self.color, self.number))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Player:

    # Initialization functions

    def __init__(self, name, order, numberOfCards):
        self.name = name
        self.order = order
        self.cards = [Card(None, 0)] * numberOfCards
        self.numberOfCards = numberOfCards


    def setCards(self, cards):
        self.cards(cards)

    def drawHand(self, DeskCards):

        for i in range(len(self.cards)):
            self.draw(DeskCards, i)

    # DISCARD

    def draw(self, DeskCards, cardPosition):
        newCard = DeskCards.removeRandom()
        self.cards[cardPosition] = newCard
        return newCard

    # HINT
    '''
    @para hintType = color/number
    @para hint = 1,2,3,4/yellow,red,blue
    check all hint has been given in a hintType
    '''
    def allHintsGiven(self, hint, hintType):
        if hint is None:
            for i in range(len(self.cards)):
                if (self.cards[i].colorHinted == False) or (self.cards[i].numberHinted == False):
                    return False
            return True
        elif hintType == "color":
            for i in range(len(self.cards)):
                if (self.cards[i].color == hint) and (self.cards[i].colorHinted == False):
                    return False
            return True

        elif hintType == "number":
            for i in range(len(self.cards)):
                if (self.cards[i].number == hint) and (self.cards[i].numberHinted == False):
                    return False
            return True
 

    # Visualization functions

    def storeInfo(self):
        # Declaring rows
        N = len(self.cards)
        # Declaring columns
        M = 2
        # using list comprehension
        # to initializing matrix
        cardMatrix = [[0 for i in range(M)] for j in range(N)]

        for i in range(len(self.cards)):
            number = str(self.cards[i].number)
            color = str(self.cards[i].color)
            if self.cards[i].numberHinted:
                number = number + "N"
            if self.cards[i].colorHinted:
                color = color + "*"

            cardMatrix[i][0] = number
            cardMatrix[i][1] = color
        return cardMatrix


class DeskCards:

    # Initialization functions

    def __init__(self, numberOfColors, cardsDistribution):
        # var cardsDistribution = int list of 1,2,3,4,5s
        self.numberOfColors = numberOfColors
        # var numberOfColors = int
        self.cardsDistribution = cardsDistribution
        # creating the initial DeskCards of cards with all available cards in it
        cards = []
        cardsPerColor = len(cardsDistribution)
        colorPossibilities = np.array(["red", "blue", "green", "yellow", "white"])[:numberOfColors]
        cardNumbers = cardsDistribution * numberOfColors
        for i in range(len(cardNumbers)):
            color = colorPossibilities[i // cardsPerColor]
            number = cardNumbers[i]
            cards.append(Card(color, number))

        self.cards = cards
        self.numberOfCards = len(cards)

    # Draw/remove cards functions

    def removeRandom(self):
        maxIndex = len(self.cards)
        randomIndex = (randrange(maxIndex))
        randomCard = self.cards[randomIndex]
        self.cards.pop(randomIndex)
        self.numberOfCards = len(self.cards)
        return randomCard

    def removeCard(self, cardToRemove):
        for i in range(self.numberOfCards):
            if cardToRemove.isSameAs(self.cards[i]):
                del self.cards[i]
                self.numberOfCards = - 1
                break
        return self.numberOfCards

    # Visualization functions

    def sayAllCards(self):
        for i in range(len(self.cards)):
            self.cards[i].sayInfo()

    # Return cards information，like this [['5', 'red'], ['1', 'red'], ['3', 'red'], ['2', 'red'], ['4', 'red']]
    def storeInfo(self):
        # Declaring rows
        N = len(self.cards)
        # Declaring columns 
        M = 2
        # using list comprehension  
        # to initializing matrix 
        cardMatrix = [[0 for i in range(M)] for j in range(N)]

        for i in range(len(self.cards)):
            cardMatrix[i][0] = self.cards[i].number
            cardMatrix[i][1] = str(self.cards[i].color)

        return cardMatrix


class HintTokens:

    def __init__(self, tokenNumber, tokenMax):
        self.tokenNumber = tokenNumber
        self.tokenMax = tokenMax

    def tokenRemove(self, human):
        if 0 < self.tokenNumber:
            self.tokenNumber -= 1
        else:
            if human:
                print("\033[31mError. Not enough tokens. You need to discard to get token.\033[0m")

    def tokenAdd(self, human):
        if self.tokenNumber < self.tokenMax:
            self.tokenNumber += 1
        else:
            if human:
                print("\033[31mError. Tokens maximum limit reached. You need to give hint to use token.\033[0m")


class PenaltyTokens:

    def __init__(self, tokenNumber, tokenMax):
        self.tokenNumber = tokenNumber
        self.tokenMax = tokenMax

    def tokenAdd(self,human):
        if self.tokenNumber < self.tokenMax:
            self.tokenNumber += 1
        else:
            if human:
                print("\033[31mError. Tokens maximum limit reached. You lost game.\033[0m")


class DiscardCards:

    def __init__(self, cards):
        self.cards = cards
        self.numberOfCards = len(cards)

    def addCard(self, card):
        self.cards.append(card)
        self.numberOfCards += 1
        return self.numberOfCards

    def convertList(self):

        global coloredCardNumber
        listCards = []
        for i in range(len(self.cards)):

            currentCard = self.cards[i]
            if currentCard.color == "red":
                coloredCardNumber = '\x1b[%sm %s \x1b[0m' % (red, currentCard.number)
            elif currentCard.color == "blue":
                coloredCardNumber = '\x1b[%sm %s \x1b[0m' % (blue, currentCard.number)
            elif currentCard.color == "green":
                coloredCardNumber = '\x1b[%sm %s \x1b[0m' % (green, currentCard.number)
            elif currentCard.color == "yellow":
                coloredCardNumber = '\x1b[%sm %s \x1b[0m' % (yellow, currentCard.number)
            elif currentCard.color == "white":
                coloredCardNumber = '\x1b[%sm %s \x1b[0m' % (white, currentCard.number)
            listCards += [coloredCardNumber]

        return listCards


class PlayedCards:

    def __init__(self, numberOfColors):
        self.colors = ["red", "blue", "green", "yellow", "white"][:numberOfColors + 1]
        self.numberOfColors = numberOfColors
        self.piles = [[] for i in range(self.numberOfColors)]  # Lists (representing each pile) within a list

    def addCard(self, card, human):
        if card.color in self.colors:
            pileIndex = self.colors.index(card.color)
            # print(pileIndex)

            if (len(self.piles[pileIndex]) == 0) and (card.number == 1):
                self.piles[pileIndex].append(card)

            elif (len(self.piles[pileIndex]) != 0) and (card.number == self.piles[pileIndex][-1].number + 1):
                self.piles[pileIndex].append(card)

            else:
                if human:
                    print("\033[31mCard cannot be added to a firework, it will be discarded\033[0m")
                    print("\033[31mThe following card was added to the discard pile: Color: {}, number: {}.\033[0m".format(card.color,
                                                                                                            card.number))
                return False
            if human:
                print("\033[34mWell done! The card was added to the {} firework!\033[0m".format(card.color))
            return True


    def convertList(self, pilePosition):
        listCards = []
        for i in range(len(self.piles[pilePosition])):
            listCards += [self.piles[pilePosition][i].number]
        return listCards


