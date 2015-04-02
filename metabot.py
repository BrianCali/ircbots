#!/usr/bin/env python
#
# IRC Bot to display information on links posted
#
# Code originally based on example bot and irc-bot class from
# Joel Rosdahl <joel@rosdahl.net>, author of included python-irclib.
#

import sys, string, random, time, urlparse, re
from imgurpython import ImgurClient
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower
from xml.dom import minidom
from urllib import urlopen
import botcommon

class MetaBot(SingleServerIRCBot):
  def __init__(self, channel, nickname, server, port):
    SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
    self.channel = channel
    self.nickname = nickname
    self.queue = botcommon.OutputManager(self.connection)
    self.queue.start()
    self.start()

  def on_nicknameinuse(self, c, e):
    self.nickname = c.get_nickname() + "_"
    c.nick(self.nickname)

  def on_welcome(self, c, e):
    c.join(self.channel)

  def on_privmsg(self, c, e):
    from_nick = nm_to_n(e.source())
    self.do_command(e, e.arguments()[0], from_nick)

  def on_pubmsg(self, c, e):
    from_nick = nm_to_n(e.source())  
    self.do_command(e, e.arguments()[0], from_nick)

  def say_public(self, text):
    "Print TEXT into public channel, for all to see."
    self.queue.send(text, self.channel)

  def say_private(self, nick, text):
    "Send private message of TEXT to NICK."
    self.queue.send(text,nick)

  def reply(self, text, to_private=None):
    "Send TEXT to either public channel or TO_PRIVATE nick (if defined)."

    if to_private is not None:
      self.say_private(to_private, text)
    else:
      self.say_public(text)
  
  #def get_imgur_info(self, url):


  def get_youtube_id(self, value):
    """
    Examples:
    - http://youtu.be/SA2iWivDJiE
    - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    - http://www.youtube.com/embed/SA2iWivDJiE
    - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    """
    p = re.compile(ur'(?:youtube(?:-nocookie)?\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^"&?/ ]{11})', re.IGNORECASE)
    m = re.search(p, value)
    if m is None:
      return None
    return m.group(1)

  # Type Specific Functions
  # 

  # Imgur Link
  def get_imgur_info(self, url):
    # Returns imgur link info.
    p = re.compile(ur'(?:.*)(?:http(?:s|)://(?:www\.|i\.|)imgur\.com/)([A-Za-z0-9]*)(?:(?:\.[jpgt]|\ |$).*)', re.IGNORECASE)
    m = re.search(p, url)
    if m is None:
      return None

    client = ImgurClient('', '')
    img = client.get_image(m.group(1))
    lines = []

    lines.append("Title: " + img.title)
    return lines

  # Youtube Link
  def get_youtube_info(self, url):
    "Returns youtube info"
    yt_id = self.get_youtube_id(url)
    if yt_id is None:
      return

    api_url = "https://gdata.youtube.com/feeds/api/videos/"+yt_id+"?v=2"
    youtubeinfo = urlopen(api_url).read()
    xmldoc = minidom.parseString(youtubeinfo)
    itemlist = xmldoc.getElementsByTagName('title') 
    if len(itemlist) == 0:
      return

    lines = []

    lines.append("Title: " + itemlist[0].firstChild.nodeValue.encode('ascii', 'ignore'))

    authorlist = xmldoc.getElementsByTagName('author')
    namelist = authorlist[0].getElementsByTagName('name')
    lines.append("Author: " + namelist[0].firstChild.nodeValue.encode('ascii', 'ignore'))

    contentlist = xmldoc.getElementsByTagName('media:content')
    lines.append("Time: " + contentlist[0].getAttribute("duration"))
    return lines

  def get_url_type(self, url):
    if re.match('.*(http(s|)://).*', url) is None:
        return None

    if re.match('.*(http(s|)://(www\.|)(youtube|youtu\.be)).*', url) is not None:
        return 'youtube'
    elif re.match('.*(http(s|)://(www\.|i\.|)imgur).*', url) is not None:
        return 'imgur'

    return None

  get_url_info = {
    'youtube': get_youtube_info,
    'imgur': get_imgur_info
  }

  def do_command(self, e, cmd, from_private):
    """This is the function called whenever someone sends a public or
    private message addressed to the bot. (e.g. "bot: blah").  Parse
    the CMD, execute it, then reply either to public channel or via
    /msg, based on how the command was received.  E is the original
    event, and FROM_PRIVATE is the nick that sent the message."""
  
    url_type = self.get_url_type(cmd)

    if url_type is None:
      return

    if url_type not in self.get_url_info:
      return

    if e.eventtype() == "pubmsg":
      # self.reply() sees 'from_private = None' and sends to public channel.
      target = None
    else:
      # assume that from_private comes from a 'privmsg' event.
      target = from_private.strip()


    lines = self.get_url_info[url_type](self, cmd)
    if lines is None:
      return

    for msg in lines:
      self.reply(msg, target)

if __name__ == "__main__":
  try:
    botcommon.trivial_bot_main(MetaBot)
  except KeyboardInterrupt:
    print "Shutting down."

