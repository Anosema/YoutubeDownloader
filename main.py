from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QLineEdit, QPushButton, QComboBox
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from sys import argv, exit

from os import remove, system, mkdir
from pytube import YouTube
from requests import get
from json import loads
from time import sleep
h = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}

try: mkdir("YoutubeDownloader")
except: pass
try: mkdir("YoutubeDownloader\\AudioFolder")
except: pass
try: mkdir("YoutubeDownloader\\VideoFolder")
except: pass

def getIndividualLinks(link):
	if "playlist" in link:
		r = get(link, headers=h)
		l = []
		for i in r.text.split("\n"):
			if "videoId" in i:
				t = i.split("var ytInitialData = ")
				for j in t[1].replace("}", "}\n").split("\n"):
					if "watchEndpoint" in j and "\"index\":" in j:
						l += ["https://youtube.com/watch?v="+j.split("\"")[5]]
		return l
	elif "youtube.com/watch?v=" in link:
		return [link]
	elif "youtu.be/" in link:
		return [f"https://youtube.com/watch?v={link.split('/')[-1]}"]
	else:
		print("no valid")
getName = lambda link: loads(get("https://www.youtube.com/oembed?url=" + link + "&format=json", headers=h).text)["title"]

class mainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setMinimumSize(800, 600)
		self.linkEntry = QLineEdit(self)
		self.linkEntry.setGeometry(10, 10, 180, 25)
		self.modeBox = QComboBox(self)
		self.modeBox.addItems(["Great audio, no video", "No audio, great video", "Great audio, great video"])
		self.modeBox.setGeometry(10, 50, 180, 25)
		self.validateButton = QPushButton("Validate", self)
		self.validateButton.setGeometry(10, 90, 180, 25)
		self.validateButton.clicked.connect(self.startDownload)
		self.linksTable = QTableWidget(self)
		self.linksTable.setGeometry(200, 10, 600, 600)
		self.linksTable.setColumnCount(3)
		self.linksTable.setHorizontalHeaderLabels(["Link", "Title", "State"])

		self.show()

	def startDownload(self):
		def cell(text):
			c = QTableWidgetItem(text)
			c.setTextAlignment(Qt.AlignCenter)
			c.setFlags(Qt.ItemIsEditable)
			return c
		self.mode = self.modeBox.currentText()
		self.pl = getIndividualLinks(self.linkEntry.text())
		if self.pl:
			self.linksTable.clear()
			self.linksTable.setRowCount(len(self.pl))
			self.linksTable.setHorizontalHeaderLabels(["Link", "Title", "State"])
			self.t = []
			for x, b in enumerate(self.pl):
				self.linksTable.setItem(x, 0, cell(b))
				self.linksTable.setItem(x, 1, cell(getName(b)))
				self.linksTable.setItem(x, 2, cell("Started"))
				self.t.append(downloaderThread(self, b, x))
				self.t[-1].start()

	def updateTable(self, l):
		self.linksTable.item(l[0], 2).setText(l[1])
	def deleteFile(self, path):
		try:
			remove(path)
		except:
			print(path)


	def resizeEvent(self, e):
		header = self.linksTable.horizontalHeader()
		header.setSectionResizeMode(QHeaderView.ResizeToContents)
		header.setSectionResizeMode(1, QHeaderView.Stretch)

	def closeEvent(self, e):
		for i in self.t:
			i.terminate()

class downloaderThread(QThread):
	tableUpdater = pyqtSignal(tuple)
	fileRemover = pyqtSignal(str)
	def __init__(self, p, link, x):
		super().__init__(p)
		self.x = x
		self.link = link
		self.tableUpdater.connect(self.parent().updateTable)
		self.fileRemover.connect(self.parent().deleteFile)

	def run(self):
		if self.parent().mode == "Great audio, no video":
			self.tableUpdater.emit((self.x, "Processing"))
			yt = YouTube(self.link)
			self.tableUpdater.emit((self.x, "Downloading"))
			pathAudio = yt.streams.filter(progressive=False, type="audio").order_by("abr").desc().first().download("YoutubeDownloader\\AudioFolder")
			system(f"ffmpeg -loglevel quiet -hide_banner -y -i \"{pathAudio}\" -vn -ab 128k -ar 44100 -y \"" + "\\".join(pathAudio.replace("AudioFolder", "").split("\\")[:-1]) + pathAudio.split("\\")[-1].replace(".webm", "") + ".mp3\"")
			self.tableUpdater.emit((self.x, "Cleaning"))
			self.fileRemover.emit(pathAudio)
			self.tableUpdater.emit((self.x, "Done"))

		elif self.parent().mode == "No audio, great video":
			self.tableUpdater.emit((self.x, "Processing"))
			yt = YouTube(self.link)
			self.tableUpdater.emit((self.x, "Downloading"))
			pathAudio = yt.streams.filter(progressive=False, type="video").order_by("resolution").desc().first().download("YoutubeDownloader\\VideoFolder")
			system(f"ffmpeg -loglevel quiet -hide_banner -y -i \"{pathVideo}\" -vn -ab 128k -ar 44100 -y \"" + "\\".join(pathVideo.replace("VideoFolder", "").split("\\")[:-1]) + pathVideo.split("\\")[-1].replace(".webm", "") + ".mp4\"")
			self.tableUpdater.emit((self.x, "Cleaning"))
			self.fileRemover.emit(pathVideo)
			self.tableUpdater.emit((self.x, "Done"))

		elif self.parent().mode == "Great audio, great video":
			self.tableUpdater.emit((self.x, "Processing"))
			yt = YouTube(self.link)
			self.tableUpdater.emit((self.x, "Downloading"))
			pathVideo = yt.streams.filter(progressive=False, type="video").order_by("resolution").desc().first().download("YoutubeDownloader\\VideoFolder")
			pathAudio = yt.streams.filter(progressive=False, type="audio").order_by("abr").desc().first().download("YoutubeDownloader\\AudioFolder")
			self.tableUpdater.emit((self.x, "Fusionning"))
			system(f"ffmpeg -loglevel quiet -hide_banner -y -i \"{pathVideo}\" -i \"{pathAudio}\" -c:v copy -c:a aac \"" + "\\".join(pathVideo.replace("VideoFolder", "").split("\\")[:-1]) + pathVideo.split("\\")[-1].replace(".webm", "") + ".mp4\"")
			self.tableUpdater.emit((self.x, "Cleaning"))
			self.fileRemover.emit(pathVideo)
			self.fileRemover.emit(pathAudio)
			self.tableUpdater.emit((self.x, "Done"))


app = QApplication(argv)
mw = mainWindow()
exit(app.exec_())
