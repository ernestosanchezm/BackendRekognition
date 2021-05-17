from selenium import webdriver
import pandas as pd
import time

web = 'https://sports.tipico.de/en/all/football/spain/la-liga'
path = 'chromedriver'
driver = webdriver.Chrome(path)
driver.get(web)

time.sleep(5) 
accept = driver.find_element_by_xpath('//*[@id="_evidon-accept-button"]')
accept.click()

teams = []
x12 = [] 
odds_events = []

box = driver.find_element_by_xpath('//div[contains(@testid, "Program_SELECTION")]') 

sport_title = box.find_elements_by_class_name('SportTitle-styles-sport')

for sport in sport_title:   
    if sport.text == 'Football':
        parent = sport.find_element_by_xpath('./..') 
        grandparent = parent.find_element_by_xpath('./..') 
      
        single_row_events = grandparent.find_elements_by_class_name('EventRow-styles-event-row')
      
        for match in single_row_events:
            
            odds_event = match.find_elements_by_class_name('EventOddGroup-styles-odd-groups')
            odds_events.append(odds_event)
           
            for team in match.find_elements_by_class_name('EventTeams-styles-titles'):
                teams.append(team.text)
            
        for odds_event in odds_events:
            for n, box in enumerate(odds_event):
                rows = box.find_elements_by_xpath('.//*')
                if n == 0:
                    x12.append(rows[0].text)

driver.quit()
dict_gambling = {'Teams': teams, '1x2': x12}
df_gambling = pd.DataFrame.from_dict(dict_gambling)
print(df_gambling)

