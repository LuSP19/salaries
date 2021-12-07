import json
import os

import requests
from dotenv import load_dotenv
from terminaltables import SingleTable

langs = [
    'JavaScript',
    'Java',
    'Python',
    'Ruby',
    'PHP',
    'C++',
    'C#',
    'C',
    'Go',
    'TypeScript',
    'Rust'
]


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8


def predict_rub_salary_hh(vacancy):
    salary = vacancy['salary']
    if salary and salary['currency'] == 'RUR':
        return predict_salary(salary['from'], salary['to'])


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] == 'rub':
        return predict_salary(vacancy['payment_from'], vacancy['payment_to'])


def get_salaries_hh(langs):
    url = 'https://api.hh.ru/vacancies/'
    headers = {'User-Agent': 'Chrome/51.0.2704.103'}
    params = {'area': 1, 'period': 30}

    salaries = dict()

    for lang in langs:
        lang_stat = dict()
        vacancies_processed = []
        vacancies_processed_count = 0

        params['text'] = f'Программист {lang}'
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        pages = response.json()['pages']

        for page in range(pages):
            params['page'] = page
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            for vacancy in response.json()['items']:
                if predict_rub_salary_hh(vacancy):
                    vacancies_processed.append(predict_rub_salary_hh(vacancy))
                    vacancies_processed_count += 1

        lang_stat['vacancies_found'] = response.json()['found']
        lang_stat['vacancies_processed'] = vacancies_processed_count
        if vacancies_processed_count:
            salaries_sum = sum(vacancies_processed)
            lang_stat['average_salary'] = int(salaries_sum / vacancies_processed_count)
        else:
            lang_stat['average_salary'] = 0

        salaries[lang] = lang_stat

    return salaries


def get_salaries_sj(langs, secret_key):
    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': secret_key}
    params = {'town': 4, 'catalogues': 48}

    salaries = dict()

    for lang in langs:
        lang_stat = dict()
        vacancies_processed = []
        vacancies_processed_count = 0

        params['keyword'] = f'Программист {lang}'
        params['page'] = 0
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        while response.json()['more']:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            for vacancy in response.json()['objects']:
                if predict_rub_salary_sj(vacancy):
                    vacancies_processed.append(predict_rub_salary_sj(vacancy))
                    vacancies_processed_count += 1
            params['page'] += 1

        lang_stat['vacancies_found'] = response.json()['total']
        lang_stat['vacancies_processed'] = vacancies_processed_count
        if vacancies_processed_count:
            salaries_sum = sum(vacancies_processed)
            lang_stat['average_salary'] = int(salaries_sum / vacancies_processed_count)
        else:
            lang_stat['average_salary'] = 0

        salaries[lang] = lang_stat

    return salaries


def print_salaries_table(title, salaries):
    table_data = []
    table_headers = [
            'Язык программирования',
            'Вакансий найдено',
            'Вакансий обработано',
            'Средняя зарплата'
        ]
    table_data.append(table_headers)

    for lang, stat in salaries.items():
        table_row = [lang]
        table_row.append(stat['vacancies_found'])
        table_row.append(stat['vacancies_processed'])
        table_row.append(stat['average_salary'])
        table_data.append(table_row)

    table_instance = SingleTable(table_data, title)
    table_instance.justify_columns[3] = 'right'
    print(table_instance.table)


def main():
    load_dotenv()
    secret_key = os.getenv('SJ_SECRET_KEY')

    salaries_hh = get_salaries_hh(langs)
    salaries_sj = get_salaries_sj(langs, secret_key)

    print_salaries_table('HeadHunter Moscow', salaries_hh)
    print()
    print_salaries_table('SuperJob Moscow', salaries_sj)


if __name__ == '__main__':
    main()
