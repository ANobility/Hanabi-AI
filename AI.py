"""
@author: weibo zhao
"""
import copy
import numpy as np
from HanabiClasses import Card
import copy
from itertools import combinations


class BeliefSpace:
    def __init__(self, state, hand_size):
        self.states = []
        state.depth = 0
        DeskCards = state.DeskCards.storeInfo()

        # transform the list into tuple
        DeskCards = [(i, j) for [i, j] in DeskCards]

        # Reduce the belief space if the AI cards have hints
        hinted = []
        unhited = []
        for i in range(len(state.AI.cards)):
            if state.AI.cards[i].colorHinted or state.AI.cards[i].numberHinted:
                hinted.append((state.AI.cards[i].number, state.AI.cards[i].color))
            else:
                unhited.append(i)

        player2 = [(i, j) for [i, j] in state.AI.storeInfo() if (i, j) not in hinted]
        unknown = player2 + DeskCards

        all_combination = set(list(combinations(unknown, hand_size - len(hinted))))
        for i in all_combination:
            newstate = copy.deepcopy(state)
            DeskCards = [item for item in unknown if item not in i]
            newstate.desk = [Card(k[1], k[0]) for k in DeskCards]

            new = [Card(k[1], k[0]) for k in i]
            for ind, k in enumerate(unhited):
                newstate.AI.cards[k] = new[ind]

            self.states.append(newstate)


class State_init:
    def __init__(self, Player1, Player2, DeskCards, PlayedCards, DiscardCards, hintTokens, penaltyTokens, turn, parent):
        self.Player = Player1
        self.AI = Player2
        self.DeskCards = DeskCards
        self.PlayedCards = PlayedCards
        self.DiscardCards = DiscardCards
        self.hintTokens = hintTokens
        self.penaltyTokens = penaltyTokens
        # only 1 or 2
        self.turn = turn

        if turn == 1:
            self.human = True
        else:
            self.human = False
        self.parent = parent
        self.depth = 0
        self.value = 0

    def switchTurn(self):
        self.turn = self.turn % 2 + 1
        self.human = not self.human

    def __eq__(self, other):

        return self.__dict__ == other.__dict__


class AI_Hint:
    def __init__(self, h_type):
        self.h_type = h_type
        self.name = "hint"

    def __call__(self, initialState, hint=None):
        # hintType: String. Can be "number" or "color"
        # hint: String ("red","green",...) or Int ("1","2","3","4" or "5")

        # initializing variables (extracted from state)
        global otherPlayer
        newState = copy.deepcopy(initialState)
        newState.parent = initialState
        newState.depth = initialState.depth + 1
        human = False  # newState.human

        if newState.turn == 1:

            otherPlayer = newState.AI
        elif newState.turn == 2:
            otherPlayer = newState.Player
        hintTokens = newState.hintTokens

        # print("hint:", hint)
        if hintTokens == 0:
            # print ("Error. Number of Hint Tokens is 0. You cannot make a Hint.")
            return None

        if otherPlayer.allHintsGiven(hint, self.h_type):
            # print ("Error. Hint already given or no cards correspond to the hint. You cannot make that hint.")
            return None
        if hint != None:
            for i in range(len(otherPlayer.cards)):
                if self.h_type == "color":
                    if otherPlayer.cards[i].color == hint:
                        otherPlayer.cards[i].colorHinted = True
                elif self.h_type == "number":
                    if otherPlayer.cards[i].number == hint:
                        otherPlayer.cards[i].numberHinted = True
        hintTokens.tokenRemove(human)
        newState.turn = newState.turn % 2 + 1

        return newState


class AI_Discard:
    # cardPosition: Int. Index of the card you want to discard from your hand.
    def __init__(self):
        self.name = "discard"

    def __call__(self, initialState, cardPosition):
        # initializing variables (extracted from state)
        newState = copy.deepcopy(initialState)
        newState.parent = initialState
        newState.depth = initialState.depth + 1
        human = False  # newState.human

        if newState.turn == 1:
            activePlayer = newState.Player
        elif newState.turn == 2:
            activePlayer = newState.AI
        hintTokens = newState.hintTokens
        DeskCards = newState.DeskCards

        if hintTokens.tokenNumber == hintTokens.tokenMax:
            # print ("Error. Number of Hint Tokens is maxed. You cannot discard a card.")
            return None

        discardedCard = activePlayer.cards[cardPosition]
        newState.DiscardCards.addCard(discardedCard)
        # activePlayer.draw(DeskCards, cardPosition)
        hintTokens.tokenAdd(human)

        newState.turn = newState.turn % 2 + 1
        # newState.switchTurn()

        return newState


class AI_Play:
    def __init__(self):
        self.name = "play"

    def __call__(self, initialState, cardPosition):  # side is an integer, 0 = left, 1 = right
        # cardPosition: Int. Index of the card you want to play from your hand.

        # initializing variables (extracted from state)
        global activePlayer
        newState = copy.deepcopy(initialState)
        newState.parent = initialState
        newState.depth = initialState.depth + 1
        human = False

        if newState.turn == 1:
            activePlayer = newState.Player
        elif newState.turn == 2:
            activePlayer = newState.AI

        playedCard = activePlayer.cards[cardPosition]

        # check if the card was correct somehow
        # use functions from the playPile
        verif = newState.PlayedCards.addCard(playedCard, human)

        if not verif:
            newState.penaltyTokens.tokenAdd(human)
            newState.DiscardCards.addCard(playedCard)
        else:
            # instead of drawing we remove a card
            activePlayer.cards.pop(cardPosition)

        newState.turn = newState.turn % 2 + 1

        return newState


