#!/usr/bin/env python
#
# IRC Bot to give responses as "Pinky", based on "Pinky and the Brain".
#
# Code originally based on example bot and irc-bot class from
# Joel Rosdahl <joel@rosdahl.net>, author of included python-irclib.
#


"""An IRC bot to read youtube info.

This is an example bot that uses the SingleServerIRCBot class from
ircbot.py.  The bot enters a channel and listens for commands in
private messages and channel traffic.  Commands in channel messages
are given by prefixing the text by the bot name followed by a colon.

"""

import sys, string, random, time, urlparse, re
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower
from xml.dom import minidom
from urllib import urlopen
import botcommon

#---------------------------------------------------------------------
# Actual code.
#
# WolfBot subclasses a basic 'bot' class, which subclasses a basic
# IRC-client class, which uses the python-irc library.  Thanks to Joel
# Rosdahl for the great framework!


class PinkyBot(SingleServerIRCBot):
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

  def get_info(self, id, target):
    "Returns youtube info"
    url = "https://gdata.youtube.com/feeds/api/videos/"+id+"?v=2"
    youtubeinfo = urlopen(url).read()
    xmldoc = minidom.parseString(youtubeinfo)
    itemlist = xmldoc.getElementsByTagName('title') 
    if len(itemlist) == 0:
      self.reply("No info :/", target)
      return
    self.reply("Title: " + itemlist[0].firstChild.nodeValue.encode('ascii', 'ignore'), target)

    authorlist = xmldoc.getElementsByTagName('author')
    namelist = authorlist[0].getElementsByTagName('name')
    self.reply("Author: " + namelist[0].firstChild.nodeValue.encode('ascii', 'ignore'), target)

    contentlist = xmldoc.getElementsByTagName('media:content')
    self.reply("Time: " + contentlist[0].getAttribute("duration"), target)
  
  def video_id(self, value):
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

  def do_command(self, e, cmd, from_private):
    """This is the function called whenever someone sends a public or
    private message addressed to the bot. (e.g. "bot: blah").  Parse
    the CMD, execute it, then reply either to public channel or via
    /msg, based on how the command was received.  E is the original
    event, and FROM_PRIVATE is the nick that sent the message."""

    videoId = self.video_id(cmd)

    if videoId is None:
      return

    if e.eventtype() == "pubmsg":
      # self.reply() sees 'from_private = None' and sends to public channel.
      target = None
    else:
      # assume that from_private comes from a 'privmsg' event.
      target = from_private.strip()

    self.get_info(videoId, target)

if __name__ == "__main__":
  try:
    botcommon.trivial_bot_main(PinkyBot)
  except KeyboardInterrupt:
    print "Shutting down."

