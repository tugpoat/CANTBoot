import sqlite3
import enum

'''
SQLite3 abstraction for database functionality needed by the application.
The Database stores library information about known games and systems.
'''
class ACNTBootDatabase:
	_sqlite = None
	_dbfile = None

	def __init__(self, dbfile):
		self._dbfile = dbfile
		try:
			self._sqlite = sqlite3.connect(self._dbfile)
		except:
			print("failed to connect to sqlite db")
			return

	def getGameList(self):
		return self._sqlite.execute("SELECT id, title FROM games").fetchall()

	def getGameInformation(self, header_title):
		return self._sqlite.execute("SELECT id, title FROM games WHERE header_title = ? LIMIT 1", [header_title]).fetchone()

	def getAttributes(self):
		return self._sqlite.execute("SELECT * FROM attributes").fetchall()

	def getSystems(self):
		return self._sqlite.execute("SELECT id, name from systems").fetchall()

	def getControlTypes(self):
		return self._sqlite.execute("SELECT id, value FROM attributes_values WHERE attribute_id=1").fetchall()

	def getPlayers(self):
		return self._sqlite.execute("SELECT id, value FROM attributes_values WHERE attribute_id=2").fetchall()

	def getMonitorTypes(self):
		return self._sqlite.execute("SELECT id, value FROM attributes_values WHERE attribute_id=3").fetchall()

	def getDIMMResetValues(self):
		return self._sqlite.execute("SELECT id, value FROM attributes_values WHERE attribute_id=4").fetchall()

	def getDIMMRAMValues(self):
		return self._sqlite.execute("SELECT id, value FROM attributes_values WHERE attribute_id=5").fetchall()

	def getSystemFromName(self, name):
		return self._sqlite.execute("SELECT * from systems where systems.name = ?", [name]).fetchone()
		
	def getGameSystem(self, game_id):
		return self._sqlite.execute("SELECT systems.id as id, systems.name as name FROM systems JOIN games ON games.system_id=systems.id WHERE games.id = ? LIMIT 1", [game_id]).fetchone()

	def getGameAttributes(self, game_id):
		return self._sqlite.execute("SELECT attributes_values.id as id, attributes.name as name, attributes_values.value as value FROM game_attributes JOIN attributes ON game_attributes.attribute_id=attributes.id JOIN attributes_values ON attributes_values_id=attributes_values.id WHERE game_id = ?", [game_id]).fetchall()

	def getGameAttribute(self, game_id, attribute_id):
		return self._sqlite.execute("SELECT atributes_values.id as value_id, attributes.name as name, attributes_values.value as value FROM game_attributes JOIN attributes ON game_attributes.attribute_id=attributes.id JOIN attributes_values ON attributes_values_id=attributes_values.id WHERE game_attributes.game_id=? AND attribute_id=? LIMIT 1", [game_id], [attribute_id]).fetchone()

	def getValuesForAttribute(self, attribute_id):
		return self._sqlite.execute("SELECT id, value from attributes_values WHERE attribute_id= ?", [attribute_id]).fetchall()
