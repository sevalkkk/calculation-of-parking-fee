from datetime import datetime
import cv2
from matplotlib import pyplot as plt
import numpy as np
import imutils
import easyocr
import sqlite3


pic = input("Resim giriniz: ")
img = cv2.imread(pic)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#cv2.imshow("Licence",gray) #griye çevrilmiş görüntü
bfilter = cv2.bilateralFilter(gray, 11, 17, 17) #Gürültü azaltma
edged = cv2.Canny(bfilter, 30, 200) #Kenar algılama
#cv2.imshow("Licence2",edged) #Kenarları algılanmış görüntü
keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
contours = imutils.grab_contours(keypoints)#plakadaki anahtar bölgelerin işaretlenmesi
contours = sorted(contours, key=cv2.contourArea, reverse=True)
location = None
for contour in contours:
    approx = cv2.approxPolyDP(contour, 40, True) 
    if len(approx) ==4:
        location = approx
        break

mask = np.zeros(gray.shape, np.uint8)
new_image = cv2.drawContours(mask, [location], 0,255, -1)
new_image = cv2.bitwise_and(img, img, mask=mask)
#cv2.imshow("Licence3",new_image) #Sadece Plakayı gösterir.
(x,y) = np.where(mask==255)
(x1, y1) = (np.min(x), np.min(y)) 
(x2, y2) = (np.max(x), np.max(y))
cropped_image = gray[x1:x2+1, y1:y2+1]
cv2.imshow("Licence4",cropped_image) #Plakayı Keserek Gösteriyor.(kırpılmış hali)
reader = easyocr.Reader(['en']) #Plakada kullanılan dil
result = reader.readtext(cropped_image) 
print(result) #kesilmiş plakanın döndürülmesi

text = result[1][-2] 

font = cv2.FONT_HERSHEY_SIMPLEX
res = cv2.putText(img, text=text, org=(approx[0][0][0], approx[1][0][1]+60), fontFace=font, fontScale=1, color=(0,255,0), thickness=2,
lineType=cv2.LINE_AA)
res = cv2.rectangle(img, tuple(approx[0][0]), tuple(approx[3][0]), (0,255,0),3) #plaka bölgesinin çevresinde oluşturulan 
# dikdörtgenin şekillendirilmesi

con = sqlite3.connect('plaka.db') #python sql bağlantısının kurulması
cur = con.cursor() #bağlantısı sağlanan veritabanın cursor yardımıyla tek tek gezilmesi işlemi
konum = ""
length = 0
cur.execute("SELECT * FROM Arac WHERE Plaka=?",(text,)) #tablodan plakaların çekilmesi işlemi

rows2 = cur.fetchall()#tüm plakaları çek

if(len(rows2)==0): #eğer tablodan çekilen plakalar null ise yani araç henüz park edilmemişse
        
    while(len(konum)!=2 or length != 0 ): #konum null iken 
        konum = input("Araçın Konumunu Giriniz:(Örn: A2) ")
        cur.execute("SELECT * FROM Arac WHERE Konum=?",(konum,)) #tablodan konumu çek
        rows = cur.fetchall() #tüm konumları çek
        length = len(rows)
        if length != 0: #tablodan çekilen konum null değilse yani o konumda bir araç var ise
            print("Girmiş olduğunuz alan dolu. Başka alan giriniz.")
        if(len(konum)!=2):
            print("Lütfen doğru konum giriniz.")
cur.execute("SELECT * FROM Arac WHERE Plaka=?",(text,)) #tablodan plakaları seç

rows = cur.fetchall() #seçilen tüm plakaları rows değişkenine ata.
length = len(rows) 
if length != 0: #eğer plakanın uzunluğu null değilse yani içeride araç varsa
    hour = rows[0][1]
    minute = rows[0][2]
    location = rows[0][3]
    nHour = datetime.now().hour #şu anki anlık saatin akrep kısmı
    nMinute = datetime.now().minute #şu anki anlık saatin yelkovan kısmı
    cHour = nHour - hour #otoparkta geçirilen süre (saat olarak)
    cMinute = nMinute - minute  #otoparkta geçirilen süre (dakika olarak)
    if(cMinute < 0): #çıkış ile giriş zamanı aranızdaki fark alındığında dakika eksi değer alırsa
        cMinute = 60 + cMinute #dakikaya 60 ekle ve alt satırda da saati bir azalt .
        cHour = cHour -1
    print("Saat ",cHour,"Dakika",cMinute,"Konum",location) #plakaya ait otoparkta kalış saati ve dakikasını ve plaknın bulunduğu konumu yazdır.
    price = cHour * 10 #otoparkta kaldığı saati otopark ücreti(10) ile çarp ve ödemesi gereken miktarı belirle.
    print("Araç Konumu: ",location,"Ücret: ",price) #çıkış yapılması istenen aracın konumu ve ödemesi gereken ücreti yazdır.
    print("İyi günler.") #çıkış yapıldı.
    cur.execute("DELETE FROM Arac WHERE Plaka =?",(text,)) #çıkış yapan aracın kaydının veritabanından silinmesi
    con.commit()
#cur.execute("INSERT INTO Arac VALUES(?,?,?,?)",(text,hour,minute,location))
else :
    cur.execute("INSERT INTO Arac VALUES(?,?,?,?)",(text,datetime.now().hour,datetime.now().minute,konum)) #eğer araç daha önce giriş yapmadıysa 
    #aracın plakasının o anki giriş saati ve dakikasının ayriyeten kullanıcan istenilen konumun veritabanına kaydedilmesi
    print("Hoşgeldiniz!")
    con.commit()
con.close()

while(True):
    cv2.imshow("Licence 5",res) #plakanın son halinin gösterilmesi
    if cv2.waitKey(1) & 0xFF == ord('q'):  # q ile çıkış yapabilirsiniz.
        break