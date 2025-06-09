from ChessBoard import ChessBoard
from evaluation import evalutate_position

a=ChessBoard()
a.display()
print(len([k.get_string() for k in a.get_legal_moves()]))
