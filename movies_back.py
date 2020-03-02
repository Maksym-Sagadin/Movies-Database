'''
Sergio Chairez
Maksym Sagadin
CIS41B - Lab 3
Back End GUI for movies_back.py

The movies_back.py will produce a JSON file and an SQL database file
libraries:sqllite3, beautifulsoup, requests
'''

import requests
from bs4 import BeautifulSoup
import re 
import sqlite3
import json

URL = "https://www.imdb.com/movies-in-theaters/"
page = requests.get(URL)


soup = BeautifulSoup(page.content, 'html.parser')
imdb = "https://www.imdb.com"

movies_data = []
movies_soup = soup.find_all('td', class_="overview-top")

genre_counter = 0
for i in range(len(movies_soup)):
    data = {}
    title = movies_soup[i].find(
        'a').textd
    title = re.sub("(\([0-9]{4})\)", "", title)
    # print(title)
    data['title'] = title
    link = imdb + movies_soup[i].find('a').attrs['href']
    data['link'] = link
    # print(title, link)
    rating = movies_soup[i].find('img').attrs['title'] if movies_soup[i].find('img') else None
    # print(rating)
    data['rating'] = rating
    if movies_soup[i].select('p.cert-runtime-genre > time'):
        runtime = movies_soup[i].select('p.cert-runtime-genre > time')
        # print(runtime[0])
        runtime = runtime[0].text
        runtime = runtime[:3]
    else:
        runtime = 0
    data['length'] = runtime
    # print(runtime)

    tmp_list = []
    
    if movies_soup[i].select('p > span'):
        tags = movies_soup[i].select('p > span')
        for tag in tags:
            if re.match('[a-zA-Z].*', tag.text):
                tmp_list.append(tag.text)
                
    data['genre'] = tmp_list
    movies_data.append(data)
    if len(tmp_list) > genre_counter:
        genre_counter = len(tmp_list)


#creates a unique list of genres
genres_list = []
for i in range(len(movies_data)):
    for genre in movies_data[i]['genre']:
        if genre not in genres_list:
            genres_list.append(genre)


# print(list(genres_set))
movies_data.append({"max_genres_in_a_movie": genre_counter, "types_of_genres": list(genres_list)})

#writes to JSON file
with open("movies.json", "w") as writeJSON:
    json.dump(movies_data, writeJSON, indent=3)
    

#opens database
movies_data = json.load(open('movies.json'))
db = sqlite3.connect('movies.db')
cur = db.cursor()

# remove old table if it's there
cur.execute("DROP TABLE IF EXISTS genres_table")
#create genre table
cur.execute('''CREATE TABLE genres_table (
                    genre_id INTEGER NOT NULL PRIMARY KEY UNIQUE,
                    genre TEXT UNIQUE ON CONFLICT IGNORE)''')


max_genre = movies_data[-1]['max_genres_in_a_movie']
unique_genres_list = movies_data[-1]['types_of_genres']

#insert into genre table
for genre in unique_genres_list:
    cur.execute('''INSERT INTO genres_table (genre) VALUES (?)''',
                (genre, ))

# remove old table if it's there  
cur.execute("DROP TABLE IF EXISTS movies_table")
create_movies_table_str = '''CREATE TABLE movies_table(
                       name TEXT NOT NULL PRIMARY KEY,
                       link TEXT NOT NULL,
                       rating TEXT,
                       length TEXT
                       '''
genre_ctr = 0
for i in range(max_genre):
    create_movies_table_str += ',genre' + \
        str(genre_ctr)+' INTEGER REFERENCES genres_table(genre_id) '
    genre_ctr += 1
create_movies_table_str += ')'

# creating movies table
# print(create_movies_table_str)
cur.execute(create_movies_table_str)


partial_SQL_statements_dict = {
    1: ["genre0) VALUES (?,?,?,?,?)", "(?)"],
    2: ["genre0, genre1) VALUES (?,?,?,?, ?,?)", "(?, ?)"],
    3: ["genre0, genre1, genre2) VALUES (?,?,?,?,?,?,?)", "(?, ?, ?)"],
    4: ["genre0, genre1, genre2, genre3) VALUES (?,?,?,?,?,?,?,?)", "(?, ?,?,?)"],
    5: ["genre0, genre1, genre2, genre3, genre4) VALUES (?,?,?,?,?,?,?,?,?)", "(?,?,?,?,?)"],
}


for record in movies_data[:-1]:
    for key in partial_SQL_statements_dict.keys():
        if len(record['genre']) == key:
            # print(len(record['genre']))
            insert_exec_statement = "INSERT INTO movies_table (name, link, rating, length, "
            insert_exec_statement += partial_SQL_statements_dict[key][0]
            # print(insert_exec_statement)
            select_exec_statement = "SELECT genre_id FROM genres_table WHERE genre in "
            select_exec_statement += partial_SQL_statements_dict[key][1]
            #selecting all the genre_id's from genres_table if they're in the record we're iterating through
            capture_genre_ids = cur.execute(
                select_exec_statement, (record['genre'])).fetchall()

            feautures_vals = [record['title'], record['link'],
                       record['rating'], record['length']]

            feautures_vals += [i[0] for i in capture_genre_ids]
            cur.execute(insert_exec_statement, (feautures_vals))

db.commit()
db.close()
