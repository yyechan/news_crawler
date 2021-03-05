import requests
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from openpyxl import Workbook


class NewsCrawler:

    def __init__(self):
        self.keyword      = ''
        self.startDate    = ''
        self.endDate      = ''
        self.pattern      = "https:\/\/news\.naver\.com\/main\/read\.nhn\?" # 정규 표현식 매칭을 위한 패턴
        self.count        = 0
        self.max_count    = 0

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

    
    def getReaction(self,url_cid):

        reactions = {'like' : 0,'warm' : 0 , 'sad' : 0, 'angry' : 0, 'want' : 0}
        URL = f'https://news.like.naver.com/v1/search/contents?q=NEWS[{url_cid}]|NEWS_SUMMARY[{url_cid}]|NEWS_MAIN[{url_cid}]'
        req = requests.get(URL,headers={'User-Agent':'Mozilla/5.0'} )
        jsons = req.json()['contents'][0]['reactions']

        for json in jsons :
            reactions[json['reactionType']] = int(json['count'])

        return reactions



    def start(self) :

        self.keyword = input('키워드를 입력하세요 : ')
        self.startDate = input('시작 기간을 입력하세요 YYYY.MM.DD : ')
        self.endDate = input('종료 기간을 입력하세요 YYYY.MM.DD : ')
        self.max_count = int(input('원하는 기사 개수를 입력하세요 : '))

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
                req=requests.get(result['href'],headers={'User-Agent':'Mozilla/5.0'}) # 차단을 막기 위해 헤더 추가
                soup = BeautifulSoup(req.text,'html.parser')
                
                try :
                    url       = result['href']
                    title     = soup.select_one('#articleTitle').text
                    press     = soup.select_one('#main_content > div.article_header > div.press_logo > a > img')['title']
                    date      = soup.select_one('span.t11').text
                    content   = soup.select_one('#articleBodyContents').text
                    reporter  = self.getReporterName(content)


                     # 기사 반응은 실시간으로 렌더링 되므로 새로운 url으로 json을 받아옴 
                    url_cid   = soup.select_one('#spiLayer > div._reactionModule.u_likeit').attrs['data-cid']
                    reactions = self.getReaction(url_cid)
                    
                except Exception as e : 
                    print(e)
                    continue
                
                sheet1.append([title,content,press,url,date,reporter,
                                self.keyword,reactions['like'],reactions['warm'],
                                reactions['sad'],reactions['angry'],reactions['want']])

                wb.save('test1.xlsx')
                self.count += 1
                print( str(self.count) + ' arcticles complete...' )

                if self.max_count == self.count :
                    return

        
if __name__ == "__main__":
    crawler = NewsCrawler()
    crawler.start()