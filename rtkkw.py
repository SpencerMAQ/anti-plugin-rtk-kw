﻿#
# Copyright: Robert Polz <robert.polz.cz@gmail.com>
# Batch-mode optimized by Vempele
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
# Automatic RTK keyword generation.
#
# Some parts of the code modified are by SpencerMAQ (Michael Spencer Quinto) <spencer.michael.q@gmail.com>

# NOTE: (TO SELF) I just cloned this because I thought the add-on stopped working
# It worked though when I changed the position of the KanjiInfo Field to "4", weird

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
    global cache                            # what is this for?
    model = mw.col.models.byName(rtkModel)  # get model (i.e. Japanese_OLD_KDamage-15AUG2015)
    mf = "mid:" + str(model['id'])
    ids = mw.col.findNotes(mf)
    for id in ids:
        note = mw.col.getNote(id)
        kanji = note[rtkKanjiField]
        keyword = note[rtkKeywordField]
        onyomi = note[rtkOnyomiField]
        kunyomi = note[rtkKunyomiField]

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

def onFocusLost(flag, n, fidx):
    src = None
    dst = None
    # have src and dst fields?
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

addHook('editFocusLost', onFocusLost)
addHook("browser.setupMenus", setupMenu)
