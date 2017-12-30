# SCSU
Download your Southern Connecticut State University academic calendar.

## Dependencies
Python3, BeautifulSoup, requests, icalendar, getpass

# Reason
I got tired of having to manually create my school calendar in Google Calendar every semester. Now this is a thing.

# The Basics
#
```
from SCSU import SCSU
student = SCSU()
```
> Import SCSU and make an instance (Python 101)
#
#
```
student.user()
```
> Provide SCSU your BannerWeb credentials. (You can also use: student.user("username"), or student.user("username", "password"), or etc.)
#  
# 
```
s.login()
```
> Send your credentials to BannerWeb to authenticate
#  
#  
```
s.listSemesters()
```
> This will only return the most recent 5 semesters from your semester list. I don't see why you would need calendars for 2005 semesters while it being 2017.
#  
# 
If you provided the correct credentials:
```
[ Attempting to collect the first five recent semesters ]

[ Found 5 semesters ]

[ Available semesters (semester code: semester label) ]
201840: Spring 2018
201820: Winter Session 2018
201810: Fall 2017
201750: Summer 2017
201740: Spring 2017
```
#
#
```
student.downloadSemester("201740")
```
> Download the semester by using the semester code
#
#
if you entered a valid semester code:
```
[ Downloading Spring 2017 Academic Calendar ]

[ Making 'Spring 2017.ics' ... Done  ]
```
#
#
```
student.logout()
```
> Logout of BannerWeb
#
# Testing Script
```
from SCSU import SCSU
student = SCSU()
student.user()
student.login()
student.listSemesters()
```
#
# Further Reading
> Refer to the "More" file for more explanation on functions
