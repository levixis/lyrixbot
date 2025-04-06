# app.py
import os
from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Replace with your Genius API access token
GENIUS_ACCESS_TOKEN = 'Zy31hHGwyHWgGusNTNpQnoSZQLJO4AvuuFTJBAK-KSBIGjGkfG8J_-rptg20PHVH'

def search_genius(song_name, artist_name=None):
    headers = {'Authorization': f'Bearer {GENIUS_ACCESS_TOKEN}'}
    query = song_name
    if artist_name:
        query += f' {artist_name}'
    params = {'q': query}
    
    try:
        response = requests.get('https://api.genius.com/search', 
                              headers=headers, 
                              params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return None
    
    data = response.json()
    hits = data.get('response', {}).get('hits', [])
    
    for hit in hits:
        if hit.get('type') == 'song':
            song = hit.get('result', {})
            primary_artist = song.get('primary_artist', {}).get('name', '').lower()
            if artist_name and artist_name.lower() not in primary_artist:
                continue
            return {
                'url': song.get('url'),
                'title': song.get('title'),
                'artist': song.get('primary_artist', {}).get('name')
            }
    return None

def scrape_lyrics(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Try different lyric container selectors
    lyrics_div = soup.find('div', class_='lyrics')
    if lyrics_div:
        return lyrics_div.get_text().strip()
    
    lyrics_containers = soup.find_all('div', attrs={'data-lyrics-container': 'true'})
    if lyrics_containers:
        lyrics = '\n'.join([container.get_text(separator='\n') for container in lyrics_containers])
        return lyrics.strip()
    
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search_lyrics():
    song_name = request.form.get('song', '').strip()
    artist_name = request.form.get('artist', '').strip()
    
    if not song_name:
        return jsonify({'error': 'Song name is required'}), 400
    
    genius_data = search_genius(song_name, artist_name or None)
    if not genius_data:
        return jsonify({'error': 'Song not found'}), 404
    
    lyrics = scrape_lyrics(genius_data['url'])
    if not lyrics:
        return jsonify({'error': 'Lyrics not found'}), 404
    
    return jsonify({
        'title': genius_data['title'],
        'artist': genius_data['artist'],
        'lyrics': lyrics
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)