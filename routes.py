from my_server import app
import sqlite3
import requests
from flask import Flask, render_template, request, abort, url_for, redirect, session, flash
import json
import os
import bcrypt
from my_server.database_handler import create_connection
from my_server import api
import numpy as np
#Globala variabler
api_key = 'RGAPI-d3cdab77-798d-4c06-b8c8-9a9a82639e51'
app.secret_key = "hemlig sdsdadfdddddfdxdddfaldla"
searchForm = ""


@app.route('/myPage/<username>',  methods = ['GET', 'POST'])
def myPage(username):
    if is_logged_in():

        summoner = getSummonerNameFromUsername(username)
        #Tar fram data om hur bra man är på spelet, (hur mycket man vinner/förlorar och vilken "rank" men är i spelet) rank är ett sätt att mäta hur bra man är på spelet.
        rankInfo = rankStatus(username)
        #Tittar om den finns någon data i databasen om det inte finns så kommer programmet krasha. Tittar även om det är fler än 10 matcher spelade,
        #om spelaren inte har mer än 10 matcher i databasen så finns inget konto med den Summonern. Dvs att man har spelat en match med denna spelare,
        #och datan har sparats därifrån.
        if existsInDataBase(summoner) == 1 and counterGames(summoner) >= 10:
            champStats = mostPlayed(summoner)

        else:
            champStats = []
        #Tittar om rankInfo är tom för om den är det så har spelaren inte spelat tillräckligt många games för att få en rank vilket kommer göra att den blir tom.
        wins = 0
        losses = 0
        winrate = 0
        if len(rankInfo) > 0:
            wins = rankInfo[0]['wins']
            losses = rankInfo[0]['losses']
            winrate = getWinrate(wins,losses)

        #tar fram datan sparad i sql.
        stats = getMatchStats(getSummonerNameFromUsername(username))
        totalMatchStats = getAllMatchStats(getSummonerNameFromUsername(username))
        return render_template('base_stats.html', summoner = summoner, champStats = champStats, rankInfo = rankInfo, stats = stats, winrate = winrate, totalMatchStats = totalMatchStats)
    else:
        return render_template('login.html')


@app.route('/myProfile', methods= ['GET', 'POST'])
def myProfile():
    global searchForm
    searchForm = ""
    username = session['username']
    return redirect(url_for('myPage', username = username))


@app.route('/searchUser', methods= ['GET', 'POST'])
def searchUser():
    username = request.form['form1']
    if usernameExist(username) == 1:
        summoner = getSummonerNameFromUsername(username)
        return redirect(url_for('page', summoner = summoner, username = username))
    return 1

@app.route('/page/<summoner>/<username>', methods = ['GET', 'POST'])
def page(summoner, username):
    global searchForm
    stats = getMatchStats(summoner)
    champStats = mostPlayed(summoner)
    totalMatchStats = getAllMatchStats(summoner)
    rankInfo = rankStatus(username)
    searchForm += username
    return render_template('base_stats.html', summoner = summoner, rankInfo = rankInfo, stats = stats, champStats = champStats, totalMatchStats = totalMatchStats)





@app.route('/loginAccount', methods = ['GET', 'POST'])
def loginAccount():
    if request.method == 'POST':
        username = request.form['inputUsername']
        password_try = request.form['inputPassword']
        data = loginInformation()
        returnStatement = False
        for d in data:
            if d[0] == username and bcrypt.hashpw(password_try.encode('utf-8'), d[1]) == d[1]:
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('myPage', username = username), code = 307)
            else:
                returnStatement = True
        if returnStatement:
            flash('Fel lösenord eller användarnamn!', 'info')
            return redirect(url_for('login'))
    else:
        abort(401)


@app.route('/login')
@app.route('/')
def login():
    if is_logged_in():
        return redirect(url_for('myPage', username = session['username']))
    return render_template('login.html')

@app.route('/create', methods = ['GET', 'POST'])
def create():
    if request.method == 'POST' or request.method =='GET':
        return render_template('create.html')


