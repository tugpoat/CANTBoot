from GameDescriptor import GameDescriptor

class GameList(List):
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

        if not os.path.isfile(filepath):
            print(igame[2] + " no longer installed, purging from DB")
            database.rmInstalledGameById(igame[0])
            continue # process next item

        game = GameDescriptor(filepath, prefs['Main']['skip_checksum'])
        if not game.isValid():
        	# TODO: Maybe spit out an error or something
        	# There are a number of reasons this might happen (filesystem unmounted etc)
        	continue

        if prefs['Main']['skip_checksum']:
                game.checksum = igame[4]

        if not prefs['Main']['skip_checksum'] and igame[4] != game.file_checksum:
                print("Checksum error in " + filename + " expected " + installed_game[4] + " got " + game.file_checksum)
                game.checksum_status = False

        game.game_id 	= igame[1]
        game.title		= igame[3]
        game.attributes = database.getGameAttributes(igame[1])

        games.append(game)

    # Clean up a little
    installed_games = None

    if not scan_fs:
    	return games

    print("Looking for new games")

    if os.path.isdir(games_directory):
    	for filename in os.listdir(games_directory):
    		filepath = games_directory + '/' + filename

    		# See if this file is already installed as a game in our db.
    		# Just use the partial games list we generated in the previous step.
    		is_installed = False

    		for igame in games:
    			if igame.filename == filename:
    				is_installed = True
    				break

    		if is_installed: continue

    		game = GameDescriptor(filepath)
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
    			game.attributes = database.getGameAttributes(installed_game[1])
    			games.append(game)
    		else:
    			print("\tUnable to identify " + filename)
                game.game_id = 0
                game.checksum_status = True
                game.title = filename
                game.attributes = []
                games.append(game)

    games.sort(key = lambda games: games.name.lower())
    return games
