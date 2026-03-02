import os
import tkinter as tk
from dataclasses import dataclass
from PIL import Image, ImageTk

# GUI Properties
# Colors 
LIGHT = "#f0d9b5" 
DARK = "#b58863"
TILE_SIZE = 80

SCRIPT_DIR = os.path.dirname(__file__)
ASSET_PATH = f"{SCRIPT_DIR}/assets"


IMAGE_TO_PIECES = {
	"p": f"{ASSET_PATH}/chess_pawn_black.png",
	"r": f"{ASSET_PATH}/chess_rook_black.png",
	"n": f"{ASSET_PATH}/chess_knight_black.png",
	"b": f"{ASSET_PATH}/chess_bishop_black.png",
	"q": f"{ASSET_PATH}/chess_queen_black.png",
	"k": f"{ASSET_PATH}/chess_king_black.png",

	"P": f"{ASSET_PATH}/chess_pawn_white.png",
	"R": f"{ASSET_PATH}/chess_rook_white.png",
	"N": f"{ASSET_PATH}/chess_knight_white.png",
	"B": f"{ASSET_PATH}/chess_bishop_white.png",
	"Q": f"{ASSET_PATH}/chess_queen_white.png",
	"K": f"{ASSET_PATH}/chess_king_white.png",
}

# Cache for making sure images get loaded only once
_image_cache = {}

@dataclass
class GameState:
	board: list
	turn: str
	castling: str
	en_passant: str
	halfmove: str
	fullmove: str

	def toFEN(self):
		ranks = []
		for rank in self.board:
			fen_rank = ""
			empty = 0
			for sq in rank:
				if sq == "None":
					empty+=1
				else:
					if empty > 0:
						fen_rank += str(empty)
						empty = 0
					fen_rank += sq
			if empty > 0:
				fen_rank += str(empty)
			ranks.append(fen_rank)
		board_fen = "/".join(ranks)
		return f"{board_fen} {self.turn} {self.castling} {self.en_passant} {self.halfmove} {self.fullmove}"

# Load and Cache images
def load_piece_image(piece):
	if piece not in _image_cache:
		filename = IMAGE_TO_PIECES[piece]
		print(f"Loading image: {filename}")
		img = Image.open(f"{filename}")
		img = img.resize((TILE_SIZE, TILE_SIZE), Image.LANCZOS)
		_image_cache[piece] = ImageTk.PhotoImage(img)
	return _image_cache[piece]

# Parse Forsyth-Edwards Notation (FEN)
# Reference: https://www.chess.com/terms/fen-chess#what-is-fen
def parseFEN(fenCode: str) -> GameState:
	# Tokenize
	board_state, turn, castling, en_passant, halfmove, fullmove = fenCode.split()
	
	# Each row represents a row on a chess board
	board = []
	for row in board_state.split('/'):
		board_row = []
		for space in row:
			if space.isdigit():
				for _ in range(int(space)):
					board_row.append("None")
			else:
				board_row.append(space)
		board.append(board_row)
	return GameState(board, turn, castling, en_passant, halfmove, fullmove)

