import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from openpyxl import Workbook

class NewsCrawler:

    def __init__(self):
        self.keyword = ''
        self.start_date = ''
        self.end_date = ''
        self.count = 0
        self.max_count = 0

    def get_last_page(self, url):

        """

        start 쿼리에 큰 값을 주어 제일 마지막 페이지를 얻어냄
        """  
        try:
            req = requests.get(url + '&start=99999')
            soup = BeautifulSoup(req.text, 'html.parser')
        except Exception as e:
            print('requests error : ', e) 
        
        page_lists = soup.select('#main_pack > div.api_sc_page_wrap > div > div > a')
        return int(page_lists[-1].text)

    def get_urls(self): 

        """

        한 페이지당 10개의 기사 URL이 있는데 페이지를 순차적으로 탐색하여 List에 넣어 반환
        """
        url = self.get_url()
        urls = set() # 중복 제거용

        last_page = self.get_last_page(url)    
        
        print("Collecting Urls start")

        for n in range(last_page): # 한 페이지당 약 10개의 기사 리스트
            start_index = n * 10 + 1
            try:
                req = requests.get(url + '&start=' + str(start_index))
                soup = BeautifulSoup(req.text, 'html.parser')
            except Exception as e:
                print('requests error : ', e) 

            results = soup.select("ul.list_news > li")

            for result in results :
                naver_urls = result.select('a')
                for naver_url in naver_urls:
                    if '네이버뉴스' in naver_url.get_text():
                        urls.add(naver_url['href'])
                    
            if len(urls) > self.max_count :
                break

        return list(urls)
        
    def get_reporter_name(self,content):
        p = re.compile('[ㄱ-ㅣ가-힣]+\s기자')
        m = p.findall(content)
        name = ''
        if m: name = m[-1]
        return name

    def get_url(self):
        return f'https://search.naver.com/search.naver?&where=news&query={self.keyword}&pd=3&ds={self.start_date}&de={self.end_date}'

    def get_reaction(self, url_cid, types):

        """
        뉴스 반응지표를 json으로 받아와 파싱한 후 반환
        """
        reactions = {
            'like': 0,'warm': 0,
            'sad': 0, 'angry': 0,
            'want': 0, 'surprise': 0,
            'cheer': 0, 'congrats': 0,
            'expect': 0, 
        }   

        if types == 'news':
            url = f'https://news.like.naver.com/v1/search/contents?q=NEWS[{url_cid}]|NEWS_SUMMARY[{url_cid}]|NEWS_MAIN[{url_cid}]'
        elif types == 'sports':
            url = f'https://sports.like.naver.com/v1/search/contents?q=SPORTS[{url_cid}]|NEWS_SUMMARY[{url_cid}]|NEWS_MAIN[{url_cid}]'
        elif types == 'entertain':
            url = f'https://news.like.naver.com/v1/search/contents?q=ENTERTAIN[{url_cid}]|NEWS_SUMMARY[{url_cid}]|NEWS_MAIN[{url_cid}]'
        
        try:
            req = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            jsons = req.json()['contents'][0]['reactions']
        except Exception as e:
            print("request Error : ", e)

        for json in jsons:
            reactions[json['reactionType']] = int(json['count'])

        return reactions

    def get_sports_crawl(self, req):

        soup = BeautifulSoup(req.text, 'html.parser')

        try:
            title = soup.select_one('#content > div > div.content > div > div.news_headline > h4').text
            press = soup.select_one('#pressLogo > a > img')['alt']
            date = soup.select_one('#content > div > div.content > div > div.news_headline > div > span:nth-child(1)').text
            date = date[5:]
            content = soup.select_one('#newsEndContents').text
            reporter = self.get_reporter_name(content) 
            url_cid = soup.select_one('#content > div > div.content > div > div.news_end_btn > div._reactionModule.u_likeit').attrs['data-cid']
            reactions = self.get_reaction(url_cid, 'sports')
        except Exception as e: 
            print(e)

        data = [
            self.keyword, title, content, press, req.url, date,
            reporter, reactions['like'], reactions['warm'],
            reactions['sad'], reactions['angry'], reactions['want'],
            reactions['surprise'], reactions['cheer'],
            reactions['expect'], reactions['congrats'],
        ]

        return data

    def get_news_crawl(self, req):
        
        soup = BeautifulSoup(req.text, 'html.parser')

        try:
            title = soup.select_one('#articleTitle').text
            press = soup.select_one('#main_content > div.article_header > div.press_logo > a > img')['title']
            date = soup.select_one('span.t11').text
            content = soup.select_one('#articleBodyContents').text
            reporter = self.get_reporter_name(content) 
            url_cid = soup.select_one('#spiLayer > div._reactionModule.u_likeit').attrs['data-cid']
            reactions = self.get_reaction(url_cid,'news')
        except Exception as e: 
            print(e)

        data = [
            self.keyword, title, content, press, req.url, date,
            reporter, reactions['like'], reactions['warm'],
            reactions['sad'], reactions['angry'], reactions['want'],
            reactions['surprise'], reactions['cheer'],
            reactions['expect'], reactions['congrats'],
        ]

        return data

    def get_entertain_crawl(self,req):
    
        soup = BeautifulSoup(req.text,'html.parser')

        try:
            title = soup.select_one('#content > div.end_ct > div > h2').text
            press = soup.select_one('#content > div.end_ct > div > div.press_logo > a > img')['alt']
            date = soup.select_one('#content > div.end_ct > div > div.article_info > span > em').text
            content = soup.select_one('#articeBody').text
            reporter = self.get_reporter_name(content)
            url_cid = soup.select_one('#ends_addition > div._reactionModule.u_likeit').attrs['data-cid']
            reactions = self.get_reaction(url_cid,'entertain')

        except Exception as e: 
            print(e)

        data = [
            self.keyword, title, content, press, req.url, date,
            reporter, reactions['like'], reactions['warm'],
            reactions['sad'], reactions['angry'], reactions['want'],
            reactions['surprise'], reactions['cheer'],
            reactions['expect'], reactions['congrats'],
        ]

        return data

    def write_to_excel(self, datas):

        try:
            df = pd.DataFrame(
                datas, 
                columns=[
                    '키워드', '기사 제목',
                    '내용', '언론사', 'URL', '발행 일자', 
                    '기자명', '좋아요', '훈훈해요', '슬퍼요',
                    '화나요', '후속기사 원해요', '놀랐어요',
                    '응원해요', '기대해요', '축하해요',
                ]
            )
            df.to_excel('news.xlsx', index=False)  
        except Exception as e:
            print("write excel error : ", e)

    def start(self):

        self.keyword = input('키워드를 입력하세요 : ')
        self.start_date = input('시작 기간을 입력하세요 YYYY.MM.DD : ')
        self.end_date = input('종료 기간을 입력하세요 YYYY.MM.DD : ')
        self.max_count = int(input('원하는 기사 개수를 입력하세요 : '))

        datas = []
        urls = self.get_urls()
    
        for url in urls: # URL을 가져와서 기사 크롤링 
            try:
                req=requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}) # 차단을 막기 위해 헤더 추가
            except Exception as e:
                print('requests error : ', e) 

            if 'https://news' in req.url:
                datas.append(self.get_news_crawl(req))
            elif 'https://sports' in req.url:
                datas.append(self.get_sports_crawl(req))
            elif 'https://entertain' in req.url:
                datas.append(self.get_entertain_crawl(req))
            else:
                continue
            
            self.count += 1
            print(str(self.count) + ' arcticles crwaling...')

            if self.max_count == self.count:
                break


        self.write_to_excel(datas)
        

if __name__ == "__main__":
    crawler = NewsCrawler()
    crawler.start()