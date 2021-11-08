from my_server.database_handler import create_connection

conn = create_connection()
cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY UNIQUE,
    username TEXT NOT NULL,
    key TEXT NOT NULL,
    summoner TEXT NOT NULL,
    summonerId TEXT NOT NULL,
    puuid TEXT NOT NULL,
    accountId TEXT NOT NULL
)''')
namn = [("Noviru","Hejsan","Noviru","4219841290","421421","4214211")]
cur.executemany('INSERT INTO users(username,key,summoner,summonerId,puuid,accountId) VALUES(?,?,?,?,?,?)', (namn))


cur.execute('''CREATE TABLE IF NOT EXISTS dataMatch(
            partId INTEGER,
            summonerName TEXT NOT NULL,
            matchId INTEGER,
            kills INTEGER,
            deaths INTEGER,
            assists INTEGER,
            champName TEXT,
            win BOOLEAN,
            creation INTEGER
)
''')

conn.commit()
