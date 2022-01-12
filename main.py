import json
import os
from itertools import count

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


def get_hh_lang_salaries_stat(lang):
    moscow_id = 1
    vacancy_posting_period = 30

    url = 'https://api.hh.ru/vacancies/'
    headers = {'User-Agent': 'Chrome/51.0.2704.103'}
    params = {
        'area': moscow_id,
        'period': vacancy_posting_period,
        'text': f'Программист {lang}'
    }

    processed_vacancies = []
    processed_vacancies_count = 0
    found_vacancies = 0

    for page in count():
        params['page'] = page
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        vacancies_on_page = response.json()['items']
        found_vacancies += len(vacancies_on_page)

        for vacancy in vacancies_on_page:
            predicted_salary = predict_rub_salary_hh(vacancy)
            if predicted_salary:
                processed_vacancies.append(predicted_salary)
                processed_vacancies_count += 1

        if page == response.json()['pages'] - 1:
            break

    if processed_vacancies_count:
        salaries_sum = sum(processed_vacancies)
        average_salary = int(salaries_sum / processed_vacancies_count)
    else:
        average_salary = 0

    lang_salaries_stat = {
        'found_vacancies': found_vacancies,
        'processed_vacancies': processed_vacancies_count,
        'average_salary': average_salary
    }

    return lang_salaries_stat


def get_hh_salaries_stat(langs):
    salaries = dict()

    for lang in langs:
        salaries[lang] = get_hh_lang_salaries_stat(lang)

    return salaries


def get_sj_lang_salaries_stat(lang, secret_key):
    moscow_id = 4
    programming_catalog_id = 48

    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': secret_key}
    params = {
        'town': moscow_id,
        'catalogues': programming_catalog_id,
        'keyword': f'Программист {lang}'
    }
    
    processed_vacancies = []
    processed_vacancies_count = 0
    found_vacancies = 0

    for page in count():
        params['page'] = page
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        vacancies_on_page = response.json()['objects']
        found_vacancies += len(vacancies_on_page)
        for vacancy in vacancies_on_page:
            predicted_salary = predict_rub_salary_sj(vacancy)
            if predicted_salary:
                processed_vacancies.append(predicted_salary)
                processed_vacancies_count += 1

        if not response.json()['more']:
            break

    if processed_vacancies_count:
        salaries_sum = sum(processed_vacancies)
        average_salary = int(salaries_sum / processed_vacancies_count)
    else:
        average_salary = 0

    lang_salaries_stat = {
        'found_vacancies': found_vacancies,
        'processed_vacancies': processed_vacancies_count,
        'average_salary': average_salary
    }

    return lang_salaries_stat


def get_sj_salaries_stat(langs, secret_key):
    salaries = dict()

    for lang in langs:
        salaries[lang] = get_sj_lang_salaries_stat(lang, secret_key)

    return salaries


def make_salaries_stat_table(title, salaries_stat):
    table = [[
        'Язык программирования',
        'Вакансий найдено',
        'Вакансий обработано',
        'Средняя зарплата'
    ]]

    for lang, stat in salaries_stat.items():
        row = [
            lang,
            stat['found_vacancies'],
            stat['processed_vacancies'],
            stat['average_salary']
        ]

        table.append(row)

    table_instance = SingleTable(table, title)
    table_instance.justify_columns[3] = 'right'

    return table_instance.table


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

    hh_salaries_stat = get_hh_salaries_stat(langs)
    hh_salaries_stat_tbl = make_salaries_stat_table('HeadHunter Moscow', hh_salaries_stat)

    sj_salaries_stat = get_sj_salaries_stat(langs, secret_key)
    sj_salaries_stat_tbl = make_salaries_stat_table('SuperJob Moscow', sj_salaries_stat)

    print(hh_salaries_stat_tbl)
    print()
    print(sj_salaries_stat_tbl)


if __name__ == '__main__':
    main()
