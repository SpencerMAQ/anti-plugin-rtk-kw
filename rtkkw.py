#
# Copyright: Robert Polz <robert.polz.cz@gmail.com>
# Batch-mode optimized by Vempele
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
# Automatic RTK keyword generation.
#
# Some parts of the code modified are by SpencerMAQ (Michael Spencer Quinto) <spencer.michael.q@gmail.com>

# NOTE: (TO SELF) I just cloned this because I thought the add-on stopped working
# It worked though when I changed the position of the KanjiInfo Field to "4", weird

# TODO: change the code so that this plugin overwrites the existing contents of the field

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.hooks import addHook
from aqt import mw
from aqt.utils import showInfo

srcFields = ['Expression']
dstFields = ['Kanji-Info']
rtkModel = 'Japanese_OLD_KDamage-15AUG2015'
rtkKanjiField = 'Kanji'
rtkKeywordField = 'Keyword'
rtkOnyomiField = 'Onyomi'
rtkKunyomiField = 'First kunyomi'

# getKeywords
##########################################################################
cache = {}


def generateCache():
    global cache
    model = mw.col.models.byName(rtkModel)  # get model (i.e. Japanese_OLD_KDamage-15AUG2015)
    mf = "mid:" + str(model['id'])          # gives something like modile ID mid: 321039213, 'id' is an argument
    ids = mw.col.findNotes(mf)

    # findNotes defined as a function @ anki/collection.py line 559
    # this is the code for findNotes
    '''
    52..    class _Collection:
    ..
    559..       def findNotes(self, query):
    560..       return anki.find.Finder(self).findNotes(query)
    '''
    # the query sent is: mid: 321312321312321
    # as for Finder(self), self refers to the _Colleciton instance

    # anki/find.py
    # code for anki.find.Finder
    '''
    16.. class Finder:
    17..
    18.. def __init__(self, col):
    19..     self.col = col
    ..
    36..     def findCards(self, query, order=False):
    '''



    # origin of mw.col (from aqt/main.py)
    '''
    258..    def loadCollection(self):
    259..    cpath = self.pm.collectionPath()
    260..    try:
    261..        self.col = Collection(cpath, log=True)
    '''
    for id in ids:
        note = mw.col.getNote(id)
        kanji = note[rtkKanjiField]
        keyword = note[rtkKeywordField]
        onyomi = note[rtkOnyomiField]
        kunyomi = note[rtkKunyomiField]

        # cache is a global dictionary
        if kanji in cache:
            cache[kanji] += kanji + " - " + keyword + " - " + onyomi + " - " + kunyomi + \
                            ' <span style="font-weight:600;font-size:150%;color:#f5ad58">|</span> '
        else:
            cache[kanji] = kanji + " - " + keyword + " - " + onyomi + " - " + kunyomi + \
                           ' <span style="font-weight:600;font-size:150%;color:#f5ad58">|</span> '


def getKeywordsFast(expression):
    kw = ""
    for e in expression:
        if e in cache:
            kw += cache[e]
    return kw


def getKeywords(expression):
    model = mw.col.models.byName(rtkModel)
    mf = "mid:" + str(model['id'])
    kw = ""
    for e in expression:
        ef = rtkKanjiField + ":" + e
        f = mf + " " + ef
        ids = mw.col.findNotes(f)
        for id in ids:
            note = mw.col.getNote(id)
            kw = kw + e + " - " + note[rtkKeywordField] + "<br>"
    return kw


# Focus lost hook
##########################################################################

# n = note
# this is a hook added to 'editFocusLost'

# This is the way editFocusLost is set-up:
'''
from aqt/browser.py
1355..    def setupHooks(self):
..
1359..        addHook("editFocusLost", self.refreshCurrentCardFilter)

637..  def refreshCurrentCardFilter(self, flag, note, fidx):
638..          self.refreshCurrentCard(note)
639..          return flag

633..    def refreshCurrentCard(self, note):
634..        self.model.refreshNote(note)
635..        self._renderPreview(False)

############

33..    class DataModel(QAbstractTableModel):
34..
35..        def __init__(self, browser):
36..            QAbstractTableModel.__init__(self)
37..            self.browser = browser
38..            self.col = browser.col
..
..
51..        def refreshNote(self, note):
51..            refresh = False
51..            for c in note.cards():
51..                if c.id in self.cardObjs:
51..                    del self.cardObjs[c.id]
51..                    refresh = True
51..            if refresh:
51..                self.layoutChanged.emit()

'''
def onFocusLost(flag, n, fidx):
    src = None
    dst = None
    # have src and dst fields?

    # copied from Damien's Japanese Support plugin
    for c, name in enumerate(mw.col.models.fieldNames(n.model())):
        for f in srcFields:
            if name == f:
                src = f
                srcIdx = c
        for f in dstFields:
            if name == f:
                dst = f
    if not src or not dst:
        return flag
    # dst field already filled?
    if n[dst]:
        return flag
    # event coming from src field?
    if fidx != srcIdx:
        return flag
    # grab source text
    srcTxt = mw.col.media.strip(n[src])
    if not srcTxt:
        return flag
    # update field
    try:
        n[dst] = getKeywords(srcTxt)

    # TODO: When Anki 2.1 comes out, change syntax to support Py 3.5
    except Exception, e:
        raise
    return True


# Bulk keywords
##########################################################################

def regenerateKeywords(nids):
    mw.checkpoint("Bulk-add RTK Keywords")
    mw.progress.start()
    for nid in nids:
        note = mw.col.getNote(nid)

        src = None
        for fld in srcFields:
            if fld in note:
                src = fld
                break
        if not src:
            # no src field
            continue
        dst = None
        for fld in dstFields:
            if fld in note:
                dst = fld
                break
        if not dst:
            # no dst field
            continue
        if note[dst]:
            # already contains data, skip
            continue
        srcTxt = mw.col.media.strip(note[src])
        if not srcTxt.strip():
            continue
        try:
            note[dst] = getKeywordsFast(srcTxt)

        # TODO: When Anki 2.1 comes out, change syntax to support Py 3.5
        except Exception, e:
            raise
        note.flush()
    mw.progress.finish()
    mw.reset()


# Menu
##########################################################################

def setupMenu(browser):
    a = QAction("Bulk-add RTK Keywords", browser)
    browser.connect(a, SIGNAL("triggered()"), lambda e=browser: onRegenerate(e))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)
    if cache == {}:
        generateCache()


def onRegenerate(browser):
    regenerateKeywords(browser.selectedNotes())


# Init
##########################################################################

# called each time a field loses focus (what does that mean?), focus as in????
addHook('editFocusLost', onFocusLost)
# adds the Menu bar option @ the browser level
addHook("browser.setupMenus", setupMenu)
