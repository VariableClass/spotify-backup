import datetime
import logging
import json
from . import SpotifyAPI
import azure.functions as func


def main(mytimer: func.TimerRequest) -> None:
	utc_timestamp = datetime.datetime.utcnow().replace(
			tzinfo=datetime.timezone.utc).isoformat()

	if mytimer.past_due:
			logging.info('The timer is past due!')

	token = ""
	includePlaylists = True
	includeLiked = True
	outputFormat = "json"
	outputFilename = "default" + "." + outputFormat
	
	spotify = SpotifyAPI(token)
	
	# Get the ID of the logged in user.
	logging.info('Loading user info...')
	me = spotify.get('me')
	logging.info('Logged in as {display_name} ({id})'.format(**me))

	playlists = []

	# List liked songs
	if includeLiked:
		logging.info('Loading liked songs...')
		liked_tracks = spotify.list('users/{user_id}/tracks'.format(user_id=me['id']), {'limit': 50})
		playlists += [{'name': 'Liked Songs', 'tracks': liked_tracks}]

	# List all playlists and the tracks in each playlist
	if includePlaylists:
		logging.info('Loading playlists...')
		playlist_data = spotify.list('users/{user_id}/playlists'.format(user_id=me['id']), {'limit': 50})
		logging.info(f'Found {len(playlist_data)} playlists')

		# List all tracks in each playlist
		for playlist in playlist_data:
			logging.info('Loading playlist: {name} ({tracks[total]} songs)'.format(**playlist))
			playlist['tracks'] = spotify.list(playlist['tracks']['href'], {'limit': 100})
		playlists += playlist_data
	
	# Write the file.
	logging.info('Writing files...')
	with open(outputFilename, 'w', encoding='utf-8') as f:
		# JSON file.
		if outputFormat == 'json':
			json.dump(playlists, f)
		
		# Tab-separated file.
		else:
			for playlist in playlists:
				f.write(playlist['name'] + '\r\n')
				for track in playlist['tracks']:
					if track['track'] is None:
						continue
					f.write('{name}\t{artists}\t{album}\t{uri}\r\n'.format(
						uri=track['track']['uri'],
						name=track['track']['name'],
						artists=', '.join([artist['name'] for artist in track['track']['artists']]),
						album=track['track']['album']['name']
					))
				f.write('\r\n')
	logging.info('Wrote file: ' + outputFilename)

	logging.info('Python timer trigger function ran at %s', utc_timestamp)
