## pip install -Iv https://pypi.python.org/packages/source/i/ipython/ipython-2.3.1.zip#md5=0affd51ad4a620fe304018094def85cc

import lxml, html, re, urllib

def get_match_events(url):
    doc=lxml.html.fromstring(urllib.urlopen(url).read())
    fixtures=doc.xpath("//div[@id='fixtures']")[0]
    rows=fixtures.xpath("div/table/tbody/tr")
    events, date = [], None
    for row in rows:
        if ("class" in row.attrib and "date" in row.attrib["class"]):
            date=row.xpath("td[@class='day']/p")[0].text
        else:
            time=row.xpath("td[@class='time']/p")[0].text
            spans=row.xpath("td/p/span[@class='add-to-bet-basket']")
            hometeam, awayteam = (spans[0].attrib["data-name"], spans[2].attrib["data-name"])
            link=row.xpath("td[@class='betting']/a")[0].attrib["href"]
            event={"kickoff": "%s %s" % (date, time),"name": "%s vs %s" % (hometeam, awayteam),"link": link}
            events.append(event)
            return events

def parse_fractional_quote(text):
    tokens=[int(tok) for tok in text.split("/")]
    if len(tokens)==1:
        tokens.append(1)
    return 100/(1+tokens[0]/float(tokens[1]))

def get_prices(url):
    doc=lxml.html.fromstring(urllib.urlopen(url).read())
    table=doc.xpath("//table[@class='eventTable ']")[0]
    rows=table.xpath("tbody/tr")
    """
    http://stackoverflow.com/questions/4624062/get-all-text-inside-a-tag-in-lxml
    """
    def stringify_children(node):
        from lxml.etree import tostring
        from itertools import chain
        parts = ([node.text] +
        list(chain(*([c.text, tostring(c), c.tail] for c in node.getchildren()))) +
        [node.tail])
        return ''.join(filter(None, parts))

    def clean_text(text):
        return " ".join([tok for tok in re.split("\\s", text) if tok!=''])

    def filter_tail_text(text):
        tokens=[tok for tok in re.split("\\s", text) if tok!='']
        return tokens[-1]

    items={}

    for row in rows:
        oddscheckerid=row.attrib["data-participant-id"]
        name=None
        for td in row.xpath("td"):
            if not "id" in td.attrib:
                continue
            suffix=td.attrib["id"].split("_")[-1]
            if suffix=="name":
                name=clean_text(td.text)
                continue
            if not re.search("^\\D{2}$", suffix):
                continue
            if suffix=="SI":
                continue
            if td.text==None:
                continue
            items.setdefault(name, {"name": name, "bookmaker": None, "price": 1e10})
            price=parse_fractional_quote(filter_tail_text(stringify_children(td)))
            if price < items[name]["price"]:
                items[name]["price"]=price
                items[name]["bookmaker"]=suffix
                return sorted(items.values(), key=lambda x: -x["price"])

import math
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def poisson(m, n):
    p=math.exp(-m)
    r=[p]
    for i in range(1, n):
        p*=m/float(i)
        r.append(p)
    return r

SamplePoissonTraces=[poisson(i, 10) for i in range(7)]

def generate_linechart(data):
    for row in data:
        plt.plot(range(len(row)), row, '-o')


generate_linechart(SamplePoissonTraces[1:])

def simulate_correct_score(mx, my, n):
    import numpy as np
    return np.outer(poisson(mx, n),
                    poisson(my, n))

SampleCorrectScoreGrid=simulate_correct_score(mx=2.5, my=1.5, n=10)

# http://stackoverflow.com/questions/14391959/heatmap-in-matplotlib-with-pcolor

def generate_heatmap(data, size, colourmap, alpha=1.0):
    df=pd.DataFrame(data)
    fig, ax = plt.subplots()
    heatmap=ax.pcolor(df, cmap=colourmap, alpha=alpha)
    fig=plt.gcf()
    fig.set_size_inches(*size)
    ax.set_frame_on(False)
    ax.set_yticks(np.arange(df.shape[0])+0.5, minor=False)
    ax.set_xticks(np.arange(df.shape[1])+0.5, minor=False)
    ax.invert_yaxis()
    ax.xaxis.tick_top()
    ax.set_xticklabels(df.columns, minor=False) 
    ax.set_yticklabels(df.index, minor=False)
    # plt.xticks(rotation=90)
    ax.grid(False)
    ax=plt.gca()
    for t in ax.xaxis.get_major_ticks(): 
        t.tick1On=False 
        t.tick2On=False 
    for t in ax.yaxis.get_major_ticks(): 
        t.tick1On=False 
        t.tick2On=False


generate_heatmap(SampleCorrectScoreGrid, size=(4, 4), colourmap=plt.cm.Blues)
generate_heatmap(simulate_correct_score(mx=4.5, my=4.5, n=10), size=(4, 4), colourmap=plt.cm.Blues)


