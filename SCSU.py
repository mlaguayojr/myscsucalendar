"""
    SCSU
        Connect to bannerweb and download any of your semesters to an iCal file.

    Python 3
    Version: 2017/12/29
"""

# Dependencies
from getpass import getpass
from requests import Session
from bs4 import BeautifulSoup
from icalendar import Calendar, Event

#Native
from urllib.request import urlopen
from datetime import datetime, timedelta

class SCSU:
    
    # Private variables
    __credentials = {"sid": None, "PIN": None}
    __session = None
    __semesters = None

    # Set BannerWeb credentials
    def user(self, u = None, p = None):
        if u == None and p == None:
            self.__text("Please enter your username and password")
            self.__credentials['sid'] = input("Username: ")
            self.__credentials['PIN'] = getpass("Password: ")
        
        elif u != None and p == None:
            self.__text("Please enter your password")
            self.__credentials['PIN'] = getpass("Password: ")

        elif u == None and p != None:
            self.__text("Please enter your username")
            self.__credentials['sid'] = input("Username: ")
            
        else:
            # i'm assuming this: u != None and p != None:
            self.__credentials['sid'] = u
            self.__credentials['PIN'] = p
            pass

        self.__text("Credentials are set")

    # Show stored credentials
    def me(self):
        print("\n[ Current Credentials ]\nUsername: %s\nPassword: %s\n" % (self.__credentials['sid'], self.__credentials['PIN']) )
    
    # Attempt to login to BannerWeb
    def login(self):
        if not self.__validCredentials():
            self.__text("BannerWeb could not be reached")
            return None
        
        # Send credentials to BannerWeb Login
        if self.__sendCredentials():
            self.__getSemesters()

    # Attempt to logout of BannerWeb
    def logout(self):
        request = self.__session.get("https://ssb-prod.ec.southernct.edu/PROD/twbkwbis.P_Logout")
        
        if request.status_code != 200:
            self.__text("Failed to logout of BannerWeb")
            return None

        self.__text('Logged out of BannerWeb.')
        self.__credentials = {"sid": None, "PIN": None}
        self.__session = None
        self.__semesters = None

    # Send credentials to BannerWeb
    def __sendCredentials(self):
        request = Session().get("https://ssb-prod.ec.southernct.edu/PROD/twbkwbis.P_WWWLogin")

        if request.status_code != 200:
            self.__text("Unable to visit login page; HTTP"+str(request.status_code))
            return False
            
        request.headers['Access-Control-Allow-Origin'] = '*'
        s = Session()
        request = s.post("https://ssb-prod.ec.southernct.edu/PROD/twbkwbis.P_ValLogin", data=self.__credentials, headers=request.headers, cookies=request.cookies)
        
        if request.status_code != 200:
            self.__text("Unable to send credentials to BannerWeb; HTTP"+str(request.status_code))
            return False
        
        # Error Message
        if "<b>Why am I not signed in? </b>" in request.text:
            self.__text("Failed to login. Check your credentials")
            return False

        # Successful message
        if "url=/PROD/twbkwbis.P_GenMenu?name=bmenu.P_MainMnu&amp;msg=WELCOME+<b>Welcome+" in request.text:
            self.__text("Successfully logged in")
            self.__session = s
            return True

    # Collect available semesters
    def __getSemesters(self):
        self.__text("Attempting to collect the first five recent semesters")

        if self.__session == None:
            self.__text("Unable to list available semesters. You have not logged in to BannerWeb")
            return None

        request = self.__session.get("https://ssb-prod.ec.southernct.edu/PROD/bwskfshd.P_CrseSchdDetl")
        
        if request.status_code != 200:
            self.__text("Unable to collect available semesters; HTTP"+str(request.status_code))
            return None
        
        semesters = BeautifulSoup(request.text, "html.parser").find("select", {"name": "term_in"}).findChildren()

        self.__semesters = {}
        for i in semesters[:5]:
            self.__semesters[ i['value'] ] = i.text.strip(" (View only)")
        
        self.__text("Found %s semesters" % (len(self.__semesters)))

    # Display available semesters
    def listSemesters(self):
        if self.__semesters == None:
            self.__text("You do not have any semesters to show")
            return None

        self.__text("Available semesters (semester code: semester label)")
        for k, v in self.__semesters.items():
            print("%s: %s" % (k, v) )

        print("")

    # Return HTTP Code
    def __response(self, url):
        return urlopen(url).getcode()

    # Validate Credentials
    def __validCredentials(self):
        if list(self.__credentials.values()) in [ [None, None], ["", ""] ]:
            self.__text("Your Credentials are not valid. Please enter your credentials to login")
            return False
        return True

    # Because I'm lazy
    def __text(self, s, end=""):
        print("\n[ %s ]\n" % (s), end=end)

    # Download Semester
    def downloadSemester(self, semester_id):
        if semester_id not in self.__semesters.keys():
            self.__text("Unable to find %s as a semester id" % (semester_id))
            return None

        semester_title = self.__semesters[semester_id]

        self.__text("Downloading %s Academic Calendar" % (semester_title) )

        request = self.__session.post("https://ssb-prod.ec.southernct.edu/PROD/bwskfshd.P_CrseSchdDetl", data={'term_in': semester_id} )

        if request.status_code != 200:
            self.__text("Unable to fetch %s Academic Calendar" % (semester_title) )
            return None
        
        calendar = self.__makeCalendar(request.text)

        if calendar == None:
            self.__text("Unable to find classes for %s Academic Calendar" % (semester_title))
            return None

        self.__text("Making '%s.ics' ... %s " % (semester_title, self.__exportCalendar(calendar, semester_title) ) )

    # Read classes and convert them to a list
    def __makeCalendar(self, html):
        soup = BeautifulSoup(html, "html.parser").find_all("table", { 'class': 'datadisplaytable'})

        if soup == None:
            return None

        calendar = []

        for i in range(0, len(soup), 2):
            
            class_content = soup[i: i+2]

            class_detail = {}

            class_detail['TITLE'] = class_content[0].find("caption", {"class": "captiontext"}).text.replace("*",'')
            
            info = class_content[0].find_all("td", {"class": "dddefault"})
            class_detail['CRN'] = info[1].text
            class_detail['PROF'] = info[3].text.replace("\n",'')
            class_detail['EMAIL'] = str(info[3].a['href']).replace("mailto:", '')
            class_detail['CREDITS'] = "%.1f" % float( str(info[5].text).strip(' ') )
            class_detail['CAMPUS'] = info[7].text

            info = class_content[1].find_all("td", {"class": "dddefault"})

            if len(info) == 14:
                
                more = []

                for i in range(0, len(info), 7):
                    more.append( info[i:i+7] )

                for i in more:
                    calendar.append(
                        {
                            'TIME': i[1].text.split(" - "),
                            'DAYS': list(i[2].text),
                            'BUILDING': i[3].text,
                            'SEMESTER': i[4].text.split(" - "),
                            'TITLE': class_detail['TITLE']+" "+i[5].text,
                            'CRN': class_detail['CRN'],
                            'PROF': class_detail['PROF'],
                            'EMAIL': class_detail['EMAIL'],
                            'CREDITS': class_detail['CREDITS'],
                            'CAMPUS': class_detail['CAMPUS']
                        }
                    )
                    
            else:
                class_detail['TIME'] = info[1].text.split(" - ")

                if class_detail['TIME'][0] != 'TBA':
                    class_detail['DAYS'] = list(info[2].text)
                    class_detail['BUILDING'] = info[3].text
                    class_detail['SEMESTER'] = info[4].text.split(" - ")
                    class_detail['TITLE'] = class_detail['TITLE']+" "+info[5].text
                    calendar.append(class_detail)
            
        return calendar

    # Convert classes to filename
    def __exportCalendar(self, calendar, filename):
        cal = Calendar()
        cal.add('prodid', '-//Mario Luis Aguayo Jr - SCSU//mxm.dk//')
        cal.add('version','1')
        
        for i in calendar:
            
            event = Event()
            event.add('summary', i['TITLE'])

            semester_start = datetime.strptime(i['SEMESTER'][0]+" "+i['TIME'][0],'%b %d, %Y %I:%M %p').strftime("%A")
            
            correct_date = {
                "Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5, "Saturday": 6, "Sunday": 0,
                "MO": 1, "TU": 2, "WE": 3, "TH": 4, "FR": 5, "SA": 6, "SU": 0
            }

            if correct_date[ self.__fixDate( [ i['DAYS'][0] ] )[0].decode("UTF-8") ] < correct_date[semester_start]:
                event.add('dtstart', datetime.strptime(i['SEMESTER'][0]+" "+i['TIME'][0],'%b %d, %Y %I:%M %p') + timedelta(days=-1) )
                event.add('dtend',   datetime.strptime(i['SEMESTER'][0]+" "+i['TIME'][1],'%b %d, %Y %I:%M %p') + timedelta(days=-1) )
            else:
                diff = correct_date[ self.__fixDate( [ i['DAYS'][0] ] )[0].decode("UTF-8") ] - correct_date[semester_start]
                event.add('dtstart', datetime.strptime(i['SEMESTER'][0]+" "+i['TIME'][0],'%b %d, %Y %I:%M %p') + timedelta(days=diff) )
                event.add('dtend',   datetime.strptime(i['SEMESTER'][0]+" "+i['TIME'][1],'%b %d, %Y %I:%M %p') + timedelta(days=diff) )
            
            event.add(
                'rrule',
                {
                    'freq': 'weekly',
                    'interval': '1',
                    'until': datetime.strptime( i['SEMESTER'][1], '%b %d, %Y'),
                    'WKST': b"SU",
                    'byday': self.__fixDate( i['DAYS'] )
                }
            )
            event.add('location', i['BUILDING'])
            event.add(
                'description',
                "CRN: %s\nProfessor: %s\nE-mail: %s\nCredits: %s" % (i['CRN'], i['PROF'], i['EMAIL'], i['CREDITS'])
            )
            event.add('class', 'private')
            event.add('priority', 5)
            cal.add_component( event )

        with open("%s.ics" % (filename), 'wb') as f:
            f.write(cal.to_ical())
            return "Done"

        return "Failed"

    # Fix date
    def __fixDate(self, l):
        template = { "M": "MO", "T": "TU", "W": "WE", "R": "TH", "F": "FR", "S": "SA", "U": "SU" }

        for i in range(0, len(l)):
            l[i] = template[ l[i] ]
            l[i] = str(l[i]).encode("UTF-8")
        return l