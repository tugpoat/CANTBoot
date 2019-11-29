from GameDescriptor import GameDescriptor
import configparser
import os

#TODO: Extend List or something
class GameList():
	
	def helloworld():
		print('Hello World!')

def build_games_list(database, prefs, scan_fs=True):
	games = []

	games_directory = prefs['Games']['directory'] or 'games'

	# Get list of installed games from DB
	installed_games = database.getInstalledGames()
	
	# Check to make sure all the games we think are installed actually are. if not, purge them from the DB.
	# While we're at it, build the already installed games into our working game list.
	print("Checking installed games")

	for igame in installed_games:
		filepath = games_directory + '/' + igame[2]
		print("Checking " + igame[2])
		if not os.path.isfile(filepath):
			print(igame[2] + " no longer installed, purging from DB")
			database.rmInstalledGameById(igame[0])
			continue # process next item

		game = GameDescriptor(filepath, prefs['Main']['skip_checksum'])
		if not game.isValid():
			#print("game not valid")
			# TODO: Maybe spit out an error or something
			# There are a number of reasons this might happen (filesystem unmounted etc)
			continue

		# Skip checksumming if requested for faster startup time
		if prefs['Main']['skip_checksum']:
				game.file_checksum = igame[4]

		if not prefs['Main']['skip_checksum'] and igame[4] != game.file_checksum:
				print("Checksum error in " + filename + " expected " + installed_game[4] + " got " + game.file_checksum)
				game.checksum_status = False

		game.game_id 	= igame[1]
		game.title		= igame[3]

		game.setSystem(database.getGameSystem(igame[1]))
		attributes = database.getGameAttributes(igame[1])
		if len(attributes) > 0:
			game.attributes = database.getGameAttributes(igame[1])
			game.setAttributes(database.getGameAttributes(igame[1]))

		games.append(game)

	# Clean up a little
	installed_games = None

	#If we don't want to scan the games directory for new roms, then just sort and return what we have.
	if not scan_fs:
		games.sort(key = lambda games: games.title.lower())
		return games

	print("Looking for new games")

	if os.path.isdir(games_directory):
		for filename in os.listdir(games_directory):
			filepath = games_directory + '/' + filename

			# See if this file is already installed as a game in our db.
			# Just use the partial games list we generated in the previous step.
			is_installed = False

			'''
			Loop through and check the filename against all our installed filenames.
			No need for search algorithms, this list will never be large.
			If we find a match, then the game is already installed and no further processing is necessary for this file.
			'''
			for igame in games:
				if igame.filename == filename:
					is_installed = True
					break

			if is_installed: continue

			'''
			Since we have established that this rom is not yet installed, we need to do the following:
			Instantiate a new GameDescriptor
			Ensure it is a valid netboot file
			Retrieve any information from the database that we can about it
			Add the game and its related information (represented by the GameDescriptor object) to the list
			'''
			game = GameDescriptor(filepath)

			# If it's not a valid netboot file we don't care about it anymore
			if not game.isValid():
				continue

			identity = database.getGameInformation(game.rom_title)

			if identity:
				# Game has information available in the DB, we have been able to identify it
				installed_game = database.getInstalledGameByGameId(identity[0])

				if not installed_game:
					# If game is not installed, do so.
					database.installGame(identity[0], filename, game.file_checksum)
					installed_game = database.getInstalledGameByGameId(identity[0])

				# TODO: at this point we should just fetch everything back from the DB and load it into a GameDescriptor on the back end.
				game.game_id = identity[0]
				game.title = identity[1]

				game.setSystem(database.getGameSystem(installed_game[1]))
				game.attributes = database.getGameAttributes(installed_game[1])
				game.setAttributes(database.getGameAttributes(installed_game[1]))
				games.append(game)
				print("\tAdded " + game.title)
			else:
				# We were unable to retrieve information about this game from the database. 
				# Just fill in whatever we can and pass it along.
				print("\tUnable to identify " + filename)
				game.game_id = 0
				game.checksum_status = True
				game.title = filename
				game.attributes = []
				games.append(game)

	# Sort and return our built list of GameDescriptor objects
	games.sort(key = lambda games: games.title.lower())
	return games