@app.route('/accountCreation', methods = ['GET', 'POST'])
def createAccount():
    if request.method == 'POST':
        username = request.form['inputUsername']
        password = request.form['inputPassword']
        confirmPassword = request.form['inputPassword2']
        summoner = request.form['inputSummoner']
        #Skapar en lista med tuples över alla användarnamn
        users = listUsernames()
        #Variabel för att veta avd jag ska returna
        returnStatement = False

        #Tittar om lösenordet matchar kontrollrutan
        if password != confirmPassword:
            flash('Lösenorden matchar inte!')
            returnStatement = True
        #Om lösenordet eller anndar namnet är mindre än 5
        if len(password)< 5 or len(username) < 5:
            flash('Lösenordet eller användrnamnet är för kort!', 'info')
            returnStatement = True
        #Loopar igenom all usernames i databasen
        for name in users:
            if username == name[0]:
                flash('Användarnamnet är upptaget!', 'info')
                returnStatement = True

        if isSummoner(summoner) == False:
            flash(f'There are no summoner named {summoner}!', 'info')
            returnStatement = True

        if returnStatement:
            return redirect(url_for('create'))
        else:
            my_salt = bcrypt.gensalt(rounds=12)
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), my_salt)
            addToTable(username,hashed_pw,summoner)
            return render_template('login.html')
    else:
        abort(401)


#Denna funktion tittar om det finns ett användarnamn med det som skrevs in vid summoner name(Summoner är spelets namn för spelarnas användarnamn)
def isSummoner(summonerName):
    url = f'https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summonerName}/?api_key={api_key}'
    res = requests.get(url)
    #Om den inte hittar någon url vid detta namn så kommer status_coden vara 404
    if res.status_code == 404:
        return False
    else:
        return True

@app.route('/logout')
def logout():
    if not is_logged_in():
        abort(401)
    else:
        session['logged_in'] = False
        session.pop('username', None)
        flash('Du är utloggad')
        return render_template('login.html')






#Lägger till datan till sql databasen
def addToTable(username,hashed_pw,summoner):
    conn = create_connection()
    cur = conn.cursor()
    #Tar fram ids som kommer behövas för att navigerar runt på APIn.
    url = f'https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner}/?api_key={api_key}'
    res = requests.get(url)
    res_json = res.json()
    summonerId = res_json['id']
    puuid = res_json['puuid']
    accountId = res_json['accountId']
    data = [(username,hashed_pw,summoner,summonerId,puuid,accountId)]

    cur.executemany('INSERT INTO users(username,key,summoner,summonerId,puuid,accountId) VALUES(?,?,?,?,?,?)', (data))
    conn.commit()

def loginInformation():
    conn = create_connection()
    cur = conn.cursor()
    sql = 'SELECT username,key FROM users'
    cur.execute(sql)
    data = cur.fetchall()
    return data

def is_logged_in():
    if 'logged_in' in session.keys() and session['logged_in'] == True:
        return True
    return False

def listUsernames():
    conn = create_connection()
    sql = 'SELECT username FROM users'
    cur = conn.cursor()
    cur.execute(sql)
    usernames = cur.fetchall()
    return usernames


#
#
#
#
#API FUNKTIONER!
#
#
#
#Gör om id på championen som skickades till namnet på championen, t.ex 1 retunerar 'Annie'
def champIdToName(id):
    url = 'http://ddragon.leagueoflegends.com/cdn/10.23.1/data/en_US/champion.json'
    data = urlToJson(url)
    name = ''
    idStr = str(id)
    #Tittar på alla championId som finns i denna databas och jämför den med det som skickades in.
    for champName in data['data']:
        if data['data'][champName]['key'] == idStr:
            #tar fram namnet för den ID
            name = champName
            break
    return name





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
        x = [participantId, kills, deaths, assists, champId, win, matchId]
        matchStats.append(x)
    #summonerName = matchDatan_json['participantIdentities'][partId]['summonerName']
    return matchStats

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
    #Om man tittar på data och skriver ut det kan man testa sig till att data[0][4] kommer vara "summonerid"

    url = f'https://euw1.api.riotgames.com/lol/league/v4/entries/by-summoner/{data[0][4]}/?api_key={api_key}'
    rankData = requests.get(url)
    rankData_json = rankData.json()

    return rankData_json



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

def getSummonerNameFromUsername(username):
    conn = create_connection()
    cur = conn.cursor()
    sql = f'SELECT summoner FROM users WHERE username = "{username}"'
    cur.execute(sql)
    summoners = cur.fetchall()
    summoner = summoners[0][0]
    return summoner

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
    #Det finns hundra matches som sparas, vilket gör att denna loop kommer köras 100 gånger.
    for match in matchInfo:
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
            creation = match['timestamp']
            stats[counterSummoner].append(creation)
            counterSummoner += 1

        #lägger till stats, vilket är stats för en match

        matchStats.append(stats)
    return matchStats


