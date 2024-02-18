from bs4 import BeautifulSoup
import requests
from ics import Calendar, Event
from datetime import datetime, timedelta
import re
import sqlite3

months_italian = ['gennaio', 'febbraio', 'marzo',
                  'aprile', 'maggio', 'giugno',
                  'luglio', 'agosto', 'settembre',
                  'ottobre', 'novembre', 'dicembre']

url = 'https://fip.it/risultati/?group=campionati-regionali&regione_codice=LO&comitato_codice=PBG&sesso=M&codice_campionato=2DM&codice_fase=1&codice_girone=58790&codice_ar=1&giornata=10'

r = requests.get(url)

main_soup = BeautifulSoup(r.content, 'html.parser')

results_calendar_class = 'results-calendar'
matches_class = 'results-matches__match'
team_class = 'team'
team_name_class = 'team__name'
team_points_class = 'team__points'
date_class = 'date'
time_class = 'time'
ref_class = 'ref'
info_class = 'info'
info_label_class = 'label'
info_value_class = 'value'

c = Calendar()

for result in main_soup.find_all('div', {'class': results_calendar_class})[0].find_all('a'):
    url = result['href']
    url = url.replace('®', '&reg')
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    matches = soup.find_all('div', {'class': matches_class})
    for i in range(len(matches)):
        team_elements = matches[i].find_all('div', {'class': team_class})
        date_element = matches[i].find('div', {'class': date_class})
        time_element = matches[i].find('div', {'class': time_class})
        ref_element = matches[i].find('div', {'class': ref_class})
        info_elements = matches[i].find_all('div', {'class': info_class})

        infos = dict()
        for info_element in info_elements:
            info_label = info_element.find('div', {'class': info_label_class})
            info_value = info_element.find('div', {'class': info_value_class})
            info_label = info_label.string.strip()
            if info_value is not None:
                info_value = ' '.join(info_value.string.strip().split())
                if len(info_value) == 0:
                    continue
                if info_label == 'Campo di gioco':
                    info_value = info_value.replace('( ', '(')
                infos[info_label] = info_value

        teams = ''
        for team_element in team_elements:
            if len(teams) != 0:
                teams += ' vs '
            team_name = team_element.find('div', {'class': team_name_class})
            team_points = team_element.find('div', {'class': team_points_class})
            team_name = team_name.string.strip()
            team_points = team_points.string.strip()
            teams += team_name
            if len(team_points) != 0:
                teams += f' ({team_points})'

        match_time = time_element.string.strip()
        match_date = date_element.string.strip()
        match_ref = ref_element.string.strip()

        for j in range(len(months_italian)):
            insensitive = re.compile(months_italian[j], re.IGNORECASE)
            if insensitive.search(match_date):
                match_date = insensitive.sub(format(j + 1, '02d'), match_date)
                break


        description = ''
        for label, value in infos.items():
            if label not in ['Campo di gioco']:
                description += f'{label}: {value}\n'


        e = Event()
        e.name = teams
        e.begin = datetime.strptime(match_date + ' ' + match_time, '%d %m %Y %H:%M')
        e.end = e.begin + timedelta(hours = 1)
        e.last_modified = datetime.now()
        e.location = infos['Campo di gioco']
        e.description = description
        e.uid = match_ref
        c.events.add(e)

with open('fip.ics', 'w') as my_file:
    my_file.writelines(c.serialize_iter())
