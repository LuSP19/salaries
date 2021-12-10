import json
import os

import requests
from dotenv import load_dotenv
from terminaltables import SingleTable


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


def get_lang_salaries_stat_hh(lang):
    hh_moscow_id = 1
    hh_vacancy_posting_period = 30

    url = 'https://api.hh.ru/vacancies/'
    headers = {'User-Agent': 'Chrome/51.0.2704.103'}
    params = {
        'area': hh_moscow_id,
        'period': hh_vacancy_posting_period
    }

    processed_vacancies = []
    processed_vacancies_count = 0

    params['text'] = f'Программист {lang}'
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    pages = response.json()['pages']

    for page in range(pages):
        params['page'] = page
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        vacancies_on_page = response.json()['items']
        for vacancy in vacancies_on_page:
            predicted_salary = predict_rub_salary_hh(vacancy)
            if predicted_salary:
                processed_vacancies.append(predicted_salary)
                processed_vacancies_count += 1

    if processed_vacancies_count:
        salaries_sum = sum(processed_vacancies)
        average_salary = int(salaries_sum / processed_vacancies_count)
    else:
        average_salary = 0

    lang_salaries_stat = {
        'found_vacancies': response.json()['found'],
        'processed_vacancies': processed_vacancies_count,
        'average_salary': average_salary
    }

    return lang_salaries_stat


def get_salaries_hh(langs):
    salaries = dict()

    for lang in langs:
        salaries[lang] = get_lang_salaries_stat_hh(lang)

    return salaries


def get_lang_salaries_stat_sj(lang, secret_key):
    sj_moscow_id = 4
    sj_programming_catalog_id = 48

    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': secret_key}
    params = {
        'town': sj_moscow_id,
        'catalogues': sj_programming_catalog_id
    }
    
    processed_vacancies = []
    processed_vacancies_count = 0
    
    params['keyword'] = f'Программист {lang}'
    params['page'] = 0
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    while response.json()['more']:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        vacancies_on_page = response.json()['objects']
        for vacancy in vacancies_on_page:
            predicted_salary = predict_rub_salary_sj(vacancy)
            if predicted_salary:
                processed_vacancies.append(predicted_salary)
                processed_vacancies_count += 1
        params['page'] += 1

    if processed_vacancies_count:
        salaries_sum = sum(processed_vacancies)
        average_salary = int(salaries_sum / processed_vacancies_count)
    else:
        average_salary = 0

    lang_salaries_stat = {
        'found_vacancies': response.json()['total'],
        'processed_vacancies': processed_vacancies_count,
        'average_salary': average_salary
    }

    return lang_salaries_stat


def get_salaries_sj(langs, secret_key):
    salaries = dict()

    for lang in langs:
        salaries[lang] = get_lang_salaries_stat_sj(lang, secret_key)

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
        table_row.append(stat['found_vacancies'])
        table_row.append(stat['processed_vacancies'])
        table_row.append(stat['average_salary'])
        table_data.append(table_row)

    table_instance = SingleTable(table_data, title)
    table_instance.justify_columns[3] = 'right'
    print(table_instance.table)


def main():
    load_dotenv()
    secret_key = os.getenv('SJ_SECRET_KEY')

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

    salaries_hh = get_salaries_hh(langs)
    salaries_sj = get_salaries_sj(langs, secret_key)

    print_salaries_table('HeadHunter Moscow', salaries_hh)
    print()
    print_salaries_table('SuperJob Moscow', salaries_sj)


if __name__ == '__main__':
    main()
