from flask import Flask, render_template, request, jsonify
from chessEngine import randomMove
import chess

app = Flask(__name__)

board = chess.Board()


def board_to_array():
    result = []
    for rank in range(7, -1, -1):
        row = []
        for file in range(8):
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            if piece is None:
                row.append("")
            else:
                row.append(piece.symbol())
        result.append(row)
    return result


@app.route("/")
def home():
    return render_template("chessHome.html")

@app.route("/game")
def game():
    return render_template("chessGame.html")

@app.route("/position")
def position():
    return jsonify(
        {
            "position": board_to_array(),
            "turn": "White" if board.turn == chess.WHITE else "Black",
            "fen": board.fen(),
            "moveHistory": get_move_history(),
            "game_over": board.is_game_over(),
        }
    )


@app.route("/move", methods=["POST"])
def move():
    data = request.get_json()

    from_square = data.get("from")
    to_square = data.get("to")
    promotion = data.get("promotion", "")

    move_text = from_square + to_square + promotion

    try:
        move = chess.Move.from_uci(move_text)
    except ValueError:
        return jsonify(
            {
                "success": False,
                "error": "Invalid move format",
                "highlight": from_square,
            }
        )

    if move not in board.legal_moves:
        return jsonify(
            {
                "success": False,
                "error": "Illegal move",
                "highlight": from_square,
            }
        )

    board.push(move)
    end_info = get_game_end_info()

    return jsonify(
        {
            "success": True,
            "position": board_to_array(),
            "turn": "White" if board.turn == chess.WHITE else "Black",
            "fen": board.fen(),
            "moveHistory": get_move_history(),
            "game_over": board.is_game_over(),
            "resultText": get_game_over_text(),
            "lastMove": {
                "from": from_square,
                "to": to_square,
            },
            **end_info,
        }
    )

@app.route("/engine-move", methods=["POST"])
def engine_move():
    if board.is_game_over():
        return jsonify(
            {
                "success": False,
                "error": "Game is already over",
                "position": board_to_array(),
                "turn": "White" if board.turn == chess.WHITE else "Black",
                "fen": board.fen(),
                "game_over": True,
            }
        )
    move = randomMove(board)
    if move is None:
        return jsonify(
            {
                "success": False,
                "error": "No legal engine moves available",
                "position": board_to_array(),
                "turn": "White" if board.turn == chess.WHITE else "Black",
                "fen": board.fen(),
                "game_over": board.is_game_over(),
            }
        )

    board.push(move)
    end_info = get_game_end_info()
    return jsonify(
        {
            "success": True,
            "position": board_to_array(),
            "turn": "White" if board.turn == chess.WHITE else "Black",
            "fen": board.fen(),
            "moveHistory": get_move_history(),
            "game_over": board.is_game_over(),
            "resultText": get_game_over_text(),
            "lastMove": {
                "from": chess.square_name(move.from_square),
                "to": chess.square_name(move.to_square),
                "promotion": chess.piece_symbol(move.promotion) if move.promotion else "",
            },
            **end_info
        }
    )

@app.route("/new-game", methods=["POST"])
def new_game():
    global board, game_settings
    data = request.get_json() or {}
    game_settings = {
        "mode": data.get("mode", "engine"),
        "timeControl": data.get("timeControl", "none"),
        "difficulty": data.get("difficulty", "easy"),
        "playerColor": data.get("resolvedPlayerColor", "White"),
    }
    board.reset()
    return jsonify(
        {
            "success": True,
            "position": board_to_array(),
            "turn": "White" if board.turn == chess.WHITE else "Black",
            "moveHistory": get_move_history(),
            "gameSettings": game_settings,
        }
    )

def get_game_over_text():
    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"
        return f"Checkmate — {winner} wins"

    if board.is_stalemate():
        return "Stalemate — draw"

    if board.is_insufficient_material():
        return "Draw — insufficient material"

    if board.is_seventyfive_moves():
        return "Draw — 75-move rule"

    if board.is_fivefold_repetition():
        return "Draw — fivefold repetition"

    if board.is_game_over():
        return "Game over"

    return None

def get_game_end_info():
    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"
        return {
            "game_over": True,
            "winner": winner,
            "endReason": "checkmate",
            "resultText": f"Checkmate — {winner} wins",
        }

    if board.is_stalemate():
        return {
            "game_over": True,
            "winner": None,
            "endReason": "stalemate",
            "resultText": "Stalemate — draw",
        }

    if board.is_insufficient_material():
        return {
            "game_over": True,
            "winner": None,
            "endReason": "insufficient material",
            "resultText": "Draw — insufficient material",
        }

    if board.is_seventyfive_moves():
        return {
            "game_over": True,
            "winner": None,
            "endReason": "75-move rule",
            "resultText": "Draw — 75-move rule",
        }

    if board.is_fivefold_repetition():
        return {
            "game_over": True,
            "winner": None,
            "endReason": "fivefold repetition",
            "resultText": "Draw — fivefold repetition",
        }

    return {
        "game_over": False,
        "winner": None,
        "endReason": None,
        "resultText": None,
    }

def get_move_history():
    temp_board = chess.Board()
    history = []
    for move in board.move_stack:
        san = temp_board.san(move)
        history.append(san)
        temp_board.push(move)
    return history

if __name__ == "__main__":
    app.run(debug=True)
