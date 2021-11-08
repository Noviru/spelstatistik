from my_server import routes
from my_server.database_handler import create_connection
import json

def gameIdToStats(matchId):
    matchStats = []
    url = f'https://euw1.api.riotgames.com/lol/match/v4/matches/{matchId}/?api_key={api_key}'
    matchDatan = requests.get(url)
    matchDatan_json = matchDatan.json()
    #Plats 0 i gameStats kommer vara det senaste spelade matchen.
    #Skapa en nestad lista men, ParticipantId, kills, death, assists, champion ID, win
    #PATH(x['participants']['participantId'] = ID x['participants']['stats']['kills'] = kills/assist/death) x['participants'][0/1]['championId']
    #För att se vilka som vann, x['teams']['win']
    #För att hitta namnet på spelaren: x['participantIdentities']['(ID)']['summonerName']
    for player in matchDatan_json['participants']:
        participantId = player['participantId']
        kills = player['stats']['kills']
        deaths = player['stats']['deaths']
        assists = player['stats']['assists']
        champId = player['championId']
        win = player['stats']['win']
        x = [participantId, kills, deaths, assists, champId, win]
        matchStats.append(x)
    #summonerName = matchDatan_json['participantIdentities'][partId]['summonerName']
    return matchStats

#Tar in ett matchid och en summoner_name och returnar PartId för den summonern.
def toPartId(matchId,summoner):
    url = f'https://euw1.api.riotgames.com/lol/match/v4/matches/{matchId}/?api_key={api_key}'
    matchDatan = requests.get(url)
    matchDatan_json = matchDatan.json()
    for player in matchDatan_json['participantIdentities']:
        if player['player']['summonerName'] == summoner:
            return player['participantId']

#Listar ut alla summoners i en match
def summonerInMatch(matchId):
    summonerNames = []
    url = f'https://euw1.api.riotgames.com/lol/match/v4/matches/{matchId}/?api_key={api_key}'
    win_json = urlToJson(url)
    counter = 0
    for players in win_json['participantIdentities']:
        x = players['player']['summonerName']
        summonerNames.append(x)
        counter +=1
    return summonerNames


def urlToJson(url):
    json = requests.get(url)
    json_json = json.json()
    return json_json


#tar ut datan som har med rank att göra.
def rankStatus(username):
    data = getDataFromUsername(username)
    #Om man tittar på data och skriver ut det kan man testa sig till att data[0][4] kommer vara "summoner" vilket är
    #ingame namnet i "Leauge of legends"
    url = f'https://euw1.api.riotgames.com/lol/league/v4/entries/by-summoner/{data[0][4]}/?api_key={api_key}'
    rankData = requests.get(url)
    rankData_json = rankData.json()
    print(rankData_json)
    return rankData_json

#


def matchesPlayed(summoner):
    data = getDataFromSummoner(summoner)

#Skickar tillbaka datan som finns i sql-databasen för den användaren man skickade in.
def getDataFromUsername(username):
    conn = create_connection()
    cur = conn.cursor()
    sql = f'SELECT * FROM users WHERE username = "{username}"'
    cur.execute(sql)
    data = cur.fetchall()
    return data
#Skickar tillbaka datan som finns i sql-databasen för den summonern man skickade in.
def getDataFromSummoner(summoner):
    conn = create_connection()
    cur = conn.cursor()
    sql = f'SELECT * FROM users WHERE summoner = "{summoner}"'
    cur.execute(sql)
    data = cur.fetchall()
    return data

#Tar fram de senaste matcherna baserat på vilket användarnamn man skickade in, använder denna data som retuneras
#mest för att ta reda på gameID.
def matchesPlayed(username):
    data = getDataFromUsername(username)
    url = f'https://euw1.api.riotgames.com/lol/match/v4/matchlists/by-account/{data[0][6]}/?api_key={api_key}'
    matchData = requests.get(url)
    matchData_json = matchData.json()
    return matchData_json



def toRelevantData(matchInfo):
    matchStats = []
    summonerPartId = []
    counter = 0
    #Det finns hundra matches som sparas, vilket gör att denna loop kommer köras 100 gånger.
    for match in matchInfo['matches']:
        if counter <= 11:
            counterSummoner = 0
            #tar fram matchID för den matchen.
            matchId = match['gameId']
            #tar fram alla stats i matchen och endast det relevanta som görs i metoden gameIdTostats
            stats = gameIdToStats(matchId)
            #listar ut alla summoers som var med i matchen.
            summoners = summonerInMatch(matchId)
            for s in summoners:
                #lägger till summonername i statsen för hela matchen.
                stats[counterSummoner].append(s)
                counterSummoner += 1

            #lägger till stats, vilket är stats för en match
            matchStats.append(stats)
            counter +=1
            #tar fram ID för alla deltagara, för att göra det enkelt söka reda på de olika spelarna.
            partIdForSummoner = toPartId(matchId, summoner)
            summonerPartId.append(partIdForSummoner)
        else:
            break

def addMatchData(matchStats):
    conn = create_connection()
    cur = conn.cursor()
    for matches in matchStats:
        for match in matches:
            cur.executemany('INSERT INTO dataMatch(summonerName,matchId,kills,deaths,assists,champId,win) VALUES(?,?,?,?,?,?,?)', (match))