def getWinrate(wins,losses):
    winrate = wins/(losses+wins)
    winrate *=100
    winrateAvrund = int(round(winrate))
    return winrateAvrund

def addMatchData(matches):
    conn = create_connection()
    cur = conn.cursor()
    for match in matches:
        for player in match:
            name = champIdToName(player[4])
            tuplePlayer = [(player[0],player[7],player[6],player[1],player[2],player[3],name,player[5],player[8])]
            cur.executemany('INSERT INTO dataMatch(partId,summonerName,matchId,kills,deaths,assists,champName,win,creation) VALUES(?,?,?,?,?,?,?,?,?)', (tuplePlayer))
    conn.commit()

@app.route('/update', methods = ['GET', 'POST'])
def update():
    if request.method == 'POST':
        if searchForm == "":
            username = session['username']
        else:
            username = searchForm
        #tar fram wins och losses bland annat
        rankInfo = rankStatus(username)
        #Här sparas de nya matcherna
        newGames = []
        #Tar fram namnet man har i spelet.
        summoner = getSummonerNameFromUsername(username)

        championData = winrateForChampion(summoner)
        #tittar om summonern finns i databasen, retunerar 0 eller 1
        exist = existsInDataBase(summoner)

        #Tittar på de senate matcherna i databasen om det var vinst eller förlust

        #matchId och overall stats från api
        matchInfo = matchesPlayed(username)

        countGames = counterGames(summoner)
        #Om spelaren finns i databasen och spelaren har mer eller lika med 10 matcher i databasen, för annars om man har spelet ett game med någon
        # som finns i databasen så kommer den spelaren redan ha ett game sparat, men man vill se mer än ett game.
        if exist == 1 and countGames >= 10:
            matchId = matchIdLatestGame(summoner)
            #If satsen tittar om matchId på den senaste matchen i sql databasen är samma som den senaste matchen i API
            if matchId != matchInfo['matches'][0]['gameId']:
                counter = 0
                for match in matchInfo['matches']:
                    #Laddar in de senaste matcherna tills den matchen som fanns i databasen sedan innan hittas eller en counter blir större än 10
                    if match['gameId'] != matchId and counter <10:
                        newGames.append(match)
                        counter += 1
                    else:
                        break
                matches = toRelevantData(newGames)
                addMatchData(matches)
        #Om den inte finns med i data basen läggs de senaste 10 matcherna in i databasen.
        #om finns i databas men har under 10 matcher? De senaste matcherna läägas till, om det inte blir över 10,
        #så ska matcherna som spelades innan den  matchen som spelades sists läggas till tills det blir 10.
        else:
            games = []
            for match in matchInfo['matches']:
                if countGames < 10:
                    games.append(match)
                    countGames +=1
                else:
                    break
            matches = toRelevantData(games)
            addMatchData(matches)

        #ta fram datan ur databasen.
        #partId = getPartId(summoner)
        #Stats från sql databsen
        stats = getMatchStats(summoner)




        winrate = 0
        if len(rankInfo) > 0:
            wins = rankInfo[0]['wins']
            losses = rankInfo[0]['losses']
            winrate = getWinrate(wins,losses)
        #Tar fram de karaktärerna man har spelat mest i de matcherna som är registerade i databasen
        champStats = mostPlayed(summoner)
        #Skapar en array för winrate på spelare


        totalMatchStats = getAllMatchStats(summoner)

        return render_template('base_stats.html', champStats = champStats, stats = stats, summoner = summoner, rankInfo = rankInfo, winrate = winrate,totalMatchStats = totalMatchStats)
    else:
        abort(401)

@app.route('/chartData', methods = ['GET', 'POST'])
def chartData():
    username = session['username']
    summoner = getSummonerNameFromUsername(username)
    exist = existsInDataBase(summoner)
    returnData = []
    if exist == 1:
        #Tittar på de senaste matcherna i databasen om det var vinst eller förlust
        winOrLoss = latestGames(summoner)
        counter = 0
        for match in winOrLoss:
            if counter < 10:
                returnData.append(match)
                counter +=1
            else:
                break
    return json.dumps(returnData)

