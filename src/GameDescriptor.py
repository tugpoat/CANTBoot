import io
import os
import hashlib
import json

class GameDescriptor:
	# Things from ROM file
	filename = None
	filepath = None
	file_checksum = None
    checksum_status = None
    system_name = None
	rom_title = None

	# Things from DB
	game_id = None
	title = None
	attributes = []

    def __init__(self, filepath, skip_checksum = False):
    	# Gather all the information we can from the filesystem
        self.filepath = filepath
        self.filename = os.path.basename(filepath)

        try:
        	# Open the file up and get all the info we need from the header data
        	self.file_size = os.stat(filepath).st_size
        	self.system_name = self.__file_get_target_system()
        	self.rom_title = self.__file_get_title()

        	# Checksum the file if we want to do that
        	if not skip_checksum:
            	self.file_checksum = self.__checksum()

        except Exception:
        	#TODO Actually do something
        	return

    def __file_get_title(self):
        'Get game title from rom file.'
        try:
            fp = open(self.filepath, 'rb')
            # We only care about the japanese title
            fp.seek(0x30, os.SEEK_SET)
            title = fp.read(32).decode('utf-8').rstrip(' ').lstrip(' ')

            fp.close()
            return title
        except Exception:
        	# TODO: thing

    def __file_get_target_system(self):
    	'Get the system that this game is meant to run on from the header'
    	try:
	        fp = open(filename, 'rb')
	        header_magic = fp.read(8).decode('utf-8')
	        fp.close()

	        if header_magic[:5] == 'NAOMI':
	        	return 'NAOMI'
	        else if header_magic[:6] == 'NAOMI2':
	        	return 'NAOMI2'
	        else if header_magic[:7] == 'CHIHIRO':
	        	return 'CHIHIRO'
	        else if header_magic == 'TRIFORCE' :
	        	return 'TRIFORCE'
	        else
	        	return False

	    except Exception:
	        # TODO: the thing
	        return False

    def __checksum(self):
    	try:
    		m = hashlib.md5()
	        with open(self.filepath, 'rb') as fh:
	            while True:
	                data = fh.read(8192)
	                if not data:
	                    break
	                m.update(data)
	                
	       	return m.hexdigest()
        except:
        	# TODO: Better error checking
        	return False

    def __hash__(self):
        return hash((self.name, self.filepath, self.size)) & 0xffffffff

    def isValid(self):
        return (system_name in ['NAOMI', 'NAOMI2', 'CHIHIRO', 'TRIFORCE'])

    def serialize(self):
    	return json.dumps({"file_name": self.filename, "file_path": self.filepath, "file_checksum": self.file_checksum, "rom_title": self.rom_title, "game_id":, self.game_id, "title": self.title, "attributes": json.dumps(self.attributes)})