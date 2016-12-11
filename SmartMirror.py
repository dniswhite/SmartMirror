from tkinter import *
import locale
import threading
import time
import urllib
import decimal
import requests

from PIL import Image, ImageTk
from contextlib import contextmanager
from requests import get

import PIL.ImageOps

# headline and popular news
newsApiUrl="https://newsapi.org/v1/articles?source=google-news&sortBy=top&apiKey="
newsApiKey=""

# ip and geo coordinates api 
jsonGeoIPApiUrl="http://jsonip.com"
jsonGeoLatLonApiURL="http://freegeoip.net/json/"

geo_ip=''
geo_lat=0.0
geo_lon=0.0

# weather settings 
weatherApiUrl="https://api.darksky.net/forecast/"
weatherApiKey=""
weatherUrl = "{0}{1}/{2},{3}?exclude=[minutely,hourly,flags]"

high_low = "High {0}{2} - Low {1}{2}"

weather_info_lookup = {
    'clear-day':{'image':"assets/clear-day.png", 'description':" Clear Day"},
    'clear-night': {'image':"assets/clear-night.png", 'description':" Clear Night"},
    'rain': {'image':"assets/rain.png", 'description':" Rain"},
    'snow':{'image':"assets/snow.png", 'description':" Snow"},
    'sleet':{'image':"assets/sleet.png", 'description':"S leet"},
    'wind':{'image':"assets/wind.png", 'description':" Windy"},
    'fog':{'image':"assets/fog.png", 'description':" Fog"},
    'cloudy':{'image':"assets/cloudy.png", 'description':" Cloudy"},
    'partly-cloudy-night':{'image':"assets/partly-cloudy-night.png", 'description':" Partly Cloudy"},
    'partly-cloudy-day': {'image':"assets/partly-cloudy-day.png", 'description':" Partly Cloudy"},
    'hail':{'image':"assets/hail.png", 'description':" Hail"},
    'thunderstorm':{'image':"assets/thunderstorm.png", 'description':" Thunderstorms"},
    'tornado':{'image':"assets/tornado.png", 'description':" Tornado"}
}

# text size vars
xlarge_text_size = 68
large_text_size = 48
medium_text_size = 28
small_text_size = 18

LOCALE_LOCK = threading.Lock()

@contextmanager
def setlocale(name): 
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)


