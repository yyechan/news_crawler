import requests
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from openpyxl import Workbook

def getLastPage() :
    req = requests.get(URL + '&start=99999')
    soup = BeautifulSoup(req.text, 'html.parser')
    page_lists = soup.select('#main_pack > div.api_sc_page_wrap > div > div > a')
    return int(page_lists[-1].text)

def getReporterName(content):
    p = re.compile('[ㄱ-ㅣ가-힣]+\s기자')
    m = p.findall(content)
    name = ''
    if m : name = m[-1]
    return name


chromedriver= "C:/webs/chromedriver.exe"
driver = webdriver.Chrome(chromedriver)
wb = Workbook() 
sheet1 = wb.active
sheet1.append(['뉴스 제목','내용','언론사','URL','발행 일자','기자명','키워드','좋아요','훈훈해요','슬퍼요','화나요','후속기사 원해요'])

keyword     = '삼성전자'
startDate   = '2021.01.01'
endDate     = '2021.01.30'

URL = f'https://search.naver.com/search.naver?&where=news&query={keyword}&pd=3&ds={startDate}&de={endDate}'

PATTERN = "https:\/\/news\.naver\.com\/main\/read\.nhn\?" # 정규 표현식 매칭을 위한 패턴


lastPage = getLastPage()

for n in range(lastPage) : # 한 페이지당 약 10개의 기사 리스트 출력

    startIndex = n*10 +1
    req = requests.get(URL +'&start=' +str(startIndex))
    soup = BeautifulSoup(req.text,'html.parser')

    results = soup.find_all('a', {'href' : re.compile(PATTERN)}) # 기사 중 네이버 뉴스 URL만 가져옴 

    for result in results: # URL을 가져와서 기사 크롤링 
        req=requests.get(result['href'],headers={'User-Agent':'Mozilla/5.0'}) # 차단을 막기 위해 헤더 추가
        soup = BeautifulSoup(req.text,'html.parser')
        
        url       = result['href']
        title     = soup.select_one('#articleTitle').text
        press     = soup.select_one('#main_content > div.article_header > div.press_logo > a > img')['title']
        date      = soup.select_one('span.t11').text
        content   = soup.select_one('#articleBodyContents').text
        reporter  = getReporterName(content)
        
        driver.get(url) # 기사 반응은 실시간으로 렌더링 되므로 셀레니움을 사용함 
        reaction1 = driver.find_element_by_css_selector('#spiLayer > div._reactionModule.u_likeit > ul > li.u_likeit_list.good > a > span.u_likeit_list_count._count').text    
        reaction2 = driver.find_element_by_css_selector('#spiLayer > div._reactionModule.u_likeit > ul > li.u_likeit_list.warm > a > span.u_likeit_list_count._count').text
        reaction3 = driver.find_element_by_css_selector('#spiLayer > div._reactionModule.u_likeit > ul > li.u_likeit_list.sad > a > span.u_likeit_list_count._count').text
        reaction4 = driver.find_element_by_css_selector('#spiLayer > div._reactionModule.u_likeit > ul > li.u_likeit_list.angry > a > span.u_likeit_list_count._count').text
        reaction5 = driver.find_element_by_css_selector('#spiLayer > div._reactionModule.u_likeit > ul > li.u_likeit_list.want > a > span.u_likeit_list_count._count').text
        
        sheet1.append([title,content,press,url,date,reporter,keyword,reaction1,reaction2,reaction3,reaction4,reaction5])
        wb.save('test.xlsx')
        
