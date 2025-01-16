import os
import time
import json

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from tqdm import tqdm
import pyperclip
import logging


def save_data(data, output_dir, file_name="scraped_data.json"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, file_name)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def open_browser():
    op = webdriver.ChromeOptions()
    chrome_service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=chrome_service, options=op)
    logging.info('크롬 브라우저 열기')
    return driver


def naver_login(naver_id, naver_pw):
    driver.get("https://nid.naver.com/nidlogin.login")

    try:
        id_box = driver.find_element(By.ID, 'id')
        pw_box = driver.find_element(By.ID, 'pw')
        pyperclip.copy(naver_id)
        id_box.send_keys(Keys.CONTROL + 'v')
        time.sleep(0.5)

        pyperclip.copy(naver_pw)
        pw_box.send_keys(Keys.CONTROL + 'V')  # 네이버 Password
        pw_box.send_keys(Keys.RETURN)  # 로그인 버튼 대신 Enter 키
        pyperclip.copy('secure')

        # 최대 대기 시간 설정 : 페이지가 다 로드되지 않았을 때 element를 찾다가
        # 오류가 나는 것을 방지하기 위한 설정. 최대 50초까지 기다리고,
        # 그 이전에 페이지가 로드되면 자동으로 다음 명령을 실행한다.
        driver.implicitly_wait(30)

        logging.info('네이버 로그인')

    except:
        logging.info('네이버 로그인 실패')
        print("no such element")  # 예외처리


def scraping():
    try:
        '''
        데이터 추출 목록
        1. 제목 (str)
        2. 질문 작성자 명 (str)
        3. 본문 텍스트 (list:str)
        4. 본문 이미지 url (list:str)
        5. 답변자 & 내용 (dict:str)
        '''

        question_data = {}

        # 제목 추출
        title = driver.find_element(By.CSS_SELECTOR, "h3.title_text").text

        # 작성자 추출
        author = driver.find_element(By.CSS_SELECTOR, ".nickname").text

        # 본문 텍스트 추출
        # time.sleep(1)
        body_text_elements = driver.find_elements(By.CSS_SELECTOR, '.se-component.se-text .se-text-paragraph')

        body_text_list = []
        for element in body_text_elements:
            text = element.text
            if len(text) > 0:  # 줄바꿈 제거
                body_text_list.append(text)

        # 본문 이미지 URL 추출
        # time.sleep(1)
        image_elements = driver.find_elements(By.CSS_SELECTOR, '.se-component.se-image img.se-image-resource')
        body_image_list = []
        for element in image_elements:
            body_image_list.append(element.get_attribute('src'))

        # 답변 추출
        comment_elements = driver.find_elements(By.CSS_SELECTOR, ".CommentItem")
        comments = []
        for comment in comment_elements:
            comment_author = comment.find_element(By.CSS_SELECTOR, ".comment_nickname").text.strip()
            content = comment.find_element(By.CSS_SELECTOR, ".text_comment").text.strip()
            comments.append({"author": comment_author, "content": content})

        question_data['title'] = title
        question_data['author'] = author
        if len(body_text_list) != 0:
            question_data['body_texts'] = body_text_list
        if len(body_image_list) != 0:
            question_data['body_images'] = body_image_list
        if len(comments) != 0:
            question_data['comments'] = comments

        logging.info(f'데이터 수집')
        return question_data

    except:
        logging.info('데이터 수집 실패')
        return None


def open_article(article, page_num, post_num):
    try:
        article.send_keys(Keys.CONTROL + "\n")
        logging.info(f'{page_num}페이지 {post_num}번째 게시물 열기')
        return True
    except:
        logging.info(f'{page_num}페이지 {post_num}번째 게시물 열기 실패')
        return False


def switch_window(forward):
    ind = -1 if forward else 0
    try:
        driver.switch_to.window(driver.window_handles[ind])
        time.sleep(0.5)
        logging.info(f'탭 이동')
        return True
    except:
        logging.info(f'탭 이동 실패')
        return False


def switch_iframe():
    driver.implicitly_wait(30)
    try:
        driver.switch_to.frame("cafe_main")
        logging.info('iframe 이동')
        return True
    except:
        logging.info('iframe 이동')
        return False


def close_article():
    try:
        driver.close()
        time.sleep(0.5)
        logging.info('게시물 닫기')
        return True
    except:
        logging.ingo('게시물 닫기 실패')
        return False


def web_scraping(cafe_url, max_pages, menu_name, output_dir, data_file_name):
    time.sleep(2)
    driver.get(cafe_url)
    time.sleep(2)
    logging.info('Accessed to url')

    menu = driver.find_element(By.XPATH, f'//a[contains(text(), "{menu_name}")]')
    menu.click()
    time.sleep(2)
    driver.switch_to.frame("cafe_main")
    logging.info('Accessed to board menu')

    scraped_data = []
    with tqdm(total=max_pages) as pbar:
        while pbar.n < max_pages:

            pbar.update(1) # pbar.n : 현재 page 번호

            page_start_time = time.time()
            page_scrape_time = []

            # 게시글 추출
            articles = driver.find_elements(By.CSS_SELECTOR, "a.article")

            for i, article in enumerate(articles):
                post_start_time = time.time()

                if pbar.n == 1 and i < 8:
                    continue

                if not open_article(article, pbar.n, i):        # 게시물이 안 열리면 다음 게시물 열기 시도
                    continue

                if not switch_window(forward=True):             # 게시물을 새 탭에서 열었는데 탭 이동이 안 될 경우 게시판으로 이동
                    switch_window(forward=False)
                    continue

                if not switch_iframe():                         # 게시물 열었는데 iframe 못 찾을 경우 끄고 다음 게시물
                    close_article()
                    switch_window(forward=False)
                    switch_iframe()
                    continue

                data = scraping()
                if data:
                    scraped_data.append(data)

                close_article()
                switch_window(forward=False)
                switch_iframe()

                page_scrape_time.append(time.time() - post_start_time)

            page_total_time = time.time() - page_start_time
            avg_post_time = sum(page_scrape_time) / len(page_scrape_time) if page_scrape_time else 0
            print(f"Page {pbar.n}: Average post scrape time: {avg_post_time:.2f}s, Total page time: {page_total_time:.2f}s")

            try:
                page_button = driver.find_element(By.CSS_SELECTOR, f"a[href*='search.page={pbar.n + 1}']")
                page_button.click()
                driver.implicitly_wait(60)
                logging.info(f'{pbar.n + 1} 페이지로 이동')
            except:
                logging.info(f'{pbar.n + 1} 페이지로 이동 실패')

            try:
                save_data(scraped_data, output_dir, data_file_name)
                logging.info('데이터 저장')
            except:
                logging.info('데이터 저장 실패')


if __name__ == '__main__':
    login_kwargs = {
        'naver_id': "YOUR_ID",
        'naver_pw': "YOUR_PASSWORD"
    }

    scraping_kwargs = {
        'cafe_url': "https://cafe.naver.com/plantremarket",
        'menu_name': "식물관련질문",

        'output_dir' : './data',
        'data_file_name' : 'scraped_data.json',
        'max_pages': 30,
    }

    logging.basicConfig(
        format='%(asctime)s: %(message)s',
        filename='scraping.log',
        filemode='w',
        level=logging.INFO)

    # 셀레니움 브라우저 오픈
    driver = open_browser()

    # 최초 로그인
    naver_login(**login_kwargs)

    # 스크래핑 실행
    web_scraping(**scraping_kwargs)