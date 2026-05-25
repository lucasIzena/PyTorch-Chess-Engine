import random

def randomMove(board):
    if len(list(board.legal_moves)) == 0:
        return None
    return random.choice(list(board.legal_moves))