class Grid(list):

    def __init__(self, data):
        list.__init__(self, data)

    def sum(self, filterfn):
        return sum([self[i][j]                    
                    for i in range(len(self))
                    for j in range(len(self))
                    if filterfn(i, j)])

    @property
    def home_win(self):
        return self.sum(lambda i, j: i > j)

    @property
    def draw(self):
        return self.sum(lambda i, j: i==j)

    @property
    def away_win(self):
        return self.sum(lambda i, j: i < j)

    @property
    def match_odds(self):
        return [self.home_win,
                self.draw,
                self.away_win]


print Grid(SampleCorrectScoreGrid).match_odds

print sum(Grid(SampleCorrectScoreGrid).match_odds)

def solve_match_odds(prob, n):
    import numpy as np
    def errfn(m, target, n):
        grid=Grid(simulate_correct_score(mx=m[0], my=m[1], n=n))
        return np.sum(np.subtract(grid.match_odds, target)**2)
    from scipy import optimize
    return optimize.fmin(errfn, (1, 1), args=(prob, n))

SolvedMeans=solve_match_odds([0.5, 0.3, 0.2], 10)

print SolvedMeans

grid=Grid(simulate_correct_score(SolvedMeans[0], SolvedMeans[1], 10))

print grid.match_odds

[0.499990991460601, 0.30000645836039203, 0.20000180196519696]


def total_goals(self, overunder, strike):
        if overunder=="over":
            filterfn=lambda i, j: i+j > strike
        else:
            filterfn=lambda i, j: i+j < strike
        return self.sum(filterfn)

Grid.total_goals=total_goals

for overunder in ["over", "under"]:
    for strike in [0.5, 1.5, 2.5]:
        price=grid.total_goals(overunder, strike)
        print "%s %.1f goals: %.3f" % (overunder, strike, price)


def asian_handicap(self, homeaway, strike):
    if homeaway=="home":
        filterfn=lambda i, j: i-j > strike
    else:
        filterfn=lambda i, j: j-i > strike
    return self.sum(filterfn)

Grid.asian_handicap=asian_handicap

for homeaway in ["home", "away"]:
    for strike in [-1.5, -0.5, 0.5, 1.5, 2.5]:
        price=grid.asian_handicap(homeaway, strike)
        print "%s %.1f: %.3f" % (homeaway, strike, price)

HomeWin, AwayWin, Draw = "home_win", "away_win", "draw"

"""
http://stackoverflow.com/questions/4265546/python-round-to-nearest-05
"""

def round_to(n, precision):
    correction = 0.5 if n >= 0 else -0.5
    return int(n/precision+correction)*precision

def nearest_half(n):
    return round_to(n, precision=0.5)

class CSGrid(list):

    def __init__(self, data):
        list.__init__(self, data)

    def sum(self, filterfn):
        return sum([self[i][j]                    
                    for i in range(len(self))
                    for j in range(len(self))
                    if filterfn(i, j)])

    def match_odds(self, selection):
        filterfns={HomeWin: lambda i, j: i > j,
                   AwayWin: lambda i, j: i < j,
                   Draw: lambda i, j: i==j}
        return self.sum(filterfns[selection])

    def correct_score(self, score):
        i, j = score
        return self[i][j]

    # asian handicaps

    def nearest_AH_strikes(self, strike):
        stk=nearest_half(strike)
        if stk < strike:
            return (stk, stk+0.5)
        elif stk > strike:
            return (stk-0.5, stk)
        else:
            return (stk, stk)

    def home_asian_handicap(self, strike):
        def asian_handicap(strike):
            nfilterfn=lambda i, j: i+strike > j
            dfilterfn=lambda i, j: i+strike != j
            return self.sum(nfilterfn)/float(self.sum(dfilterfn))
        upstrike, downstrike = self.nearest_AH_strikes(strike)
        # print (strike, (upstrike, downstrike))
        return (asian_handicap(upstrike)+
                asian_handicap(downstrike))/float(2)

    def away_asian_handicap(self, strike):
        def asian_handicap(strike):
            nfilterfn=lambda i, j: j+strike > i
            dfilterfn=lambda i, j: j+strike != i
            return self.sum(nfilterfn)/float(self.sum(dfilterfn))
        upstrike, downstrike = self.nearest_AH_strikes(strike)
        # print (strike, (upstrike, downstrike))
        return (asian_handicap(upstrike)+
                asian_handicap(downstrike))/float(2)

    # over / under goals

    def over_goals(self, strike):        
        filterfn=lambda i, j: i+j > strike
        return self.sum(filterfn)

    def under_goals(self, strike):
        filterfn=lambda i, j: i+j < strike
        return self.sum(filterfn)