class Clock(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        # initialize time label
        self.time1 = ''
        self.timeLbl = Label(self, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.timeLbl.pack(side=TOP, anchor=E)
        # initialize date label
        self.display_date = ''
        self.dateLbl = Label(self, text=self.display_date, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.dateLbl.pack(side=TOP, anchor=E)
        self.tick()

    def tick(self):
        with setlocale(''):
            #hour in 12h format
            time2 = time.strftime('%I:%M:%S %p') 

            day_of_week = time.strftime('%A')
            date = time.strftime("%B %d, %Y")
            display_date_now = "{0}, {1}".format(day_of_week, date)
            
            # if time or date has changed update screen
            if time2 != self.time1:
                self.time1 = time2
                self.timeLbl.config(text=time2)
            if display_date_now != self.display_date:
                self.display_date = display_date_now
                self.dateLbl.config(text=display_date_now)

            self.timeLbl.after(200, self.tick)

class Weather(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.frame_title = Frame(self, background='black')
        self.frame_title.pack(side=TOP, anchor=W)
        
        image = Image.open("assets/weather.png")
        image = image.resize((48,48), Image.ANTIALIAS)
        image = image.convert('RGB')
        photo = ImageTk.PhotoImage(image)
        self.weatherImage = Label(self.frame_title, bg='black', image=photo)
        self.weatherImage.image = photo
        self.weatherImage.pack(side=LEFT, anchor=N)
        
        self.current = ''
        self.weatherLabel = Label(self.frame_title, text=self.current, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.weatherLabel.pack(side=LEFT, anchor=N)

        self.high_low = ''
        self.highlowLabel = Label(self, text=self.high_low, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.highlowLabel.pack(side=TOP, anchor=W)

        self.current_weather = ''
        self.currentLabel = Label(self, text=self.current_weather, font=('Helvetica', xlarge_text_size), fg="white", bg="black")
        self.currentLabel.pack(side=TOP, anchor=W)

        self.check_weather()

    def get_json_weather(self):
        try:
            url = weatherUrl.format(weatherApiUrl,weatherApiKey,geo_lat,geo_lon)
            return get(url).json()
        except (requests.exceptions.ConnectionError, ValueError):
            return None
        
    def check_weather(self):
        # refresh weather everyy minutes
        weather = self.get_json_weather()
        if None != weather:
            # parse out information and update display
            degrees = '\N{DEGREE SIGN}'
            current = weather['currently']
            day = weather['daily']['data'][0]

            info = weather_info_lookup[current['icon']]
            if None != info:
                if self.current != info['description']:
                    self.weatherLabel.config(text=info['description'])

                    image = Image.open(info['image'])
                    image = image.resize((48,48), Image.ANTIALIAS)
                    image = image.convert('RGB')
                    photo = ImageTk.PhotoImage(image)

                    self.weatherImage.config(image=photo)
                    self.weatherImage.image = photo

            current_temp = round(decimal.Decimal(current['temperature']))
            current_low = round(decimal.Decimal(day['temperatureMin']))
            current_high = round(decimal.Decimal(day['temperatureMax']))

            if self.current_weather != current_temp:
                self.currentLabel.config(text=str(current_temp)+"{0}".format(degrees))

            highlow = high_low.format(current_high, current_low, degrees)
            if self.high_low != highlow:
                self.highlowLabel.config(text=highlow)
        
            self.after(900000, self.check_weather)
        else:
            self.after(60000, self.check_weather)

class News(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.frame_title = Frame(self, background='black')
        self.frame_title.pack(side=TOP, anchor=W)

        image = Image.open("assets/news.png")
        image = image.resize((48,48), Image.ANTIALIAS)
        image = image.convert('RGB')
        photo = ImageTk.PhotoImage(image)

        self.newsImage = Label(self.frame_title, bg='black', image=photo)
        self.newsImage.image = photo
        self.newsImage.pack(side=LEFT, anchor=N)
        
        self.current = ' Breaking News'
        self.newsLabel = Label(self.frame_title, text=self.current, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.newsLabel.pack(side=LEFT, anchor=N)

        self.breakingNews = Frame(self, bg='black')
        self.breakingNews.pack(side=LEFT, anchor=N)
        
        self.check_news()

    def get_json_news(self):
        try:
            return get("{0}{1}".format(newsApiUrl, newsApiKey)).json()
        except (requests.exceptions.ConnectionError, ValueError):
            return None
        
    def check_news(self):
        # delete entries from news
        for headline in self.breakingNews.winfo_children():
            headline.destroy()

        news_info = self.get_json_news()

        if None != news_info:
            # parse headline news information
            headlines = news_info['articles']

            for headline in headlines[:3]:
                article = Headline(self.breakingNews, headline['title'], headline['description'])
                article.pack(side=TOP, anchor=W)
                
            # check for news in fifteen (15) minutes
            self.after(900000, self.check_news)
        else:
            # failed to get news info, try again in a minute
            self.after(60000, self.check_news)

class Headline(Frame):
    def __init__(self, parent, title, description):
        Frame.__init__(self, parent, padx=70, bg='black')
        self.title = title
        self.headlineLabel = Label(self, text=self.title, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.headlineLabel.pack(side=LEFT, anchor=N)
        
class XKCDComic(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent, bg='black')

        self.get_comic()

    def get_json_comic(self):
        try:
            return get("http://xkcd.com/info.0.json").json()
        except (requests.exceptions.ConnectionError, ValueError):
            return None

    def get_image(self, location):
        try:
            imageName = location.split('/')[-1]
            self.comicName = "assets/comic."+imageName.split('.')[-1]
            urllib.request.urlretrieve(location, self.comicName)

            image = Image.open(self.comicName)
            inverted = PIL.ImageOps.invert(image)
            inverted.save(self.comicName)
        except (urllib.ContentTooShortError, IOError):
            return False

        return True        
        
    def get_comic(self):
        # remove comics that may already be displayed
        for comic in self.winfo_children():
            comic.destroy()
        
        comic_info = self.get_json_comic()

        if None != comic_info:
            remoteImage = comic_info['img']

            if self.get_image(remoteImage):
                # display image here
                image = Image.open(self.comicName)
                image = image.convert('RGB')
                
                w, h = image.size
                if w >= 284 and h >= 284:
                    # images too large screw things up
                    image = image.resize((370,317), Image.ANTIALIAS)

                photo = ImageTk.PhotoImage(image)

                self.comicImage = Label(self, bg='black', image=photo)
                self.comicImage.image = photo
                self.comicImage.pack(side=LEFT, anchor=N)

                # try to update hourly
                self.after(3600000, self.get_comic)
            else:
                # failed to get image so try again in a minute
                self.after(60000, self.get_comic)
                
class SmartWindow():
    def __init__(self):
        self.tk = Tk()
        self.tk.configure(background='white')
        self.topFrame = Frame(self.tk, background='black')
        self.topFrame.pack(side=TOP, fill=BOTH, expand=YES)
        self.midFrame = Frame(self.tk, background='black')
        self.midFrame.pack(side=TOP, fill=BOTH, expand=YES)
        self.botFrame = Frame(self.tk, background='black')
        self.botFrame.pack(side=BOTTOM, fill=BOTH, expand=YES)

        # setup config params
        self.setup_ip()
        self.setup_geo_coords()

        # event binding for full screen
        self.tk.bind("<F8>", self.toggle_fullscreen)
        self.state=False
        
        # clock tick/tock widget
        self.clock = Clock(self.topFrame)
        self.clock.pack(side=RIGHT, anchor=N, padx=100, pady=60)

        # weather widget
        self.weather = Weather(self.topFrame)
        self.weather.pack(side=LEFT, anchor=N, padx=100, pady=60)

        # news widget
        self.news = News(self.botFrame)
        self.news.pack(side=LEFT, anchor=N, padx=100, pady=20)

        # comic widget
        self.comic = XKCDComic(self.midFrame)
        self.comic.pack(side=RIGHT, anchor=N, padx=100)

    def toggle_fullscreen(self, event=None):
        self.state = not self.state
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def setup_ip(self):        
        try:
            json_ip = get(jsonGeoIPApiUrl).json()
            global geo_ip
            geo_ip = json_ip['ip']
        except (requests.exceptions.ConnectionError, ValueError):
            return None

    def setup_geo_coords(self):
        try:
            json_geo = get(jsonGeoLatLonApiURL+geo_ip).json()
            global geo_lat
            geo_lat = json_geo['latitude']
            global geo_lon
            geo_lon = json_geo['longitude']
        except (requests.exceptions.ConnectionError, ValueError):
            return None
        

if __name__ == '__main__':
    win=SmartWindow()
    win.tk.mainloop()
