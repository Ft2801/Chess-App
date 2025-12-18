import chess

class ChessModel:
    """
    Wraps the chess.Board object and provides methods for game interaction.
    """
    def __init__(self):
        self.board = chess.Board()

    def reset_game(self):
        self.board.reset()

    def make_move(self, move: chess.Move) -> bool:
        """Attempts to make a move. Returns True if legal and made."""
        if move in self.board.legal_moves:
            self.board.push(move)
            return True
        return False

    def undo_move(self):
        if len(self.board.move_stack) > 0:
            self.board.pop()

    def get_legal_destinations(self, square: chess.Square) -> list[chess.Square]:
        """Returns a list of legal destination squares for a piece at the given square."""
        destinations = []
        for move in self.board.legal_moves:
            if move.from_square == square:
                destinations.append(move.to_square)
        return destinations

    def is_game_over(self) -> bool:
        return self.board.is_game_over()

    def is_checkmate(self) -> bool:
        return self.board.is_checkmate()

    def get_outcome(self):
        return self.board.outcome()

    def get_fen(self) -> str:
        return self.board.fen()

    def get_piece_map(self):
        return self.board.piece_map()
    
    @property
    def move_history(self):
        return self.board.move_stack

    def get_turn(self):
        return self.board.turn  # chess.WHITE or chess.BLACK
