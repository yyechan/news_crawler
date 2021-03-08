import requests
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from openpyxl import Workbook


class NewsCrawler:

    def __init__(self):
        self.keyword      = '삼성전자'
        self.startDate    = '2021.01.01'
        self.endDate      = '2021.01.30'
        self.pattern      = "https:\/\/news\.naver\.com\/main\/read\.nhn\?" # 정규 표현식 매칭을 위한 패턴
        self.chromedriver = "C:/webs/chromedriver.exe"
        self.count        = 0

    def getLastPage(self,URL) :
        req = requests.get(URL + '&start=99999')
        soup = BeautifulSoup(req.text, 'html.parser')
        page_lists = soup.select('#main_pack > div.api_sc_page_wrap > div > div > a')
        return int(page_lists[-1].text)

    def getReporterName(self,content):
        p = re.compile('[ㄱ-ㅣ가-힣]+\s기자')
        m = p.findall(content)
        name = ''
        if m : name = m[-1]
        return name

    def getURL(self):
        return f'https://search.naver.com/search.naver?&where=news&query={self.keyword}&pd=3&ds={self.startDate}&de={self.endDate}'

    
    def start(self) :

        webdriver_options = webdriver.ChromeOptions()
        webdriver_options .add_argument('headless')

        driver = webdriver.Chrome(self.chromedriver, options=webdriver_options)

        wb = Workbook() 
        sheet1 = wb.active
        sheet1.append(['뉴스 제목','내용','언론사','URL','발행 일자','기자명','키워드','좋아요','훈훈해요','슬퍼요','화나요','후속기사 원해요'])

        URL = self.getURL()

        lastPage = self.getLastPage(URL)
        
        for n in range(lastPage) : # 한 페이지당 약 10개의 기사 리스트 출력

            startIndex = n*10 +1
            req = requests.get(URL +'&start=' +str(startIndex))
            soup = BeautifulSoup(req.text,'html.parser')

            results = soup.find_all('a', {'href' : re.compile(self.pattern)}) # 기사 중 네이버 뉴스 URL만 가져옴 

            for result in results: # URL을 가져와서 기사 크롤링 
                req = requests.get(result['href'], headers={'User-Agent':'Mozilla/5.0'}) # 차단을 막기 위해 헤더 추가
                soup = BeautifulSoup(req.text,'html.parser')
                
                try :
                    url = result['href']
                    title = soup.select_one('#articleTitle').text
                    press = soup.select_one('#main_content > div.article_header > div.press_logo > a > img')['title']
                    date = soup.select_one('span.t11').text
                    content = soup.select_one('#articleBodyContents').text
                    reporter = self.getReporterName(content)
                except Exception as e : 
                    print(e)
                    continue

                driver.get(url) # 셀레니움을 이용한 
                reaction1 = driver.find_element_by_css_selector('#spiLayer > div._reactionModule.u_likeit > ul > li.u_likeit_list.good > a > span.u_likeit_list_count._count').text    
                reaction2 = driver.find_element_by_css_selector('#spiLayer > div._reactionModule.u_likeit > ul > li.u_likeit_list.warm > a > span.u_likeit_list_count._count').text
                reaction3 = driver.find_element_by_css_selector('#spiLayer > div._reactionModule.u_likeit > ul > li.u_likeit_list.sad > a > span.u_likeit_list_count._count').text
                reaction4 = driver.find_element_by_css_selector('#spiLayer > div._reactionModule.u_likeit > ul > li.u_likeit_list.angry > a > span.u_likeit_list_count._count').text
                reaction5 = driver.find_element_by_css_selector('#spiLayer > div._reactionModule.u_likeit > ul > li.u_likeit_list.want > a > span.u_likeit_list_count._count').text
                
                sheet1.append([
                    title, content, press, url,
                    date, reporter, self.keyword,
                    reaction1, reaction2, reaction3,
                    reaction4, reaction5,
                ])
                wb.save('test1.xlsx')
                self.count += 1
                print( str(self.count) + ' arcticles complete...' )

        
if __name__ == "__main__":
    crawler = NewsCrawler()
    crawler.start()