import sys
from PyQt5.QtCore import QAbstractListModel, QMargins, QPoint, Qt
from PyQt5.QtGui import QColor, QPalette
import openai
from PyQt5.QtWidgets import (
    QApplication,
    QLineEdit,
    QListView,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

USER_ME = 0
USER_THEM = 1

BUBBLE_COLORS = {USER_ME: "#90caf9", USER_THEM: "#a5d6a7"}

BUBBLE_PADDING = QMargins(15, 5, 15, 5)
TEXT_PADDING = QMargins(25, 15, 25, 15)
from PyQt5.QtWidgets import QStyledItemDelegate


class MessageDelegate(QStyledItemDelegate):
    """
    Draws each message.
    """

    def paint(self, painter, option, index):
        # "model.data" yönteminden kullanıcı ve mesaj tuple olarak alınır
        user, text = index.model().data(index, Qt.DisplayRole)

        # option.rect contains our item dimensions. We need to pad it a bit
        # to give us space from the edge to draw our shape.

        bubblerect = option.rect.marginsRemoved(BUBBLE_PADDING)
        textrect = option.rect.marginsRemoved(TEXT_PADDING)

        # Baloncuk çizilirken, kimin mesajı gönderdiğine bağlı olarak renk + ok konumu değiştir.
        # Baloncuk, kenarında bir üçgen olan yuvarlatılmış bir dikdörtgendir.

        painter.setPen(Qt.NoPen)
        color = QColor(BUBBLE_COLORS[user])
        painter.setBrush(color)
        painter.drawRoundedRect(bubblerect, 10, 10)

        #Balonun hangi yönde olacağına karar veririz

        if user == USER_ME:
            p1 = bubblerect.topRight()
        else:
            p1 = bubblerect.topLeft()
        painter.drawPolygon(p1 + QPoint(-20, 0), p1 + QPoint(20, 0), p1 + QPoint(0, 20))

        #  Mesajı ekleyelim
        painter.setPen(Qt.black)
        painter.drawText(textrect, Qt.TextWordWrap, text)

    def sizeHint(self, option, index):
        _, text = index.model().data(index, Qt.DisplayRole)


        #Metnin gerektireceği boyutları hesaplıyoruz
        metrics = QApplication.fontMetrics()
        rect = option.rect.marginsRemoved(TEXT_PADDING)
        rect = metrics.boundingRect(rect, Qt.TextWordWrap, text)
        rect = rect.marginsAdded(TEXT_PADDING)  # Yeniden kenar boşlukları ekliyoruz kutuya.
        return rect.size()


class MessageModel(QAbstractListModel):
    def __init__(self, *args, **kwargs):
        super(MessageModel, self).__init__(*args, **kwargs)
        self.messages = []

        
    def data(self, index, role):
        if role == Qt.DisplayRole:
            #Burada, kullanıcı ve mesajı tuple olarak dönderiyoruz.
            return self.messages[index.row()]

    def rowCount(self, index):
        return len(self.messages)

    def add_message(self, who, text):
        """
        Mesaj listesine mesajı ekliyoruz
        """
        if text:  # text boşsa boşuna ekleme işlemi yapmıyoruz.
            self.messages.append((who, text))
            # Yeni mesaj geldiği için arayüzü yeniden refreshliyoruz.
            self.layoutChanged.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        l = QVBoxLayout()
        
        
        openai.api_key = self.get_api_key()
        #Chatgpt promptlarını biriktireceğimiz listeyi oluşturuyoruz
        #Konuşmanın öncesinin bilebilmeliki sohbet tarzı olsun
        self.messages_gpt = []

        #Chatgpt'ye api docs bilgilerine göre bir rol atamamız gerekiyor.
        self.messages_gpt.append({"role": "assistant", "content": "You’re a kind helpful assistant"})
        
        #İnput alanı için default yazı
        self.message_input = QLineEdit("Enter message here")

        # Buton ayarları
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height

        #Gönder butonu
        self.btn1 = QPushButton("Gönder")

        #Arayüz için mesajların saklanacağı ListView objesi
        self.messages = QListView()

        palette = QPalette()
        palette.setColor(QPalette.Base, QColor(169,169,169))
        self.messages.setPalette(palette)
        # Mesajları göstermek için
        self.messages.setItemDelegate(MessageDelegate())

        self.model = MessageModel()
        self.messages.setModel(self.model)

        #Gönder butonuna tıklanınca çalışacak fonksiyonun bağlanması
        self.btn1.pressed.connect(self.message_to)

        #Widgetleri ekliyoruz
        l.addWidget(self.messages)
        l.addWidget(self.message_input)
        l.addWidget(self.btn1)


        self.w = QWidget()
        self.w.setLayout(l)
        self.setCentralWidget(self.w)

    
    def get_api_key(self):
        import json
  
        # Json dosyasını açıyoruz.
        f = open('config.json')
        
        
        data = json.load(f)
        api_key = data["openai key"]
        return api_key

    def message_to(self):
        
        
        #Gönder butonuna tıklanınca mesaj inputtan alınır.
        #Yazılan mesaj me olarak mesaj modeline eklenir
        self.model.add_message(USER_ME, self.message_input.text())

        #Ayrı olarak chatgpt mesajlar listesine de ekleriz
        self.messages_gpt.append({"role": "user", "content": self.message_input.text()})

        #Chatgpt ye mesaj listesini yollarız ve son soruya cevap verir.
        completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", #Yapay zeka modellerinden birisi (davinci vs kullanılabilir)
        messages=self.messages_gpt)
        chat_response = completion.choices[0].message.content

        #Chatgpt den gelen mesaj modele karşı taraf olarak eklenir
        self.model.add_message(USER_THEM,chat_response )

        #Chatgptden gelen mesaj chatgpt mesaj listesine eklenir
        self.messages_gpt.append({"role": "assistant", "content": chat_response})

        #Mesaj kutucuğunu temizler
        self.message_input.clear()




app = QApplication(sys.argv)
window = MainWindow()
window.setWindowTitle("Sağlık Asistanım 🩺")
palette = QPalette()
palette.setColor(QPalette.Window, QColor(80, 80, 80))
window.setPalette(palette)
window.show()
app.exec_()