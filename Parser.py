from re import sub
from requests import get
from bs4 import BeautifulSoup

import Database

import config

# Возвращает список групп на указанных курсе и институте
def ParseGroups(CourseNum: int, InstituteNum: int) -> list:
    CourseNum = str(CourseNum)
    InstituteNum = str(InstituteNum)

    request = get(config.url_schedule)
    soup = BeautifulSoup(request.text, "html.parser")
    groups = []

    # Данные о группе и номере курса введены неправильно или
    # группы не были найдены
    try:
        GroupSoup = soup.\
            find(id=CourseNum).\
            find(id="fac-" + CourseNum + "-Институт-№" + InstituteNum).\
            find_all('a', class_="sc-group-item")
    except Exception:
        return []

    for group in GroupSoup:
        group = group.get_text()
        groups.append(group)
    return groups

# Возвращает расписание группы на указанную неделю в виде списка занятий
# Занятие также представляет собой список всегда одинаковой длины, хранящий информацию о его проведении
def ParseScheduleWeek(GroupName: str, week: int) -> list:
    url = config.url_schedule + \
          "/detail.php?group=" + \
          GroupName + '&week=' + str(week)
    request = get(url)

    WeekSoup = BeautifulSoup(request.text, "html.parser")

    result = []
    for DaySoup in WeekSoup.find_all('div', class_="sc-table sc-table-day"):
        d = DaySoup.find('div', class_="sc-table-col sc-day-header sc-gray").text
        for SubjectSoup in DaySoup.\
                           find('div', class_="sc-table sc-table-detail").\
                           find_all('div', class_="sc-table-row"):
            subject = [GroupName, week, d[:5], d[5:]]
            subject.append(SubjectSoup.find('div', class_="sc-table-col sc-item-time").text)
            subject.append(SubjectSoup.find('div', class_="sc-table-col sc-item-type").text)
            TitleSoup = SubjectSoup.find('div', class_="sc-table-col sc-item-title")
            subject.append(TitleSoup.find('span', class_="sc-title").text)
            subject.append(TitleSoup.find('span', class_="sc-lecturer").text)
            try:
                location = SubjectSoup.find_all('div', class_="sc-table-col sc-item-location")[1].text
                subject.append(sub(r"[\n\t\xa0]", "", location))
            except Exception:
                subject.append("")
            result.append(subject)

    return result

# Возвращает расписание сессии
def ParseSession(GroupName: str) -> list:
    url = config.url_session + ".php?group=" + GroupName
    request = get(url)

    SessionSoup = BeautifulSoup(request.text, "html.parser")

    result = []
    for DaySoup in SessionSoup.find_all('div', class_="sc-table sc-table-day"):
        date = DaySoup.find('div', class_="sc-table-col sc-day-header sc-gray").text
        for SubjectSoup in DaySoup.\
                           find('div', class_="sc-table sc-table-detail").\
                           find_all('div', class_="sc-table-row"):
            subject = [GroupName, date]
            subject.append(SubjectSoup.find('div', class_="sc-table-col sc-item-time").text)
            TitleSoup = SubjectSoup.find('div', class_="sc-table-col sc-item-title")
            subject.append(TitleSoup.find('span', class_="sc-title").text)
            subject.append(TitleSoup.find('span', class_="sc-lecturer").text)
            try:
                location = SubjectSoup.find_all('div', class_="sc-table-col sc-item-location")[1].text
                subject.append(sub(r"[\n\t\xa0]", "", location))
            except Exception:
                subject.append("")
            result.append(subject)

    return result