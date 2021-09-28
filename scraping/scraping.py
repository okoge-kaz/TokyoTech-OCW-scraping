import time

from bs4 import BeautifulSoup
from selenium import webdriver
import json

RESET_LIMIT = 600
reset_count = 0

'''lamda functions are here'''


def replace_inappropriate_string(s):
    return str(s).replace('\t', ' ').replace('\n', ' ').replace('\xa0', ' ').replace('\u3000', ' ').strip(' ')


def first_elem(d):
    return d[list(d.keys())[0]] if len(d) > 0 else None


try:
    assert driver
except Exception:
    driver = None
    mem_reset_count = 0


def init_driver():
    '''initialize webdriver when time seems to be over the LIMIT'''

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    global driver
    driver = webdriver.Chrome(options=options)


def get_html(*args, **kwargs):
    global reset_count
    # if over the limit ( => reset webdriver )
    if reset_count >= RESET_LIMIT:
        reset_count = 0
        driver.quit()
        init_driver()
    driver.get(*args, **kwargs)  # ?
    time.sleep(6)
    html = driver.page_source
    reset_count += 1
    return html


def html_check(*args, **kwargs):
    time_out_length = 360
    html = get_html(*args, **kwargs)
    start_time = time.time()
    diff_time = time.time() - start_time
    full_loaded = False
    while not full_loaded:
        html = driver.page_source
        full_loaded = html.find('left-menu') and html.find('right-contents')
        if time_out_length <= diff_time:
            print("timeout")
            return "timeout"
        # if html.find("HTTP 404") or html.find("404 NOT FOUND") or html.find("404 Not Found"):
        #     return "404"
    return html


def get_department_list(year=2020, lang="JA"):
    '''fetching data from tokyo tech ocw'''

    url = 'http://www.ocw.titech.ac.jp/index.php?module=Archive&action=ArchiveIndex&GakubuCD=1&GakkaCD=311100&KeiCD=11&tab=2&focus=200&lang={}&Nendo={}&SubAction=T0200'.format(
        lang, year)
    html = html_check(url)
    # print(html)
    soup = BeautifulSoup(html, 'lxml')

    '''for your information left-body-? means'''
    # left-body-1 : 学士課程 学院
    # left-body-2 : 大学院課程 学院
    # left-body-3 : 学士課程 学部
    # left-body-4 : 大学院課程 学部

    left_body_section = soup.find('div', id='left-body-1')
    # if left_body_section is None : print('bad')

    left_body_section_li_tags = [
        elem for elem in left_body_section.ul if elem.name == "li"]

    major_map_data = {}  # 系の名前とurlがセットになった辞書型
    # 元のコードはurlではなくurlをつくる要素となる文字列を辞書型にしている

    def extract_department_name_from_li_tag(li_tag_element, department_name_map):
        '''get_department_list function calls this function. and collect information from argument (li_tag_element) ,then update information map (second argument)'''

        if li_tag_element.a is None:
            return False
        # department_name: 学院名
        department_name = str(
            replace_inappropriate_string(li_tag_element.a.string))

        major_name_and_url_map = {}
        for li_element in li_tag_element.ul:
            if li_element.name == 'li':
                extract_major_name_from_li_tag(
                    li_element, major_name_and_url_map)

        # map: (key: department_name::string , value: major_name_and_url_map::dictionary[key::string, url::string ])
        department_name_map[department_name] = major_name_and_url_map
        return True

    def extract_major_name_from_li_tag(li_tag_element, major_name_map):
        '''extract_department_name_from_li_tag function calls this function, and this function's job is collection infromation about combination between key: major name and value: individual url'''
        # 上記の関数から呼び出され、系の名前とurlをついにした辞書(map)型の返値を返す。これを上記の関数で学院名とこの関数の返値で辞書型にする。
        major_name = li_tag_element.a.span.string

        def url_munipulate(url_segment):
            adder = 'http://www.ocw.titech.ac.jp/'
            return adder + url_segment

        full_url = url_munipulate(
            li_tag_element.a['href']) if li_tag_element.a['href'] != '#' else url

        major_map_data[major_name] = full_url
        major_name_map[major_name] = full_url

        return

    department_map_data = {}

    for li_element in left_body_section_li_tags:
        extract_department_name_from_li_tag(li_element, department_map_data)

    # deparment_map_data: (学院名 , map(系名: url)) , major_map_data: ( 系名, url )
    return department_map_data, major_map_data


def get_major_all_course_list(major_name, major_url, retry_limit=5):
    '''各系からすべての講義を取得する retlieve all course's basic information from every major'''

    shaping_tables = []  # データ要素を整える

    for _ in range(retry_limit):
        html = html_check(major_url)
        # print(html)
        soup = BeautifulSoup(html, 'lxml')

        tables = [table_element.tbody for table_element in soup.find_all(
            'table', class_='ranking-list') if table_element.tbody is not None]
        # HTMLの要素のうち各系の講義一覧がある要素を取得する find_allにしているのは200番台,300番台と複数あるから

        if len(tables) == 0:
            continue
        for table in tables:
            trs = [elem for elem in table if elem.name == 'tr']
            for tr in trs:
                shaping_tables.append(
                    get_course_detail_informaion_from_tr_tag(major_name, tr))

        if len(shaping_tables) > 0:
            break
    # shaping_tables: dictionary[] type 講義詳細情報が辞書型で管理されたものがリストになっている
    return shaping_tables


def get_course_detail_informaion_from_tr_tag(major_name, tr_tag_element):
    course_information = {}
    # url_adder = 'http://www.ocw.titech.ac.jp/'
    td_tag_elements = tr_tag_element.find_all('td')
    for td_tag_element in td_tag_elements:
        if td_tag_element.name == 'td' and (td_tag_element.get('class') is not None):
            if str(td_tag_element).find('width_code') != -1 and td_tag_element.string is not None:
                course_information['courseId'] = replace_inappropriate_string(
                    str(td_tag_element.string))
                # print(td_tag_element)
                # print(replace_inappropriate_string(str(td_tag_element.string)))
                # print(len(replace_inappropriate_string(str(td_tag_element.string))))
                # print()
                course_information['courseDigit'] = (int)(
                    (replace_inappropriate_string(str(td_tag_element.string)))[5])
                course_information['department'] = major_name
            elif str(td_tag_element).find('course_title') != -1:
                # course_information['url'] = url_adder + str(td_tag_element.a['href'])
                course_information['courseName'] = replace_inappropriate_string(
                    str(td_tag_element.a.string))
                index = (str(td_tag_element.a['href'])).find('&KougiCD=')
                id = str(td_tag_element.a['href'])[index + 9:index + 18]
                course_information['id'] = id
            elif str(td_tag_element).find('lecturer') != -1:
                teachers = []
                for element in td_tag_element:
                    if element.name == 'a':
                        teachers.append(
                            replace_inappropriate_string(str(element.string)))
                course_information['teachers'] = teachers
    # course_information: courseId, courseDigit, url ,courseName, teachers
    print(course_information)
    return course_information


def main():
    if driver is None:
        init_driver()
    [department_list, major_list] = get_department_list()
    for major, url in major_list.items():
        print((major, url))
    data = []
    count: int = 1
    for key, value in major_list.items():
        # print(value)
        tmp_data = get_major_all_course_list(key, value)
        with open('data/' + str(count) + '.json', 'w', encoding="utf-8") as f:
            json.dump(tmp_data, f, indent=4, ensure_ascii=False)
        data.extend(tmp_data)
        # print(data)
        count += 1

    file_path = './course.json'
    with open(file_path, 'w', encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    driver.quit()


if __name__ == '__main__':
    main()