#
#
#
#SQL kommandon
#
#
#

#Tar fram alla personers stats i en match, alltså alla summoners stats, inte bara den som är inloggad.
def getAllMatchStats(summoner):
    matchStats = []
    conn = create_connection()
    cur = conn.cursor()
    sql = f'SELECT matchId from dataMatch where upper(summonerName) = upper("{summoner}") group by matchId'
    cur.execute(sql)
    matchIds = cur.fetchall()
    for i in range(len(matchIds)-1, -1, -1):
        ids = matchIds[i]
        sql = f'select * from dataMatch where matchId = "{ids[0]}"'
        cur.execute(sql)
        statsMatch = cur.fetchall()
        matchStats.append(statsMatch)
    return matchStats


#Används ej fick inte sql att fungera
def winrateForChampion(summoner):
    championData = []
    conn = create_connection()
    cur = conn.cursor()
    sql =f'Select champName, count(win),(Select count(win) where win = 1) from dataMatch where upper(summonerName) = upper("{summoner}") group by champName order by count(*) desc'
    cur.execute(sql)
    data = cur.fetchall()
    counter = 0
    for champ in data:
        if counter < 4:
            name = champ[0]
            if champ[2] == None:
                wins = 0
            else:
                wins = champ[2]

            losses = champ[1] - wins
            counter += 1
            winrate = getWinrate(wins, losses)
            champion = [name, winrate]
            championData.append(champion)

        else:
            break
    return championData

#tittar på alla mactcher som spelats och sorterar dem i ordningen dem spelades. Det som retuneras är en array av 0 och 1 då 1 är vinst 0 eller loss.
def latestGames(summoner):
    conn = create_connection()
    cur = conn.cursor()
    sql = f'select win from dataMatch where upper(summonerName) = upper("{summoner}") order by creation desc'
    cur.execute(sql)
    data = cur.fetchall()
    return data

#Tar fram de 4 mest spelade karaktärerna för en viss summoenr
def mostPlayed(summoner):
    conn = create_connection()
    cur = conn.cursor()
    champions = []
    sql = f'SELECT champName, COUNT(*), AVG(kills), AVG(deaths), AVG(assists) from dataMatch where upper(summonerName) = upper("{summoner}") group by champName ORDER BY COUNT(*) desc'
    cur.execute(sql)
    data = cur.fetchall()
    for x in range(4):
        champions.append(data[x])
    return champions

def summonerToUsername(summoner):
    conn = create_connection()
    cur = conn.cursor()
    sql =f'select username from users where upper(summoner) = upper("{summoner}")'
    cur.execute(sql)
    username = cur.fetchall()
    return username


def counterGames(summoner):
    conn = create_connection()
    cur = conn.cursor()
    sql = f'SELECT COUNT(matchId) from dataMatch WHERE upper(summonerName) = upper("{summoner}")'
    cur.execute(sql)
    counter = cur.fetchall()[0][0]
    return counter

def existsInDataBase(summoner):
    conn = create_connection()
    cur = conn.cursor()
    sql = f'SELECT EXISTS(SELECT * FROM dataMatch WHERE upper(summonerName)= upper("{summoner}"))'
    cur.execute(sql)
    exists = cur.fetchall()[0][0]
    return exists

def getMatchStats(summoner):
    conn = create_connection()
    cur = conn.cursor()
    sql = f'select * from dataMatch WHERE upper(summonerName) = upper("{summoner}") ORDER BY creation DESC'
    cur.execute(sql)
    stats = cur.fetchall()
    return stats

def usernameExist(username):
    conn = create_connection()
    cur = conn.cursor()
    sql = f'SELECT EXISTS(SELECT * FROM users WHERE upper(username)= upper("{username}"))'
    cur.execute(sql)
    exists = cur.fetchall()[0][0]
    return exists

def matchIdLatestGame(summoner):
    conn = create_connection()
    cur = conn.cursor()
    sql = f'SELECT distinct matchId FROM dataMatch WHERE creation = (SELECT MAX(creation) FROM dataMatch WHERE upper(summonerName) = upper("{summoner}")) GROUP BY matchId'
    cur.execute(sql)
    matchId = cur.fetchall()[0][0]
    return matchId