class ChessGame:
	def __init__(self, gameState: GameState):
		print("ChessGame Created...")
		self.root = tk.Tk() 
		self.gameState = gameState

		# Info panel
		#  
		self.info_panel = tk.Frame(
			self.root, 
			width=180, 
			padx=15, 
			pady=15, 
			relief="ridge", 
			borderwidth=2, 
			bg="lightgray"
		)
		self.info_panel.grid(row=0, column=0, sticky="ns")

		title = tk.Label(
			self.info_panel,
			text="Game Info",
			font=("Arial", 18, "bold"),
			bg="lightgray"
		)
		title.pack(anchor="w", pady=20)


		# helper to make info lables
		self.turn_label = tk.Label(self.info_panel, text=f"Turn: {self.gameState.turn}", font=("Arial", 16))
		self.turn_label.pack(anchor="w", pady=20)
		self.castling_label = tk.Label(self.info_panel, text=f"castling: {self.gameState.castling}", font=("Arial", 16))
		self.castling_label.pack(anchor="w", pady=20)
		self.en_passant_label = tk.Label(self.info_panel, text=f"en_passant: {self.gameState.en_passant}", font=("Arial", 16))
		self.en_passant_label.pack(anchor="w", pady=20)
		self.halfmove_label = tk.Label(self.info_panel, text=f"halfmove: {self.gameState.halfmove}", font=("Arial", 16))
		self.halfmove_label.pack(anchor="w", pady=20)
		self.fullmove_label = tk.Label(self.info_panel, text=f"fullmove: {self.gameState.fullmove}", font=("Arial", 16))
		self.fullmove_label.pack(anchor="w", pady=20)

		# Chess Board
		self.canvas = tk.Canvas(self.root, width=640, height=640) 
		self.canvas.grid(row=0, column=1, sticky="ns")


		self.piece_ids = {}
		self.drag_data = {
			"item": None,
			"x": 0,
			"y": 0
		}

		self.draw_board()
		self.bind_events()

	#---------------------
	# Dragging Logic 
	#---------------------
	def bind_events(self):
		self.canvas.tag_bind("all", "<ButtonPress-1>", self.on_piece_click)
		self.canvas.tag_bind("all", "<B1-Motion>", self.on_piece_move)
		self.canvas.tag_bind("all", "<ButtonRelease-1>", self.on_piece_release)
	
	def on_piece_click(self, event):
		item = self.canvas.find_closest(event.x, event.y)[0]
		if item not in self.piece_ids:
			return
		
		self.drag_data['item'] = item
		self.drag_data['x'] = event.x
		self.drag_data['y'] = event.y
		self.canvas.tag_raise(item)

	def on_piece_move(self, event):
		item = self.drag_data["item"]
		if item is None:
			return
		
		dx = event.x - self.drag_data["x"]
		dy = event.y - self.drag_data["y"]

		self.canvas.move(item, dx, dy)

		self.drag_data["x"] = event.x
		self.drag_data["y"] = event.y

	def on_piece_release(self, event):
		item = self.canvas.find_closest(event.x, event.y)[0]
		if item not in self.piece_ids:
			return
		
		# Snap to nearest square
		col = event.x // TILE_SIZE
		row = event.y // TILE_SIZE

		if 0 <= row < 8 and 0 <= col < 8:
			x = col * TILE_SIZE + TILE_SIZE/2
			y = row * TILE_SIZE + TILE_SIZE/2
			self.canvas.coords(item, x, y)
		self.drag_data["item"] = None

	def draw_board(self):
		for row in range(8):
			for col in range(8):
				color = LIGHT if (row + col) % 2 == 0 else DARK
				
				# Draw squares
				x1 = col * TILE_SIZE
				y1 = row * TILE_SIZE
				x2 = x1 + TILE_SIZE
				y2 = y1 + TILE_SIZE
				self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)

				piece = self.gameState.board[row][col]
				if piece != "None":
					try:
						img = load_piece_image(piece)
						item = self.canvas.create_image(
							x1 + TILE_SIZE/2,
							y1 + TILE_SIZE/2,
							image=img
						)
					except:
						item = self.canvas.create_text(
							x1 + TILE_SIZE/2,
							y1 + TILE_SIZE/2,
							text = piece,
							font=("Arial", 32),
							fill="black" if piece.islower() else "white"
						)
					self.piece_ids[item] = (row, col)

	def start(self):
		print("Starting Game...")
		self.root.mainloop()

# Test FEN codes
#code = "r3k2r/pppq1ppp/2n1bn2/3pp3/3PP3/2N1BN2/PPP2PPP/R3K2R w - - 10 12"
STARTING_STATE = "nbrqkbrn/pppppppp/8/8/8/8/PPPPPPPP/NBRQKBRN w KQkq - 0 1"

if __name__ == "__main__":
	gameState = parseFEN(STARTING_STATE)
	app = ChessGame(gameState)
	app.start()