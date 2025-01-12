import os
import time
import json
from collections import deque

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from tqdm import tqdm
import pyperclip


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
    return driver


def naver_login(naver_id, naver_pw):
    driver.get("https://nid.naver.com/nidlogin.login")

    try:
        id_box = driver.find_element(By.ID, 'id')
        pw_box = driver.find_element(By.ID, 'pw')
        pyperclip.copy(naver_id)
        id_box.send_keys(Keys.CONTROL + 'v')
        time.sleep(1)

        pyperclip.copy(naver_pw)
        pw_box.send_keys(Keys.CONTROL + 'V')  # 네이버 Password
        pw_box.send_keys(Keys.RETURN)  # 로그인 버튼 대신 Enter 키
        pyperclip.copy('secure')

        # 최대 대기 시간 설정 : 페이지가 다 로드되지 않았을 때 element를 찾다가
        # 오류가 나는 것을 방지하기 위한 설정. 최대 50초까지 기다리고,
        # 그 이전에 페이지가 로드되면 자동으로 다음 명령을 실행한다.
        driver.implicitly_wait(50)

    except:
        print("no such element")  #예외처리


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
        title = driver.find_element(By.XPATH, '//*[@id="app"]/div/div/div[2]/div[1]/div[1]/div/div/h3').text

        # 작성자 추출
        author = driver.find_element(By.CSS_SELECTOR, ".nickname").text

        # 본문 텍스트 추출
        # time.sleep(1)
        body_text_elements = driver.find_elements(By.CSS_SELECTOR, '.se-component.se-text .se-text-paragraph')
        body_text_list = []
        for element in body_text_elements:
            text = element.text
            if len(text) > 0: # 줄바꿈 제거
                body_text_list.append(text)

        # 본문 이미지 URL 추출
        # time.sleep(1)
        image_elements = driver.find_elements(By.CSS_SELECTOR, '.se-component.se-image img.se-image-resource')
        body_image_list = []
        for element in image_elements:
            body_image_list.append(element.get_attribute('src'))

        # 답변 추출
        # time.sleep(1)  # 댓글 데이터 로드 대기
        comment_elements = driver.find_elements(By.CSS_SELECTOR, ".CommentItem")
        comments = []
        for comment in comment_elements:
            time.sleep(0.5)
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

        return question_data

    except:
        return None


def web_scraping(cafe_url, max_pages, menu_name, output_dir, data_file_name):
    # 로그인 후 대기
    time.sleep(2)

    # 카페 접속
    driver.get(cafe_url)
    time.sleep(2)

    # 게시판 클릭
    menu = driver.find_element(By.XPATH, f'//a[contains(text(), "{menu_name}")]')
    menu.click()
    time.sleep(2)

    # cafe_main으로 ifram 이동
    driver.switch_to.frame("cafe_main")

    # 페이지네이션
    i = 1
    scraped_data = []
    with tqdm(total=max_pages) as pbar:
        while pbar.n < max_pages:

            for j in range(1, 16):
                try:
                    # 게시물 새 창에서 열기 -> 창 이동
                    page_button = driver.find_element(By.XPATH,
                                                      f'//*[@id="main-area"]/div[4]/table/tbody/tr[{j}]/td[1]/div[2]/div/a[1]')
                    page_button.send_keys(Keys.CONTROL + "\n")
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.switch_to.frame("cafe_main")
                    time.sleep(0.5)  # 페이지 로드 대기

                    # 웹 스크래핑
                    data = scraping()
                    if data:
                        scraped_data.append(data)

                    # 특정 게시물 데이터 수집에 문제가 생기더라도 다음 게시물로 넘어감.
                except:
                    print(f"{i}번째 page의 {j}번째 글 데이터 수집 과정에서 error 발생.")
                    pass

                # 새 창 닫기 -> 원래 창으로 이동
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                driver.switch_to.frame("cafe_main")

            i += 1
            try:
                page_button = driver.find_element(By.XPATH, f'//*[@id="main-area"]/div[6]/a[{i}]')
                page_button.click()
                time.sleep(2)  # 페이지 로드 대기

            except Exception as e:
                print(f"{i}번째 page 클릭 과정에서 error 발생")
                raise

            pbar.update(1)

            if pbar.n % 10 == 0:
                i = 2
            if i == 12:
                i = 2

            save_data(scraped_data, output_dir, data_file_name)


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

    # 셀레니움 브라우저 오픈
    driver = open_browser()

    # 최초 로그인
    naver_login(**login_kwargs)

    # 스크래핑 실행
    web_scraping(**scraping_kwargs)