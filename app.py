from flask import Flask
from flask import request,redirect,render_template,url_for,flash,session
from werkzeug.utils import secure_filename
from py2neo import Graph, Node, Relationship, NodeMatcher
from datetime import datetime, timedelta
import os
import pytesseract
from PIL import Image
import cv2
from ocr_core import ocr_core
from models import User

app = Flask(__name__)
app.secret_key = "super secret key"
UPLOAD_FOLDER = '/static/uploads/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif','jfif'])



def connect_database():
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "1234"))
    #tx = graph.begin()
    return graph

graph = Graph("bolt://localhost:7687", auth=("neo4j", "1234"))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET','POST'])
def login():

    if request.method == 'POST':
        username = request.form['text']
        password = request.form['password']
        
        resultUsername= graph.run("MATCH (a) WHERE a.name={x} RETURN a.name", x=username).evaluate()
        resultPassword= graph.run("MATCH (a) WHERE a.password={y} RETURN a.password", y=password).evaluate()
        if resultUsername == username and resultPassword == password:
            if resultUsername == 'admin':
                session['logged_in']=True
                session['name'] = username
                return redirect(url_for('admin'))
            else:
                session['name'] = username
                return redirect(url_for('user'))
        else:
            flash('Kullanici adi veya parola hatali','error')
            print('Veritabanı ile eşleşemedi')

    return render_template('login.html')
    
@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return render_template('upload.html', msg='No file selected')
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            return render_template('upload.html', msg='No file selected')

        if file and allowed_file(file.filename):
            file.save(os.path.join(os.getcwd() + UPLOAD_FOLDER, file.filename))

            # call the OCR function on it
            
            extracted_text = ocr_core(file)
            listele = extracted_text.split()
            print(listele)
            sayac = 0
            isbnNo = ''
            for i in listele:
                sayac+=1
                if i == "ISBN" or i == "ISBN:" or i == "ISBN: " or i=="lSBN" or i=="lSBN:":
                    #print("*******")
                    isbnNo=listele[sayac]
                    #print(listele[sayac])
                    #print("*******")
                    break
            a = isbnNo.split('—')
            bos = []
            for i in a:
                for j in i:
                   bos.append(j)
            print(bos.count)
            array_length = len(bos)
            i=0
            yedek_bos = bos.copy()
            for i in range(array_length):
                if bos[i] == "9" or bos[i] == "8" or bos[i] == "7" or bos[i] == "6" or bos[i] == "5" or bos[i] == "4" or bos[i] == "3" or bos[i] == "2" or bos[i] == "1" or bos[i] == "0":
                    #print("devamke")
                    pass
                else:
                    sil = bos[i]
                    yedek_bos.remove(sil)
                i+=1
            
            #print('bos: ',bos)
            #print('yedek bos: ',yedek_bos)
            x = "".join(yedek_bos)

            #print(x)
            #print(type(x))
            #sayi = int(x)
            #print(type(sayi))
            #print('son bos: ',bos)
            extracted_text = isbnNo
            kitapAdi = request.form['kitapAdi']
            #print(kitapAdi)
            
            kitap = Node("Book", kitap_adi=kitapAdi, isbn=x, stok=1)
            graph.create(kitap)
        
            # extract the text and display it
            return render_template('upload.html',
                                   msg='Successfully processed',
                                   extracted_text=extracted_text,
                                   img_src=UPLOAD_FOLDER + file.filename)
    elif request.method == 'GET':
        return render_template('upload.html')    


@app.route('/admin', methods=['GET','POST'])
def admin():
    return render_template('layout.html')




@app.route('/listele', methods=['GET','POST'])
def listele():

            userr = ""
            userr = session['name'] 
            listele = graph.run("MATCH (n:Login)-[r:HAS]-(b:Book) RETURN n.name, b.kitap_adi").data()
            print('listele: ' , listele)
            donenListeKapasitesi = len(listele)
            kullaniciAdiTopla=[]
            kitapAdiTopla=[]
            for i in range(0,donenListeKapasitesi):
                print(listele[i]['n.name'] , "  " , listele[i]['b.kitap_adi'])
                kullaniciAdiTopla.append(listele[i]['n.name'])
                kitapAdiTopla.append(listele[i]['b.kitap_adi'])
            
            return render_template('kitaplistele.html',kitapAdiTopla=kitapAdiTopla, 
                                    kullaniciAdiTopla=kullaniciAdiTopla,
                                    donenListeKapasitesi=donenListeKapasitesi)


    
