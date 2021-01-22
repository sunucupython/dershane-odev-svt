from flask import Flask,jsonify,render_template,request,redirect,url_for,make_response
from flask_sqlalchemy import SQLAlchemy
import os
import json
from functools import wraps
import datetime
import binascii
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dershane.db'
db = SQLAlchemy(app)


class User(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    token  =  db.Column(db.String(24),nullable=True)
class SifresizGir(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    codex = db.Column(db.String(80), unique=True, nullable=False)
class Ogrenci(db.Model):
    no = db.Column(db.Integer, primary_key=True)
    fullName=db.Column(db.Text)
    tc=db.Column(db.Text)
    telNo=db.Column(db.Text)
    veliFullName=db.Column(db.Text)
    veliTelNo=db.Column(db.Text)
    borc=db.Column(db.Float)
    kayitTarih=db.Column(db.Text)
    adres=db.Column(db.Text)
class GelirKayitlari(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    taksitOdemesiMi=db.Column(db.Boolean)
    gelirTur=db.Column(db.Text)
    ogrNo = db.Column(db.Integer)
    gelir=db.Column(db.Float)
    gelirNot=db.Column(db.Text)
    kayitTarih=db.Column(db.Text)
class GiderKayitlari(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    giderTur=db.Column(db.Text)
    gider=db.Column(db.Float)
    giderNot=db.Column(db.Text)
    kayitTarih=db.Column(db.Text)
class GelirTurleri(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    gelirTurName=db.Column(db.Text)
    turAktif=db.Column(db.Boolean)
class GiderTurleri(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    giderTurName=db.Column(db.Text)
    turAktif=db.Column(db.Boolean)
class Istatistikler(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    toplamGelir=db.Column(db.Float)
    toplamGider=db.Column(db.Float)
    toplamOgrenci = db.Column(db.Integer)
def kimlikd(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            tokenx = request.cookies.get("session")
            if tokenx==None or tokenx=="0" or tokenx==0:
                return render_template("hata401.html"), 401
            k_bilgileri = User.query.filter_by(token=tokenx).first()
        
            if k_bilgileri==None:
                resp = make_response(redirect(url_for('hataci')))
                resp.set_cookie("session","0")
                return resp
             
            else:
                return f()
        except:
            return render_template("hata401.html"), 401
    return wrapper

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)



@app.route("/uyari")
def hataci():
    return render_template("hata401.html"), 401


@app.route("/")
@kimlikd
def index():
    IstatistiklerTablo=Istatistikler.query.get(1)
    return render_template("index.html",Istatistiklerx=IstatistiklerTablo)


@app.route("/index")
@kimlikd
def index2():
    return index()

@app.route("/ogrenciekle")
@kimlikd
def ogrenciekle():
    return render_template("ogrenciekle.html")
@app.route("/gelirekle")
@kimlikd
def gelirekle():
    GelirTurleriTablo=GelirTurleri.query.all()
    return render_template("gelirekle.html",GelirTurlerix=GelirTurleriTablo)
@app.route("/giderekle")
@kimlikd
def giderekle():
    GiderTurleriTablo=GiderTurleri.query.all()
    return render_template("giderekle.html",GiderTurlerix=GiderTurleriTablo)

@app.route("/api/ogrekle",methods=['POST'])
def ogrekle():
    try:
        veri=request.json
        tcVarmi=Ogrenci.query.filter_by(tc=veri["ogr_tc"]).first()
        if tcVarmi==None:
            db.session.add(Ogrenci(
            fullName=veri["ogr_adsoyad"],
            tc=veri["ogr_tc"],
            telNo=veri["ogr_tel"],
            veliFullName=veri["veli_adsoyad"],
            veliTelNo=veri["veli_tel"],
            borc=veri["odenecek_tutar"],
            kayitTarih=veri["kayit_tarih"],
            adres=veri["ogr_adres"]

            ))
            IstatistiklerTablo=Istatistikler.query.get(1)
            IstatistiklerTablo.toplamOgrenci += 1
            db.session.commit()
            donut = {"basarili":True}
            return jsonify(donut)
        else:
            donut = {"hata":True,"msg":"Bu TC.NO ile bir öğrenci daha önce kaydedilmiş"}
            return jsonify(donut)
    except Exception as e:
        print(e)
        donut = {"hata":True,"msg":"Hata"}
        return jsonify(donut)

@app.route("/api/ogrsil",methods=['POST'])
def ogrsil():
    try:
        veri=request.json
        tcVarmi=Ogrenci.query.filter_by(tc=veri["ogr_tc"]).first()
        if tcVarmi==None:
            donut = {"hata":True,"msg":"Bu TC.NO ile bir öğrenci bulunmadı"}
            return jsonify(donut)
        else:
            db.session.delete(tcVarmi)
            IstatistiklerTablo=Istatistikler.query.get(1)
            IstatistiklerTablo.toplamOgrenci -= 1
            db.session.commit()
            donut = {"basarili":True}
            return jsonify(donut)
    except Exception as e:
        print(e)
        donut = {"hata":True,"msg":"Hata"}
        return jsonify(donut)


@app.route("/api/ogrupdate",methods=['POST'])
def ogrupdate():
    try:
        veri=request.json
        Ogrencix=Ogrenci.query.filter_by(no=veri["id"]).first()
        if Ogrencix==None:
            donut = {"hata":True,"msg":"Bu NO ile bir öğrenci bulunmadı"}
            return jsonify(donut)
        else:
            Ogrencix.fullName=veri["ogr_adsoyad"]
            Ogrencix.tc=veri["ogr_tc"]
            Ogrencix.telNo=veri["ogr_tel"]
            Ogrencix.veliFullName=veri["veli_adsoyad"]
            Ogrencix.veliTelNo=veri["veli_tel"]
            Ogrencix.borc=veri["odenecek_tutar"]
            Ogrencix.kayitTarih=veri["kayit_tarih"]
            Ogrencix.adres=veri["ogr_adres"]
            db.session.commit()
            donut = {"basarili":True}
            return jsonify(donut)
    except Exception as e:
        print(e)
        donut = {"hata":True,"msg":"Hata"}
        return jsonify(donut)

@app.route("/api/glrekle",methods=['POST'])
def glrrekle():
    try:
        veri=request.json
        Ogrencix=Ogrenci.query.filter_by(no=veri["ogrno"]).first()
        if Ogrencix==None:
            donut = {"hata":True,"msg":"Bu OGRENCİ.NO ile bir öğrenci bulunmadı"}
            return jsonify(donut)
        else:
            if(veri["isTaksitOdemesi"]==True and Ogrencix.borc<=0):
                donut = {"hata":True,"msg":"Öğrencinin borcu bulunmadığı için taksit ödemesi eklenemedi!"}
                return jsonify(donut)
            elif(veri["isTaksitOdemesi"]==True and Ogrencix.borc>0) :
                Ogrencix.borc-=float(veri["gelir_lira"])
            db.session.add(GelirKayitlari(gelirTur=veri["gelir_tur"],
            taksitOdemesiMi=veri["isTaksitOdemesi"],
            ogrNo=veri["ogrno"],
            gelir=veri["gelir_lira"],
            gelirNot=veri["gelir_not"],
            kayitTarih=veri["gelir_tarih"]))
            IstatistiklerTablo=Istatistikler.query.get(1)
            IstatistiklerTablo.toplamGelir+=float(veri["gelir_lira"])
            db.session.commit()
            donut = {"basarili":True}
            return jsonify(donut)
    except Exception as e:
        print(e)
        donut = {"hata":True,"msg":"Hata"}
        return jsonify(donut)

@app.route("/api/glrsil",methods=['POST'])
def glrsil():
    try:
        veri=request.json
        GelirVarmi=GelirKayitlari.query.filter_by(idx=veri["gelirID"]).first()
        if GelirVarmi==None:
            donut = {"hata":True,"msg":"Bu ID ile bir Gelir Kaydı bulunmadı"}
            return jsonify(donut)
        else:
            IstatistiklerTablo=Istatistikler.query.get(1)
            IstatistiklerTablo.toplamGelir -= GelirVarmi.gelir
            db.session.delete(GelirVarmi)
            db.session.commit()
            donut = {"basarili":True}
            return jsonify(donut)
    except Exception as e:
        print(e)
        donut = {"hata":True,"msg":"Hata"}
        return jsonify(donut)

@app.route("/api/glrupdate",methods=['POST'])
def glrupdate():
    try:
        veri=request.json
        GelirVarmi=GelirKayitlari.query.filter_by(idx=veri["gelirID"]).first()
        if GelirVarmi==None:
            donut = {"hata":True,"msg":"Bu ID ile bir Gelir Kaydı bulunmadı"}
            return jsonify(donut)
        else:
            OGRVarmi=Ogrenci.query.filter_by(no=veri["ogrno"]).first()
            if OGRVarmi==None:
                donut = {"hata":True,"msg":"Bu OGRENCİ.NO ile bir öğrenci bulunamadı"}
                return jsonify(donut)
            if(veri["isTaksitOdemesi"]==True and GelirVarmi.taksitOdemesiMi==False):
                #normal gelir taksit ödemesine çevrileecek
                if OGRVarmi.borc<=0:
                    donut = {"hata":True,"msg":"Öğrencinin borcu bulunmadığı için taksit ödemesi eklenemedi!"}
                    return jsonify(donut)
                else:
                     OGRVarmi.borc-=float(veri["gelir_lira"])
            elif(veri["isTaksitOdemesi"]==False and GelirVarmi.taksitOdemesiMi==True):
                OGRVarmi.borc+=float(veri["gelir_lira"])
            IstatistiklerTablo=Istatistikler.query.get(1)
            IstatistiklerTablo.toplamGelir-= GelirVarmi.gelir
            GelirVarmi.gelirTur=veri["gelir_tur"]
            GelirVarmi.taksitOdemesiMi = veri["isTaksitOdemesi"]
            GelirVarmi.ogrNo=veri["ogrno"]
            GelirVarmi.gelir=veri["gelir_lira"]
            GelirVarmi.gelirNot=veri["gelir_not"]
            GelirVarmi.kayitTarih=veri["gelir_tarih"]
            IstatistiklerTablo.toplamGelir+= float(veri["gelir_lira"])
            db.session.commit()
            donut = {"basarili":True}
            return jsonify(donut)
    except Exception as e:
        print(e)
        donut = {"hata":True,"msg":"Hata"}
        return jsonify(donut)


@app.route("/api/gdrekle",methods=['POST'])
def gdrekle():
    try:
        veri=request.json
        db.session.add(GiderKayitlari(
        giderTur=veri["gider_tur"],
        gider=veri["gider_lira"],
        giderNot=veri["gider_not"],
        kayitTarih=veri["gider_tarih"]))
        IstatistiklerTablo=Istatistikler.query.get(1)
        IstatistiklerTablo.toplamGider+=float(veri["gider_lira"])
        db.session.commit()
        donut = {"basarili":True}
        return jsonify(donut)
    except Exception as e:
        print(e)
        donut = {"hata":True,"msg":"Hata"}
        return jsonify(donut)
@app.route("/api/gdrsil",methods=['POST'])
def gdrsil():
    try:
        veri=request.json
        GidervarMi=GiderKayitlari.query.filter_by(idx=veri["giderID"]).first()
        if GidervarMi==None:
            donut = {"hata":True,"msg":"Bu ID ile bir Gider Kaydı bulunamadı"}
            return jsonify(donut)
        else:
            IstatistiklerTablo=Istatistikler.query.get(1)
            IstatistiklerTablo.toplamGider -= GidervarMi.gider
            db.session.delete(GidervarMi)
            db.session.commit()
            donut = {"basarili":True}
            return jsonify(donut)
    except Exception as e:
        print(e)
        donut = {"hata":True,"msg":"Hata"}
        return jsonify(donut)
@app.route("/api/gdrupdate",methods=['POST'])
def gdrupdate():
    try:
        veri=request.json
        GidervarMi=GiderKayitlari.query.filter_by(idx=veri["giderID"]).first()
        if GidervarMi==None:
            donut = {"hata":True,"msg":"Bu ID ile bir Gider Kaydı bulunamadı"}
            return jsonify(donut)
        else:
            IstatistiklerTablo=Istatistikler.query.get(1)
            IstatistiklerTablo.toplamGider-= GidervarMi.gider
            GidervarMi.giderTur=veri["gider_tur"]
            GidervarMi.gider=veri["gider_lira"]
            GidervarMi.giderNot=veri["gider_not"]
            GidervarMi.kayitTarih=veri["gider_tarih"]
            IstatistiklerTablo.toplamGider+= float(veri["gider_lira"])
            db.session.commit()
            donut = {"basarili":True}
            return jsonify(donut)
    except Exception as e:
        print(e)
        donut = {"hata":True,"msg":"Hata"}
        return jsonify(donut)


@app.route("/api/getborcsuz")
def getborcsuz():
    try:
        ogrenciler  = Ogrenci.query.all()
        veri=[]
        for i in ogrenciler:
            if i.borc<=0:
                veri.append({"no":i.no,"isim":i.fullName,"borc":i.borc})
        return jsonify(veri)
    except Exception as e:
        print(e)
        donut = {"hata":True,"msg":"Hata"}
        return jsonify(donut)

@app.route("/api/getborclu")
def getborclu():
    try:
        ogrenciler  = Ogrenci.query.all()
        veri=[]
        for i in ogrenciler:
            if i.borc>0:
                veri.append({"no":i.no,"isim":i.fullName,"borc":i.borc})
        return jsonify(veri)
    except Exception as e:
        print(e)
        donut = {"hata":True,"msg":"Hata"}
        return jsonify(donut)


@app.route("/ogrenciler")
@kimlikd
def ogrenciler():
    Ogrencix = Ogrenci.query.all()
    return render_template("ogrenciler.html",Ogrenciler=Ogrencix)
@app.route("/gelirler")
@kimlikd
def gelirler():
    Gelirlerx = GelirKayitlari.query.all()
    return render_template("gelirler.html",Gelirler=Gelirlerx)
@app.route("/giderler")
@kimlikd
def giderler():
    Giderlerx = GiderKayitlari.query.all()
    return render_template("giderler.html",Giderler=Giderlerx)
@app.route("/raporlar")
@kimlikd
def raporlar():
    return render_template("raporlar.html")



@app.route("/sifresiz")
def sifresiz():
    try:
        hashCode = request.args.get("hash")
        if hashCode==None:
            donut = {"hata":True,"msg":"Hash kodu None"}
            return jsonify(donut)

        Sifresizx = SifresizGir.query.filter_by(codex=hashCode).first()
        if Sifresizx==None:
            donut = {"hata":True,"msg":"hatali hash"}
            return jsonify(donut)
        else:
            k_bilgileri = User.query.filter_by(username=Sifresizx.username).first()
            if k_bilgileri==None:
                donut = {"hata":True,"msg":"Bu hashla kullanici yok"}
                return jsonify(donut)
            else:
                resp = make_response(redirect(url_for('index')))
                resp.set_cookie("session",k_bilgileri.token)
                return resp
    except:
        donut = {"hata":True}
        return jsonify(donut)


@app.route("/cikis")
def cikis():
    try:
        resp = make_response(redirect(url_for('index')))
        resp.set_cookie("session","0")
        return resp
    except:
        donut = {"hata":True}
        return jsonify(donut)



if __name__=="__main__":
    app.run(debug=True,port=80)
