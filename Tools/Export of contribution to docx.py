from docx import Document
import pyodbc
import Configuration
import pickle
from docx.enum.text import WD_COLOR_INDEX
from Mechanics import PageCreator, SQLConnector, ContributionComparator, CustomLogging, ExclusionsDict, xWikiClient
SQLConfig = Configuration.SQLConfig()
SQLConnector = SQLConnector(SQLConfig)
xWikiConfig = Configuration.xWikiConfig('Migration pool')
xWikiClient = xWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)

PageTitle = '3. Backup copy Schedule (Copy intervals)'
platform = 'xWIKI'
SQLQuery = SQLConnector.GetDatagramsByPageTitleandPlatform(PageTitle, platform)
datagram = SQLQuery[0]
contributors_datagram = SQLQuery[1]
Colors = ['BRIGHT_GREEN','YELLOW','TEAL','VIOLET','PINK','RED','TURQUOISE','DARK_YELLOW','GRAY_50','GRAY_25','DARK_BLUE','DARK_RED','BLUE','GREEN']
ColorsByUser = {}
UniqueUsers = set(contributors_datagram.values())
for index, contributor in enumerate(UniqueUsers):
    ColorsByUser.update({contributor: Colors[index]})
#print(dir(WD_COLOR_INDEX))
#making docx
document = Document()
document.add_heading(PageTitle)
#filling docx
paragraph_authors = document.add_paragraph()
paragraph_authors.add_run('Legend:')
run = paragraph_authors.add_run()
run.add_break()
for user in ColorsByUser:
    Current_color = ColorsByUser[user]
    font = paragraph_authors.add_run(user).font
    font.highlight_color = getattr(WD_COLOR_INDEX, Current_color)
    run = paragraph_authors.add_run()
    run.add_break()

paragraph = document.add_paragraph()
paragraph.add_run('Page content by authors:')
run = paragraph.add_run()
run.add_break()
for letter in datagram:
    Current_color = ColorsByUser[contributors_datagram[letter[1]]]
    font = paragraph.add_run(letter[0]).font
    font.highlight_color = getattr(WD_COLOR_INDEX,Current_color)
document.save('C:\Temp\\' +PageTitle+ '.docx')