@app.route('/kitapekle', methods=['GET','POST'])
def kitapekle():
    return render_template('kitap.html')

@app.route('/zamanatla', methods=['GET','POST'])
def zamanatla():
    if request.method == 'POST':
        gunSayisi = request.form['atlanacakGunSayisi']  
        veritabanındakiGunSayisi= graph.run("MATCH (a:Time) SET a.time={x} RETURN a.time", x=gunSayisi).evaluate()
        flash('Zaman Değiştirildi.','success')
        print(veritabanındakiGunSayisi)
    return render_template('zamanatla.html')


@app.route('/user', methods=['GET','POST'])
def user():
    userr = ""
    userr = session['name']
    return render_template('user.html', userr=userr)


@app.route('/kitapal', methods=['GET','POST'])
def kitapal():
        
            # Kitap Adi ve ISBN numarası PARSE işlemleri Başlangıcı
            
#************************************************************************************************************   
            
            
            userr = ""
            userr = session['name'] 
            listele = graph.run("MATCH (n:Book) WHERE n.stok=1 RETURN n.kitap_adi, n.isbn").to_ndarray()
            sya = 0
            ktp = []
            no = []
            Noo=''
            kitapA=''
            kitapAdiTopla = []
            kitapNoTopla=[]
            for e in listele:
                sya+=1
                #print('listele içindeki eleman sayisi:',sya)
            
            for sayac in range(sya):
                str2 = ''.join(str(e) for e in listele[sayac])
                #print('Listele icindeki eleman:', str2)
                for i in str2:
                    #print('str2 içindeki string ifade: ',i)
                    if i == "0" or i == "1" or i == "2" or i == "3" or i == "4" or i == "5" or i == "6" or i == "7" or i == "8" or i == "9":
                        no.append(i)
                    else:
                        ktp.append(i)
                Noo = ''.join(str(e) for e in no)
                kitapA = ''.join(str(e) for e in ktp)
                #print('Noo:',Noo)
                #print('**')
                #print('kitapA:',kitapA)
                kitapAdiTopla.append(kitapA)
                kitapNoTopla.append(Noo)
                #print('kitapAdiTopla:',kitapAdiTopla[sayac])
                #print('kitapNoTopla:',kitapNoTopla[sayac])
                Noo=''
                kitapA=''
                str2=''
                no=[]
                ktp = []
                
            #print(sya)
            for sayac in range(sya):
                print('Kitap Adi: ',kitapAdiTopla[sayac], ' Kitap No: ', kitapNoTopla[sayac])


            suankiUser = session['name']
            test = graph.run("MATCH (a) WHERE a.name={x} RETURN a.kapasite", x=suankiUser).data()
            usersNumberOfBooks = test[0]["a.kapasite"]  # Kapasiteyi veren kod

                
            
            # Kitap Adı ve ISBN numarası PARSE işlemlerinin sonu
