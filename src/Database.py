import sqlite3
import enum
import sys
from mbus import *
from main_events import FOAD

'''
SQLite3 abstraction for database functionality needed by the application.
The Database stores library information about known games and systems.
'''
class ACNTBootDatabase:
	_sqlite = None
	_dbfile = None

	def __init__(self, dbfile: str):
		self._dbfile = dbfile
		try:
			self._sqlite = sqlite3.connect(self._dbfile)
		except:
			print("failed to connect to sqlite db")
			return

		MBus.add_handler(FOAD, self.die)

	def die(self, data):
		print("ohfuck")
		self._sqlite.close()

	def getGameList(self) -> list:
		return self._sqlite.execute("SELECT id, title FROM games").fetchall()

	def getGameInformation(self, header_title: str) -> list:
		return self._sqlite.execute("SELECT id, title FROM games WHERE header_title = ? LIMIT 1", [header_title]).fetchone()

	def getGameInformationByIdent(self, header_ident: str) -> list:
		result = self._sqlite.execute("SELECT id, title FROM games WHERE header_ident = ?", [header_ident])
		if self._sqlite.rowcount > 1:
			return result.fetchall()
		else:
			result.fetchone()

	def getGameInformationByChecksum(self, md5sum: str) -> list:
		#TODO: test
		result = self._sqlite.execute("SELECT games.id, games.title, description FROM game_checksums WHERE game_checksums.md5 = ? JOIN game ON game_checksums.game_id = games.id LIMIT 1", [md5sum]).fetchone()
		if self._sqlite.rowcount < 1:
			return [] # not found
		'''
		md5row = self._sqlite.execute("SELECT game_id, description FROM game_checksums WHERE md5 = ?", [md5sum]).fetchone()
		if self._sqlite.rowcount < 1:
			return false

		game_id = md5row[0]
		descr = md5row[1]
		md5row = None #save a little memory maybe, depending on GC

		self._sqlite.execute("SELECT id, title FROM games WHERE id = ? LIMIT 1", [game_id]).fetchone()

		if self._sqlite.rowcount < 1:
			return false
		'''
		return result

	def getGameInformationById(self, game_id: int) -> list:
		return self._sqlite.execute("SELECT id, title FROM games WHERE id = ? LIMIT 1", [game_id]).fetchone()

	def getAttributes(self) -> list:
		return self._sqlite.execute("SELECT * FROM attributes").fetchall()

	def getSystems(self) -> list:
		return self._sqlite.execute("SELECT id, name from systems").fetchall()

	def getControlTypes(self) -> list:
		return self._sqlite.execute("SELECT id, value FROM attributes_values WHERE attribute_id=1").fetchall()

	def getPlayers(self) -> list:
		return self._sqlite.execute("SELECT id, value FROM attributes_values WHERE attribute_id=2").fetchall()

	def getMonitorTypes(self) -> list:
		return self._sqlite.execute("SELECT id, value FROM attributes_values WHERE attribute_id=3").fetchall()

	def getDIMMResetValues(self) -> list:
		return self._sqlite.execute("SELECT id, value FROM attributes_values WHERE attribute_id=4").fetchall()

	def getDIMMRAMValues(self) -> list:
		return self._sqlite.execute("SELECT id, value FROM attributes_values WHERE attribute_id=5").fetchall()

	def getSystemFromName(self, name: str) -> list:
		return self._sqlite.execute("SELECT * from systems where systems.name = ?", [name]).fetchone()
		
	def getGameSystem(self, game_id: int) -> list:
		return self._sqlite.execute("SELECT systems.id as id, systems.name as name FROM systems JOIN games ON games.system_id=systems.id WHERE games.id = ? LIMIT 1", [game_id]).fetchone()

	def getGameAttributes(self, game_id: int) -> list:
		return self._sqlite.execute("SELECT attributes_values.id as id, attributes.name as name, attributes_values.value as value FROM game_attributes JOIN attributes ON game_attributes.attribute_id=attributes.id JOIN attributes_values ON attributes_values_id=attributes_values.id WHERE game_id = ?", [game_id]).fetchall()

	def getGameAttribute(self, game_id: int, attribute_id: int) -> list:
		return self._sqlite.execute("SELECT atributes_values.id as value_id, attributes.name as name, attributes_values.value as value FROM game_attributes JOIN attributes ON game_attributes.attribute_id=attributes.id JOIN attributes_values ON attributes_values_id=attributes_values.id WHERE game_attributes.game_id=? AND attribute_id=? LIMIT 1", [game_id], [attribute_id]).fetchone()
	
	def getValuesForAttribute(self, attribute_id: int) -> list:
		return self._sqlite.execute("SELECT id, value from attributes_values WHERE attribute_id= ?", [attribute_id]).fetchall()

	def getGameKnownChecksums(self, game_id: int) -> list:
		return self._sqlite.execute("SELECT md5, description from game_checksums WHERE game_id = ?", [game_id]).fetchall()

	

	def validateGameChecksum(game_id: int, checksum: str) -> bool:
		pass