def score(state):
    score = 0
    for pile in state.PlayedCards.piles:
        # print(len(pile))
        score += len(pile)
        # print(state.penaltyTokens.tokenNumber)
    return score * 10 - 5 * state.penaltyTokens.tokenNumber - len(state.DiscardCards.cards)


class Solver:
    def __init__(self, max_depth):
        self.max_depth = max_depth

        self.actions = [[AI_Hint("color"), AI_Hint("number")], AI_Play(), AI_Discard()]

    def search_tree(self, beliefspace, currentState):
        global actions
        results = 0
        for state in beliefspace:
            children = [self.weight(self.actions[0][0](state, color)) for color in
                        np.unique([card.color for card in state.Player.cards])]  # giving hint color
            children = children + [self.weight(self.actions[0][1](state, number)) for number in
                                   np.unique([card.number for card in state.Player.cards])]  # giving hint color
            children = children + [self.weight(self.actions[1](state, pos)) for pos in
                                   np.arange(len(state.AI.cards))]  # playing card
            children = children + [self.weight(self.actions[2](state, pos)) for pos in
                                   np.arange(len(state.AI.cards))]  # discarding a card
            results = results + np.array(children)
            actions = [(self.actions[0][0].__dict__, color) for color in
                       np.unique([card.color for card in state.Player.cards])]
            actions = actions + [(self.actions[0][1].__dict__, number) for number in
                                 np.unique([card.number for card in state.Player.cards])]
            actions = actions + [(self.actions[1].__dict__, pos) for pos in np.arange(len(state.AI.cards))]
            actions = actions + [(self.actions[2].__dict__, pos) for pos in np.arange(len(state.AI.cards))]

        sorted_list = sorted([(action, -value) for action, value in zip(actions, results)],
                             key=lambda element: (element[1], element[0][0]["name"], str(element[0][1])))

        top_action = sorted_list[0][0]

        if top_action[0]["name"] == "play":
            print("\033[31mThe computer played: \033[0m", currentState.AI.cards[top_action[1]].storeInfo())
            return 1, top_action[1]
        elif top_action[0]["name"] == "hint":
            print("\033[31mYou got a hint: \033[0m", str(top_action[0]["h_type"]) + " " + str(top_action[1]))
            return 2, (top_action[0]["h_type"], top_action[1])
        elif top_action[0]["name"] == "discard":
            print("\033[31mThe computer discarded: \033[0m ", currentState.AI.cards[top_action[1]].storeInfo())
            return 3, top_action[1]

    def max_value(self, state):
        if state is None:
            return 0
        initialPenaltyTokens = state.parent.penaltyTokens.tokenNumber
        finalPenaltyTokens = state.penaltyTokens.tokenNumber
        difPenaltytokens = finalPenaltyTokens - initialPenaltyTokens

        if difPenaltytokens != 0:
            return -100
        if state.depth >= self.max_depth:
            return score(state)
        # vaule = -∞
        vaule = - np.inf
        # giving hints colors
        for card in state.Player.cards:
            # self.actions[0][0](state,card.color)) is a state
            vaule = max(vaule, self.weight(self.actions[0][0](state, card.color)))
            # giving hints numbers
            vaule = max(vaule, self.weight(self.actions[0][1](state, card.number)))

        # playing cards 
        for pos in np.arange(len(state.AI.cards)):
            vaule = max(vaule, self.weight(self.actions[1](state, pos)))
            vaule = max(vaule, self.weight(self.actions[2](state, pos)))

        return vaule

    def weight(self, state):
        if state is None:
            return - 100

        initialPenaltyTokens = state.parent.penaltyTokens.tokenNumber
        finalPenaltyTokens = state.penaltyTokens.tokenNumber
        difPenaltytokens = finalPenaltyTokens - initialPenaltyTokens

        # if the action get penalty token return -10
        if difPenaltytokens != 0:
            return -100

        if state.depth >= self.max_depth:
            return score(state)
        a = np.zeros(len(state.Player.cards))
        for i in range(len(a)):
            if state.Player.cards[i].colorHinted or state.Player.cards[i].numberHinted:
                a[i] = 1
            if state.Player.cards[i].colorHinted and state.Player.cards[i].numberHinted:
                a[i] = 2
        if a.sum() == 0:  # if there are no hints on the cards
            w_hint = 1
            w_play = 0
        else:  # if there are hints on the cards
            w_hint = 1 / (a.sum()) / 5
            w_play = 2 / (a.sum()) / 5

        vaule = w_hint * self.max_value(self.actions[0][0](state))

        for pos in np.arange(len(state.Player.cards)):
            vaule = vaule + w_play * a[pos] * self.max_value(self.actions[1](state, pos))
        return vaule