#************************************************************************************************************
           
            
            if request.method == 'POST':

                suankiUser = session['name']
                test = graph.run("MATCH (a) WHERE a.name={x} RETURN a.kapasite", x=suankiUser).data()
                usersNumberOfBooks = test[0]["a.kapasite"]  # Kapasiteyi veren kod
                ceviir = int(usersNumberOfBooks)
                print('ceviir: ', ceviir)
                print(type(ceviir))
                
                if ceviir >= 0 and ceviir < 3:
                    #Kitapların tarihlerini aldık.
                    if ceviir == 0:
                        print('Bu birinci kitap olucak')

                        # Su anki zamanı bulmak icin zaman atladan gelen degeride ekle
                     
                        since = datetime.now()
                        print(since)
                        print(type(since))

                        # Zaman Atla Veritabanı Bilgisini çekiyoruz.

                        gunver= graph.run("MATCH (a:Time) RETURN a.time").evaluate()
                        toInt = int(gunver)
                        days = timedelta(days=toInt)
                        print('eklenecek gun sayisi: ', days)
                    
                        # Su anki ve eklenen tarih bilgileri ile son zaman bilgisi

                        birgunSonra = since + days
                        print(birgunSonra)
                    

                        de = birgunSonra.timetuple()
                        listeyeTopla=[]
                        saya=0
                        for i in de:
                            listeyeTopla.append(i)
                            saya+=1
                            if saya>5:
                                break
                                    
                        for j in listeyeTopla:
                            print(j)
                            print(type(j))

                        donenKitap = request.form['kitapAdi']
                        donenIsbn = request.form['isbnNo']
                        print(donenKitap,donenIsbn)
                        test = graph.run("MATCH (a) WHERE a.name={x} RETURN a.name", x=suankiUser)
                        print(type(test))
                        print(test)
                
                        aa = graph.nodes.match("Login", name=suankiUser).first()
                        bb = graph.nodes.match("Book", kitap_adi=donenKitap).first()   
                       
                        ab = Relationship(aa, "HAS", bb, yil=listeyeTopla[0], ay=listeyeTopla[1], 
                        gun=listeyeTopla[2], saat=listeyeTopla[3], dakika=listeyeTopla[4], saniye=listeyeTopla[5])
                        print(ab) 
                        suankiUser = session['name']
                        test = graph.run("MATCH (a) WHERE a.name={x} RETURN a.kapasite", x=suankiUser).data()
                        usersNumberOfBooks = test[0]["a.kapasite"]  # Kapasiteyi veren kod
                        ceviir = int(usersNumberOfBooks)
                        print('ceviir: ', ceviir)
                        ceviir+=1
                        print('yeni Cevir: ', ceviir)
                        
                            
                        graph.run("MATCH (n:Login) WHERE n.name={x} SET n.kapasite={y};", x=suankiUser,y=ceviir).evaluate()
                        graph.run("MATCH (b:Book) WHERE b.kitap_adi={x} SET b.stok=0;", x=donenKitap).evaluate()   
                        flash('Kitap basariyla alindi','success')       
                        graph.create(ab)
                        

                    else:
                        aKontrolu = graph.run("MATCH (n:Login)-[r:HAS]->(b:Book) WHERE n.name={x} RETURN r.yil;", x=suankiUser).data()
                        bKontrolu = graph.run("MATCH (n:Login)-[r:HAS]->(b:Book) WHERE n.name={x} RETURN r.ay;", x=suankiUser).data()
                        cKontrolu = graph.run("MATCH (n:Login)-[r:HAS]->(b:Book) WHERE n.name={x} RETURN r.gun;", x=suankiUser).data()
                        dKontrolu = graph.run("MATCH (n:Login)-[r:HAS]->(b:Book) WHERE n.name={x} RETURN r.saat;", x=suankiUser).data()
                        eKontrolu = graph.run("MATCH (n:Login)-[r:HAS]->(b:Book) WHERE n.name={x} RETURN r.dakika;", x=suankiUser).data()
                        fKontrolu = graph.run("MATCH (n:Login)-[r:HAS]->(b:Book) WHERE n.name={x} RETURN r.saniye;", x=suankiUser).data()
                        

                        print("aKontrolu: ", aKontrolu)
                        print("bKontrolu: ", bKontrolu)
                        print("cKontrolu: ", cKontrolu)
                        print("dKontrolu: ", dKontrolu)
                        print("eKontrolu: ", eKontrolu)
                        print("fKontrolu: ", fKontrolu)

                        
                        for i in range(0,ceviir):
                            print('Bu bir denemedir....  Sayi: ', i)
                            yilKontrolu = aKontrolu[i]["r.yil"]
                            ayKontrolu = bKontrolu[i]["r.ay"]
                            gunKontrolu = cKontrolu[i]["r.gun"]
                            saatKontrolu = dKontrolu[i]["r.saat"]
                            dakikaKontrolu = eKontrolu[i]["r.dakika"]
                            saniyeKontrolu = fKontrolu[i]["r.saniye"]

                            print("yilKontrolu: ", yilKontrolu)
                            print("ayKontrolu: ", ayKontrolu)
                            print("gunKontrolu: ", gunKontrolu)
                            print("saatKontrolu: ", saatKontrolu)
                            print("dakikaKontrolu: ", dakikaKontrolu)
                            print("saniyeKontrolu: ", saniyeKontrolu)

                            print('*************************')

                            # Alınan kitapların tarih bilgilerini aldım. Her for dönüşünde
                            # bir ilişkinin tarih bilgisini kontrol ediyoruz. 
                        
                    
                            # Su anki zamanı bulmak icin zaman atladan gelen degeride ekle
                     
                            since = datetime.now()
                            print(since)
                            print(type(since))

                            # Zaman Atla Veritabanı Bilgisini çekiyoruz.

                            gunver= graph.run("MATCH (a:Time) RETURN a.time").evaluate()
                            toInt = int(gunver)
                            days = timedelta(days=toInt)
                            print('eklenecek gun sayisi: ', days)
                    
                            # Su anki ve eklenen tarih bilgileri ile son zaman bilgisi

                            birgunSonra = since + days
                            print(birgunSonra)
                    

                            de = birgunSonra.timetuple()
                            listeyeTopla=[]
                            saya=0
                            for i in de:
                                listeyeTopla.append(i)
                                saya+=1
                                if saya>5:
                                    break
                                    
                            for j in listeyeTopla:
                                print(j)
                                print(type(j))
                            
                            if listeyeTopla[0]>yilKontrolu:
                                print('KİTABI GERİ VER !')
                                print('VERİTABANI İSLEMLERİNİ YAPMA')
                                flash('Sistemde teslim tarihi gecmis kitabiniz mevcut. Kitap almadan once onlari teslim ediniz','error')
                            else:
                                if listeyeTopla[1]>ayKontrolu:
                                    print('KİTABI GERİ VER !')
                                    print('VERİTABANI İSLEMLERİNİ YAPMA')
                                    flash('Sistemde teslim tarihi gecmis kitabiniz mevcut. Kitap almadan once onlari teslim ediniz','error')
                                else:
                                    if listeyeTopla[2]-gunKontrolu>=7:
                                        print('KİTABI GERİ VER !')
                                        print('VERİTABANI İSLEMLERİNİ YAPMA')
                                        flash('Sistemde teslim tarihi gecmis kitabiniz mevcut. Kitap almadan once onlari teslim ediniz','error')
                                    else:
                                        
                                        donenKitap = request.form['kitapAdi']
                                        donenIsbn = request.form['isbnNo']
                                        print(donenKitap,donenIsbn)
                                        test = graph.run("MATCH (a) WHERE a.name={x} RETURN a.name", x=suankiUser)
                                        print(type(test))
                                        print(test)
                
                                        aa = graph.nodes.match("Login", name=suankiUser).first()
                                        bb = graph.nodes.match("Book", kitap_adi=donenKitap).first()   
                       
                                        ab = Relationship(aa, "HAS", bb, yil=listeyeTopla[0], ay=listeyeTopla[1], 
                                        gun=listeyeTopla[2], saat=listeyeTopla[3], dakika=listeyeTopla[4], saniye=listeyeTopla[5])
                                        print(ab) 
                                        suankiUser = session['name']
                                        test = graph.run("MATCH (a) WHERE a.name={x} RETURN a.kapasite", x=suankiUser).data()
                                        usersNumberOfBooks = test[0]["a.kapasite"]  # Kapasiteyi veren kod
                                        ceviir = int(usersNumberOfBooks)
                                        print('ceviir: ', ceviir)
                                        ceviir+=1
                                        print('yeni Cevir: ', ceviir)
                                        if ceviir > 3:
                                            ceviir=3
                                            graph.run("MATCH (n:Login) WHERE n.name={x} SET n.kapasite={y};", x=suankiUser,y=ceviir).evaluate()
                                            graph.run("MATCH (b:Book) WHERE b.kitap_adi={x} SET b.stok=0;", x=donenKitap).evaluate()   
                                            flash('Kitap basariyla alindi','success')         
                                            graph.create(ab)
                                        else:
                                            graph.run("MATCH (n:Login) WHERE n.name={x} SET n.kapasite={y};", x=suankiUser,y=ceviir).evaluate()
                                            graph.run("MATCH (b:Book) WHERE b.kitap_adi={x} SET b.stok=0;", x=donenKitap).evaluate() 
                                            flash('Kitap basariyla alindi','success')           
                                            graph.create(ab)
                                        
                else:
                    flash('3\'ten fazla kitap alamazsiniz.','error')                        

            return render_template('kitapal.html', kitapAdiTopla=kitapAdiTopla, kitapNoTopla=kitapNoTopla,sya=sya, userr=userr)

