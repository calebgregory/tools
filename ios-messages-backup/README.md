# <https://github.com/ReagentX/imessage-exporter>

> what is this?

this is a way to view messages taken from an iphone backup.

iphones store messages in a sqlite database.  they also store contacts in an addressbook sqlite db.  imessage-exporter is a nice, open-source, out-of-the-box CLI for generating an .html or .txt view of those messages (with media normalizing, and other neat features).  this directory contains scripts around those.

> why?

_apple_...  i don't want to purchase icloud.  i've always resisted it.  this is a way for my phone to lose its special role as "the" storage system of my messages.  i've waited too long to do this.  now i can finally clear up 30 GB of storage space on my 64 GB phone by deleting all of my messages, while still holding on to them.  search = ripgrep, silver-searcher, whatever.  just open the html file and read on, brother.

## future me

if you have taken another backup, change the value in `.secret`, then `run.sh {date}`.  you can use `serve.sh` to browse the messages from an index / table-of-contents.
