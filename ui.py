from flask import Flask, render_template, request, jsonify, url_for
import chess
import logging
from game import PlayLastMove, EngineMove, board
from gantry import StartTransmitting, EndTransmitting, transmitting

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

piece_map = {
    'P': 'whitePawn.png', 'p': 'blackPawn.png',
    'N': 'whiteKnight.png', 'n': 'blackKnight.png',
    'B': 'whiteBishop.png', 'b': 'blackBishop.png',
    'R': 'whiteRook.png',   'r': 'blackRook.png',
    'Q': 'whiteQueen.png',  'q': 'blackQueen.png',
    'K': 'whiteKing.png',   'k': 'blackKing.png'
}

def render_chess_board():
    board_html = "<table class='chessboard'>"
    for rank in range(8, 0, -1):
        board_html += "<tr>"
        for file in "abcdefgh":
            square = file + str(rank)
            file_index = ord(file) - ord('a')
            rank_index = 8 - rank
            cell_color = "white" if ((file_index + rank_index) % 2 == 0) else "black"
            square_index = chess.parse_square(square)
            piece = board.piece_at(square_index)

            highlight = ""
            if len(board.move_stack) > 0:
                lastMove = board.peek()
                if chess.square_name(lastMove.from_square) == square or chess.square_name(lastMove.to_square) == square:
                    highlight = " highlight"
            
            if piece:
                piece_char = piece.symbol()
                if piece_char in piece_map:
                    img_url = url_for('static', filename=f"PieceImages/{piece_map[piece_char]}")
                    piece_html = f"<img src='{img_url}' class='piece' draggable='true' data-square='{square}'>"
                else:
                    piece_html = ""
            else:
                piece_html = ""
            board_html += f"<td class='{cell_color}{highlight}' data-square='{square}'>{piece_html}</td>"
        board_html += "</tr>"
    board_html += "</table>"
    return board_html

@app.route('/')
def index():
    board_html = render_chess_board()
    return render_template('index.html', board_html=board_html, transmitting=transmitting)

@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    move_str = data.get('move')
    try:
        move = chess.Move.from_uci(move_str)
        if move in board.legal_moves:
            board.push(move)
            new_board_html = render_chess_board()
            return jsonify({'status': 'success', 'board_html': new_board_html})
        else:
            return jsonify({'status': 'invalid move'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/update_physical_board', methods=['POST'])
def update_physical_board():
    try:
        PlayLastMove()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


# FIX LATER
@app.route('/engine_move', methods=['POST'])
def engine_move():
    try:
        EngineMove()
        new_board_html = render_chess_board()
        return jsonify({'status': 'success', 'board_html': new_board_html})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/update_transmitting', methods=['POST'])
def update_transmitting():
    data = request.get_json()
    if data.get('transmitting', False):
        StartTransmitting()
    else:
        EndTransmitting()
    return jsonify({'status': 'success', 'transmitting': transmitting})

# New endpoint to reset the board
@app.route('/reset', methods=['POST'])
def reset():
    board.reset()  # Resets the board to the initial position.
    
    new_board_html = render_chess_board()
    return jsonify({'status': 'success', 'board_html': new_board_html})

if __name__ == '__main__':
    app.run(debug=False)
