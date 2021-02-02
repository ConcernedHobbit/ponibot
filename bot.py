from telethon.sync import TelegramClient, events
import os, re
from urllib.request import urlopen
from bs4 import BeautifulSoup, SoupStrainer
from bs4.diagnose import diagnose

API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HEPPA = os.environ.get('HEPPA_URL')

APPROVALS = "+" #u"\U0001F44D" # Unicode thumbs up
VETOES = "❌ "    #u"\U0001F44E" # Unicode thumbs down

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='(?i)/start'))
async def start(event):
    print("[+] Start command received")

@bot.on(events.NewMessage(pattern='(?i)/help'))
async def help(event):
    print("[+] Help message requested")
    res = ''

    res += '**Commands:**\n'
    res += '/help Print this message\n'
    res += '/candidates List all HEPPA candidates\n'
    res += '/top n List top n HEPPA candidates (default: 5)\n'
    res += '/lead List candidates in the lead\n'
    res += '/vote Link the voting website'

    await event.respond(res)

@bot.on(events.NewMessage(pattern='(?i)/vote'))
async def vote(event):
    print("[+] Vote link requested")
    await event.respond(f"**Vote here:** {HEPPA}", link_preview=False)

@bot.on(events.NewMessage(pattern='(?i)/lead'))
async def lead(event):
    print("[+] Lead listing requested")
    candidates = parseHeppa()
    cutoff = candidates[0].approvals
    res = buildResponse([x for x in candidates if x.approvals >= cutoff and x.vetoes < 1])
    await event.respond(res, link_preview=False)

@bot.on(events.NewMessage(pattern='(?i)/candidates'))
async def candidates(event):
    print("[+] Candidate listing requested")
    candidates = parseHeppa()
    await event.respond(buildResponse(candidates), link_preview=False)

@bot.on(events.NewMessage(pattern='(?i)/top ?(\d*)'))
async def top(event):
    amount = 5

    if event.pattern_match.group(1):
        amount = int(event.pattern_match.group(1))

    print(f"[+] Top {amount} requested")
    if amount > 0:
        candidates = parseHeppa()
        await event.respond(buildResponse(candidates[:amount]), link_preview=False)

def buildResponse(candidates):
    res = ''

    if candidates:
        for candidate in candidates:
            res += f"**{APPROVALS}{candidate.approvals}** "
            if candidate.vetoes > 0:
                res += f"** {VETOES}{candidate.vetoes} **"
            if candidate.link:
                res += f"[{candidate.name}]({candidate.link})"
            else:
                res += candidate.name
            res += "\n"
    else:
        res += '**No candidates**'

    return res

def parseHeppa():
    res = urlopen(HEPPA)
    data = res.read()
    soup = BeautifulSoup(data)
    candidates = []

    # HTML parsing is messy. TODO: Edge cases, handling, all that.
    try:
        for row in soup.find_all('tr'):
            cols = row.find_all('td')
            if cols:
                if cols[0].a:
                    name = cols[0].a.string
                    link = cols[0].a.get('href')
                else:
                    name = cols[0].string.strip()
                    link = None
                nominator = cols[1].string
                tags = [n[1:-1] for n in cols[2].string[1:-1].split(', ')]
                approvals = int(cols[3].string)
                vetoers = [n[1:-1] for n in cols[5].string[1:-1].split(', ')]
                candidates.append(Candidate(name, link, nominator, tags, approvals, vetoers))
    except Exception as e:
        print(f"[!] Error {e}")
        
    return candidates

class Candidate:
    def __init__(self, name, link, nominator, tags, approvals, vetoers):
        self.name = name
        self.link = link
        self.nominator = nominator
        self.tags = tags
        self.approvals = approvals
        if len(vetoers[0]) > 0:
            self.vetoes = len(vetoers)
            self.vetoers = vetoers
        else:
            self.vetoes = 0
            self.vetoers = []


if __name__ == "__main__":
    print("[+] Starting Ponibot")
    bot.run_until_disconnected()
