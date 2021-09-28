import json
import urllib.request


def main():
    for id in range(1, 26):
        PATH: str = 'scraping/data/' + str(id) + '.json'
        with open(PATH, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
            for index in range(len(json_data)):
                url = 'https://titechinfo-data.s3-ap-northeast-1.amazonaws.com/course-review-tmp/course/' + json_data[index]['id'] + '.json'
                try:
                    with urllib.request.urlopen(url):
                        json_data[index]['isExist'] = True
                        print(True)
                except urllib.error.URLError:
                    json_data[index]['isExist'] = False
                    print(False)
            with open('data/' + str(id) + '.json', 'w', encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    main()
