import time
import json
import pickle
from collections import deque

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from tqdm import tqdm


def open_browser():
    op = webdriver.ChromeOptions()
    chrome_service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service = chrome_service, options=op)
    return driver


def naver_login(naver_id, naver_pw):
    driver.get("https://nid.naver.com/nidlogin.login")

    try:
        id_box = driver.find_element(By.ID, 'id')
        pw_box = driver.find_element(By.ID, 'pw')
        id_box.send_keys(naver_id)  # 네이버 ID
        pw_box.send_keys(naver_pw)  # 네이버 Password
        pw_box.send_keys(Keys.RETURN)  # 로그인 버튼 대신 Enter 키

        # 최대 대기 시간 설정 : 페이지가 다 로드되지 않았을 때 element를 찾다가
        # 오류가 나는 것을 방지하기 위한 설정. 최대 50초까지 기다리고,
        # 그 이전에 페이지가 로드되면 자동으로 다음 명령을 실행한다.
        driver.implicitly_wait(50)

    except:
        print("no such element")          #예외처리


def scraping():
    return


def web_scraping(cafe_url, max_pages, menu_name):
    # 카페 접속
    driver.get(cafe_url)
    time.sleep(3)

    # 식물관련질문 게시판 클릭
    menu = driver.find_element(By.XPATH, f'//a[contains(text(), "{menu_name}")]')
    menu.click()
    time.sleep(2)

    # cafe_main으로 ifram 이동
    driver.switch_to.frame("cafe_main")

    # 페이지네이션
    i = 1
    with tqdm(total=max_pages) as pbar:
        while pbar.n < max_pages:

            # 스크래핑
            scraping()

            i += 1
            try:
                page_button = driver.find_element(By.XPATH, f'//*[@id="main-area"]/div[6]/a[{i}]')
                page_button.click()
                time.sleep(2)  # 페이지 로드 대기
            except:
                raise

            pbar.update(1)

            if pbar.n % 10 == 0:
                i = 2
            if i == 12:
                i = 2


if __name__ == '__main__':
    login_kwargs = {
    'naver_id' : "YOUR ID",
    'naver_pw' : "YOUR_PASSWORD"
    }

    scraping_kwargs = {
    'cafe_url' : "https://cafe.naver.com/plantremarket",
    'menu_name' : "식물관련질문",

    'max_pages' : 30
    }

    # 셀레니움 브라우저 오픈
    driver = open_browser()

    # 최초 로그인
    naver_login(**login_kwargs)

    # 스크래핑 실행
    web_scraping(**scraping_kwargs)