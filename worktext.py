import pyzmail, imapclient, pprint, openpyxl, datetime, os, time, logging
from twilio.rest import Client

logging.basicConfig(filename='/opt/python/log/worktext.log', level=logging.DEBUG)
#logging.basicConfig(filename='/tmp/my.log', level=logging.DEBUG)
accountSID = 'ACd2b73bc31fb0e249fe8540c3d6ba32a1'
authToken = os.environ['AUTH_TOKEN']
myTwilioNumber = '+15126400707 '
myCellPhone = os.environ['CELL_PHONE_NUMBER']

def updateTimes():
	times = {}
	imapObj = imapclient.IMAPClient('imap.gmail.com', ssl=True)
	imapObj.login('parker.speich@gmail.com', os.environ['PASS'])
	print("Logged In")
	imapObj.select_folder('INBOX', readonly=True)
	uids = imapObj.gmail_search('Dominos Schedule')
	rawMessages = imapObj.fetch(uids, ['BODY[]'])
	print('Fetched: '+str(len(uids))+' Emails')
	for index,uid in enumerate(range(len(uids)-2,len(uids))):
		msg = pyzmail.PyzMessage.factory(rawMessages[uids[uid]][b'BODY[]'])
		print('Parsing Email: '+str((index+1)))
		for part in msg.mailparts:
			if part.type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
				payload = part.get_payload()
				with open('temp.xlsx','wb') as f:
					f.write(payload)
				wb = openpyxl.load_workbook('temp.xlsx',read_only = True)
				sheet = wb[wb.sheetnames[0]]
				for r in range(1,100):
					if sheet.cell(column = 3, row = r).value == "Parker":
						row = r
						break
				for column in range(7):
					times[sheet.cell(column = 6, row = 1).value+datetime.timedelta(days=column)] = sheet.cell(column = column+6, row = row).value
	return times

def main():
	print('Updating Time List')
	times = updateTimes()

	#Check to see if it is one hour before work and send a text
	currentDate = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)
	currentTime = datetime.time(datetime.datetime.now().hour,datetime.datetime.now().minute)
	if times[currentDate] != 'off':
		if times[currentDate].hour < 9:
			oneHrBeforeWork = datetime.time(times[currentDate].hour+11,times[currentDate].minute)
		else:
			oneHrBeforeWork = datetime.time(times[currentDate].hour-1,times[currentDate].minute)
		logging.debug("Current time = "+str(currentTime))
		logging.debug("One hr before work = "+str(oneHrBeforeWork))
		if (currentTime == oneHrBeforeWork):
			twilioCli = Client(accountSID, authToken)
			message = twilioCli.messages.create(body="You have work at: "+str(times[currentDate])[:5], from_=myTwilioNumber, to=myCellPhone)
			print('Text Sent To: ',myCellPhone)
main()