@app.route('/kitapver', methods=['GET','POST'])
def kitapver():

    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return render_template('upload.html', msg='No file selected')
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            return render_template('upload.html', msg='No file selected')

        if file and allowed_file(file.filename):
            file.save(os.path.join(os.getcwd() + UPLOAD_FOLDER, file.filename))

            # call the OCR function on it
            extracted_text = ocr_core(file)
            listele = extracted_text.split()
            sayac = 0
            isbnNo = ''
            for i in listele:
                sayac+=1
                if i == "ISBN" or i == "ISBN:" or i == "ISBN: " or i=="lSBN" or i=="lSBN:":
                    isbnNo=listele[sayac]                
                    break
                
            a = isbnNo.split('—')
            bos = []
            for i in a:
                for j in i:
                   bos.append(j)

            array_length = len(bos)
            i=0
            yedek_bos = bos.copy()
            for i in range(array_length):
                if bos[i] == "9" or bos[i] == "8" or bos[i] == "7" or bos[i] == "6" or bos[i] == "5" or bos[i] == "4" or bos[i] == "3" or bos[i] == "2" or bos[i] == "1" or bos[i] == "0":
                    pass
                else:
                    sil = bos[i]
                    yedek_bos.remove(sil)
                i+=1

            parseISBN = "".join(yedek_bos)
            print("parseISBN: " , parseISBN)

            suankiUser = session['name']
            print('suankiUser: ',suankiUser)    


            kontrolKapasite =graph.run("MATCH (a:Login) WHERE a.name={x} RETURN a.kapasite ", x=suankiUser).evaluate()
            if kontrolKapasite == 0:
                flash('Daha onceden kitap almadiniz.','error')
            else:

                beforeRCount= graph.run("MATCH (p:Login { name: {y} } )-[r:HAS]-() RETURN count(r)", y=suankiUser).evaluate()
                donenSonuc= graph.run("MATCH (a:Login)-[r:HAS]->(b:Book {isbn:{y}}) DELETE r ", y=parseISBN).evaluate()
                afterRCount = graph.run("MATCH (p:Login { name: {y} } )-[r:HAS]-() RETURN count(r)", y=suankiUser).evaluate()

                # Eğer hiç kitap yoksa kontrol yaptır.

                if beforeRCount > afterRCount:
                    print('Kitap geri verildi.')
                    kapasiteSayisi =graph.run("MATCH (a:Login) WHERE a.name={x} RETURN a.kapasite ", x=suankiUser).evaluate()
                    print('Kapasite sayisi: ', kapasiteSayisi)
                    kapasiteSayisi-=1
                    print('Sonraki Kapasite sayisi: ', kapasiteSayisi)
                    graph.run("MATCH (a:Login) WHERE a.name={x} SET a.kapasite={y}",x=suankiUser,y=kapasiteSayisi).evaluate()
                    graph.run("MATCH (a:Book) WHERE a.isbn={x} SET a.stok=1",x=parseISBN,).evaluate()               
                    graph.run("MATCH (a:Login)-[r:HAS]->(b:Book {isbn:{y}}) DELETE r ", y=parseISBN).evaluate()
                    graph.run("MATCH (b:Book) REMOVE b.kategori").evaluate()
                    flash('Kitap sisteme basariyla geri verildi.','success')
                else:
                    print('Bu ISBN numaraları kitap kullanıcı üstünde degil.')
                    flash('Kitap kullanici ustunde degil.','error')
                print('beforeRCount: ',beforeRCount, ' afterRCount: ',afterRCount)
            


        
            # extract the text and display it

            return render_template('kitapverme.html',
                                   msg='Successfully processed',
                                   extracted_text=extracted_text,
                                   img_src=UPLOAD_FOLDER + file.filename)
    elif request.method == 'GET':
        return render_template('kitapverme.html')    

if __name__ == "__main__":
   app.debug = True
   app.run()
