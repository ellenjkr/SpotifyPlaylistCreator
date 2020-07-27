import os
from os import listdir
from os.path import isfile, join
import sys
import json
from json.decoder import JSONDecodeError
import requests
import spotipy
import spotipy.util as util
import webbrowser
import eyed3


class Songs():
	def __init__(self, directory):
		super(Songs, self).__init__()
		self.directory = directory
		self.readFiles()
		self.sep100Songs()

	def readFiles(self):
		files = [f for f in listdir(self.directory) if isfile(join(self.directory, f))]
		self.songs = {'Title':[], 'Artist':[]}

		for pos, i in enumerate(files):
			if i == 'desktop.ini':
				files.pop(pos)

		cont = 0
		for i in files:
			try:
				song = eyed3.load(f"{self.directory}/{i}")
				self.songs['Title'].append(song.tag.title)
				if isinstance(song.tag.artist, type(None)):
					self.songs['Artist'].append('')
				else:
					if "/" in song.tag.artist:
						artist = song.tag.artist.split('/')
						self.songs['Artist'].append(artist[0])
					else:
						self.songs['Artist'].append(song.tag.artist)
			except:
				if ".jpg" not in i:
					if ".m4a" in i:
						cont += 1
					else:
						print(f"{i} não foi possível")

		if cont > 0:
			print(cont, "m4a")

	def sep100Songs(self): # Separate the songs in different lists if it reaches 100 songs, because of the limit of songs of the API
		self.listsOfSongs = []
		temp = {'Title':[], 'Artist':[]}
		posRef = 0
		for i in range(len(self.songs['Title'])):
			if i % 99 == 0 and i != 0:
				temp['Title'] = self.songs['Title'][i-99:i+1]
				temp['Artist'] = self.songs['Artist'][i-99:i+1]
				self.listsOfSongs.append(temp)
				temp = {'Title':[], 'Artist':[]}
				posRef = i + 1
				print(posRef)
			elif i == (len(self.songs['Title'])-1):
				temp['Title'] = self.songs['Title'][posRef:len(self.songs['Title'])]
				temp['Artist'] = self.songs['Artist'][posRef:len(self.songs['Title'])]
				self.listsOfSongs.append(temp)


class SpotifyUris():
	def __init__(self, songs, token):
		super(SpotifyUris, self).__init__()
		self.songs = songs
		self.token = token
		self.uris = []
		self.addUris()

	def get_spotify_uri(self, song_name, artist):
		try:
			query = f"https://api.spotify.com/v1/search?query=track%3A{song_name}+artist%3A{artist}&type=track&offset=0&limit=20"
			response = requests.get(
				query,
				headers = {
					"Content-Type":"application/json",
					"Authorization":f"Bearer {self.token}"
				}
			)
			response_json = response.json()
			songs = response_json["tracks"]["items"]
			#only use the first song
			uri = songs[0]['uri']
			return uri

		except:
			try:
				if "'" in song_name:
					song_name = song_name.replace("'", "")
				
				query = f"https://api.spotify.com/v1/search?query=track%3A{song_name}+artist%3A{artist}&type=track&offset=0&limit=20"
				response = requests.get(
					query,
					headers = {
						"Content-Type":"application/json",
						"Authorization":f"Bearer {self.token}"
					}
				)
				response_json = response.json()
				songs = response_json["tracks"]["items"]
				#only use the first song
				uri = songs[0]['uri']

				return uri

			except:
				print('Música não encontrada: ', song_name, " - ", artist)
		
	def addUris(self):
		for pos in range(len(self.songs['Title'])):
			title = self.songs['Title'][pos]
			artist = self.songs['Artist'][pos]
			uri = self.get_spotify_uri(title, artist)
			if isinstance(uri, type(None)) == False:
				self.uris.append(uri)



class SpotifyPlaylist():
	def __init__(self, user, token, playlistName, description='', public=True):
		super(SpotifyPlaylist, self).__init__()
		# self.user = 'ellen_junker'
		self.user = user
		self.token = token
		self.playlistName = playlistName
		self.description = description
		self.public = public

	def create_playlist(self):
		request_body = json.dumps({
			"name": self.playlistName,
			"description": self.description,
			"public": self.public
		})
		query = f"https://api.spotify.com/v1/users/{self.user}/playlists"
		response = requests.post(
			query,
			data = request_body,
			headers = {
				"Content-Type":"application/json",
				"Authorization": f"Bearer {self.token}"
			}
		)
		response_json = response.json()
		self.playlist_id = response_json["id"]


	def add_songs_to_playlist(self, songsUris):		
		requests_data = json.dumps(songsUris)

		query = f"https://api.spotify.com/v1/playlists/{self.playlist_id}/tracks"

		response = requests.post(
			query,
			data = requests_data,
			headers={
				"Content-Type":"application/json",
				"Authorization":f"Bearer {self.token}"
			}
		)

def getToken():
	username = 'ellen_junker'
	scope = 'playlist-modify-public'
	client_id = '6c6749c4e12d4ed989ca0c344383e8a1'
	client_secret = 'a02f8ba8a03b4cbcbfc6dd817ffc90db'
	redirect_uri = 'https://google.com.br/'
	try:
		token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
		return token
	except:
		os.remove(f".cache-{username}")
		token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
		return token

def createPlaylistFromDir(directory, username, token, playlistName, description, public):
	songs = Songs(directory)
	playlist = SpotifyPlaylist(username, token, playlistName, description, public)
	playlist.create_playlist()

	for listOfSongs in songs.listsOfSongs:
		uris = SpotifyUris(listOfSongs, token)
		playlist.add_songs_to_playlist(uris.uris)

	print('\nDirectory: ', f"{directory} \nDone", "\n\n=====================================================", '\n\n')


if __name__ == '__main__':
	eyed3.log.setLevel("ERROR")
	token = getToken()
	sp = spotipy.Spotify(auth=token)

	# createPlaylistFromDir(f"path", "username", token, "playlistName", "description", True)

	directory = ""
	for folder in listdir(directory):
		playlistDir = directory + f"/{folder}"
		username = ""
		playlistName = folder
		description = f""
		public = True
		createPlaylistFromDir(playlistDir, username, token, playlistName, description, public)
