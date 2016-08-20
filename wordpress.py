# -*- coding: utf8 -*- 
#! python 
# Copyright (c) 2008 Luis Rei
#
# 2011 - Modifications by Adam Morris
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# Notes:
# - currently does not handle images, attachments or comments
# - was only tested on MacOS X (10.5)
# - not "carefully" developed e.g. poor exception handling, little testing, ...
# - see also http://wordpress.com/blog/2006/06/12/xml-import-export/
import os, sys, getopt, time, urllib
from xml.dom import minidom
__author__ = 'Luis Rei (luis.rei@gmail.com)'
__homepage__ = 'http://luisrei.com'
__version__ = '1.0'
__date__ = '2008/03/23'
reload(sys)
sys.setdefaultencoding( "utf-8" )
def convert(infile, outdir, splitByYear, categoryDirs):
    """Convert WordPress Export File to multiple html files.
    Keyword arguments:
    infile -- the location of the WordPress Export File
    outdir -- the directory where the files will be created
    authorDirs -- if true, create different directories for each author
    categoryDirs -- if true, create directories for each category
    """
    # First we parse the XML file into a list of posts.
    # Each post is a dictionary
    dom = minidom.parse(infile)
    blog = [] # list that will contain all posts
    firstYear = None
    lastYear = None
    
    for node in dom.getElementsByTagName('item'):
        #Fix bug with negative years, which have unspecified behaviour in ISO standard. Causes a crash due to the formatter not expecting a negative sign before the year digits
        
        #Split date by spaces into it's componenents (weekday, month day, month, year, etc)
        rawDate = node.getElementsByTagName('pubDate')[0].firstChild.data.split(" ")
        
        #Strip negative sign from date
        rawDate[3] = rawDate[3].lstrip("-")
        
        #Join array back into a string
        sanitizedDate = ' '.join(rawDate)
        
        post = dict()
        post["title"] = node.getElementsByTagName('title')[0].firstChild.data if node.getElementsByTagName('title')[0].firstChild else ''
        post["date"] = sanitizedDate if sanitizedDate else ''
        post["time"] = time.strftime("%Y%m%dT%H%M%SZ",time.strptime(post["date"], "%a, %d %b %Y %H:%M:%S +0000")) if post["date"] else ''
        post["year"] = int(time.strftime("%Y",time.strptime(post["date"], "%a, %d %b %Y %H:%M:%S +0000"))) if post["date"] else ''
        if post["year"] and (firstYear == None or post["year"] < firstYear):
            firstYear = post["year"]
        if post["year"]  and (lastYear == None  or post["year"] > lastYear):
            lastYear = post["year"]
        post["author"] = node.getElementsByTagName('dc:creator')[0].firstChild.data if node.getElementsByTagName('dc:creator')[0].firstChild else ''
        post["id"] = node.getElementsByTagName('wp:post_id')[0].firstChild.data if node.getElementsByTagName('wp:post_id')[0].firstChild else ''
        post["text"] = node.getElementsByTagName('content:encoded')[0].firstChild.data if node.getElementsByTagName('content:encoded')[0].firstChild else ''
        # wp:attachment_url could be use to download attachments
        # Get the categories
        tempCategories = []
        for subnode in node.getElementsByTagName('category'):
            tempCategories.append(subnode.getAttribute('nicename'))
        categories = [x for x in tempCategories if x != '']
        post["categories"] = categories
        # Add post to the list of all posts
        blog.append(post)
    # Then we create the directories and HTML files from the list of posts.
    # The "base" directory
    outdir += "/wordpress/"
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    os.chdir(outdir)
    files = {}
    if splitByYear:
        for i in range(firstYear,lastYear+1):
            filename = "{0}.enex".format(i)
            files[i] = open(filename, 'w')
    else:
        files[0] = open("wordpress.enex", 'w')
    header = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export.dtd">
<en-export export-date="{0}" application="Evernote" version="Evernote Mac 2.2.1 (154267)">
""".format(time.strftime("%Y%m%dT%H%M%SZ",time.gmtime()))
    for f in files:
        files[f].write(header)
    for post in blog:
        # Add a meta tag to specify charset (UTF-8) in the HTML file
        meta = """\n<note><title>{0}</title>""".format(post["title"].encode('utf-8').replace("&","+"))
        start = """<content><![CDATA[<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>"""
        files[post["year"] if splitByYear else 0].write(meta+start+"\n")
        # Convert the unicode object to a string that can be written to a file
        # with the proper encoding (UTF-8)
        text = post["text"].encode('utf-8')
        # Replace simple newlines with + newline so that the HTML file
        # represents the original post more accurately
        text = text.replace("\n","<br/>\n")
        files[post["year"] if splitByYear else 0].write(text)
        # Finalize HTML
        end = "\n</en-note>\n]]></content><created>{0}</created><updated>{0}</updated>".format(post["time"])
        if categoryDirs:
            if post["categories"] != None:
                for category in post["categories"]:
                    end += "<tag>{0}</tag>".format(urllib.unquote(str(category.title())).decode('utf-8'))
        end += "<note-attributes/></note>"
        files[post["year"] if splitByYear else 0].write(end)
    lastend="\n</en-export>"
    for f in files:
        files[f].write(lastend)
        files[f].close()

def usage(pname):
    """Displays usage information
    keyword arguments:
    pname -- program name (e.g. obtained as argv[0])
    """
    print """python {0} [-hac] [-o outdir] infile
    Converts a WordPress Export File to multiple html files.
    Options:
        -h,--help\tDisplays this information.
        -y,--create separte files by year
        -c,--categories\tCreate directory structure from post categories.
        -o,--outdir\tSpecify a directory for the output.
    Example:
    python {1} -y -c -o ~/TEMP ~/wordpress.2008-03-20.xml
    """.format(pname, pname)

def main(argv):
    outdir = ""
    splitByYear = False
    categories = False
    try:
        opts, args = getopt.getopt(argv[1:], "hy:o:c", ["help", "year", "outdir", "categories"])
    except getopt.GetoptError, err:
        print str(err)
        usage(argv[0])
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(argv[0])
            sys.exit()
        elif opt in ("-y", "--year"):
            splitByYear = True
        elif opt in ("-c", "--categories"):
            categories = True
        elif opt in ("-o", "--outdir"):
            outdir = arg
    infile = "".join(args)
    if infile == "":
        print "Error: Missing Argument: missing wordpress export file."
        usage(argv[0])
        sys.exit(3)
    if outdir == "":
        # Use the current directory
        outdir = os.getcwd()
    convert(infile, outdir, splitByYear, categories)
if __name__ == "__main__":
    main(sys.argv)
