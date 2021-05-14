import requests
from bs4 import BeautifulSoup as BS
import os
import xml.etree.ElementTree as ET
import ftplib
from datetime import datetime
import winsound
import time


# Соединяемся с FTP-сервером
host = ''  # хост
ftp_user = ''  # логин
ftp_password = ''  # пароль для входа

# после чего каждую переменную подключим к авторизации:
ftp = ftplib.FTP(host, ftp_user, ftp_password)
ftp.encoding = 'UTF-8'
welcome_text = ftp.getwelcome()
print(welcome_text)  # Вывели на экран Welcome-сообщение сервера
ftp.cwd('P/outbound/ORDERS')


# Модуль получения данных с айки
login = 'admin'
user_secret = ''
org_id = ''
urlserv = "" # 
auth_html = requests.get(urlserv + '/api/auth?login=' + login + '&pass=' + user_secret)
token = BS(auth_html.text, 'html.parser')
token = token.__str__().replace('"', '')
print('token = ', token)
f = open(os.getcwd() + '\\mats\\tokenlogs.txt', 'a', encoding='UTF-8')
f.write(str(token) + '\n')
f.close()
r = requests.get(urlserv + '/api/products?key=' + token)
f = open('products.xml', 'w', encoding='UTF-8')
f.write(r.text.replace('<containers/>', ''))
f.close()
r = requests.get(urlserv + '/api/corporation/stores?key=' + token)
f = open('stores.xml', 'w', encoding='UTF-8')
f.write(r.text)
f.close()
f = open('prodsort.xml', 'w', encoding='UTF-8')
f.write('<nomenklatures>')
tree = ET.parse('products.xml')
root = tree.getroot()
for member in root.iter('productDto'):
    name = member.find('name')
    nm = name.text.replace('&', '')
    productid = member.find('id')
    #f.write('<product><name>' + name.text + '</name><id>' + productid.text + '</id></product>')
    for membe in member.iter('barcodes'):
        for memb in membe.iter('barcodeContainer'):
            barcode = memb.find('barcode')
            f.write('<product><name>' + str(nm) + '</name><id>' + productid.text + '</id><barcode>' + barcode.text + '</barcode></product>')
f.write('</nomenklatures>')
f.close()

r = requests.get(urlserv + '/api/logout?key=' + token)
# парсер модуль
while True:
    auth_html = requests.get(urlserv + '/api/auth?login=' + login + '&pass=' + user_secret)
    key = BS(auth_html.text, 'html.parser')
    key = key.__str__().replace('"', '')
    print('token = ', key)
    f = open(os.getcwd() + '\\mats\\tokenlogs.txt', 'a', encoding='UTF-8')
    f.write(str(key) + '\n')
    f.close()
    # Создаем список файлов из исходного
    directory_file = 'data.txt'
    
    with open(directory_file) as f:
        list_iso = [row.strip() for row in f]
    print('Список файлов:', list_iso)
    
    # Создаем список файлов с сервера
    sub_directory_list = ftp.nlst()
    print('Список файлов на ftp:', sub_directory_list)
    # new_files = set(list_iso) ^ set(sub_directory_list)
    new_files = set(sub_directory_list) - set(list_iso)
    new_files = list(new_files)  # которые есть в фтп но нету в дате.
    print('В папке добавлены файлы:', new_files)
    if len(new_files) > 0:
        print('Изменения есть')
        directory_for_save_temp = directory_file
        try:
            os.mkdir(directory_file)
        except OSError:
            print("Успешно создан(ы) файл(ы) %s " % new_files)
        else:
            print("Создать файл(ы) %s не удалось" % new_files)
        for new_file in new_files:
            with open(directory_file, 'a') as local_file:
                local_file.write(new_file + '\n')
        for new_file in new_files:
            with open('mats/' + new_file, 'wb') as localfile:
                ftp.retrbinary('RETR ' + new_file, localfile.write)
            tree = ET.parse("mats/" + new_file)
            #tree = ET.parse("mats/test.xml")
            root = tree.getroot()

        for new_file in new_files:
            f = open('logs.txt', 'a', encoding='UTF-8')
            f.write(str(datetime.now()) + '\n' + new_file + '\n')
            f.close()
            f = open('outgoinginvoicedto.xml', 'w', encoding='utf-8')
            
            with open('mats/' + new_file, 'wb') as localfile:
                ftp.retrbinary('RETR ' + new_file, localfile.write)
            tree = ET.parse("mats/" + new_file)
            # tree = ET.parse("mats/test.xml")
            root = tree.getroot()
            for member in root.iter('DTM'):
                for membe in member.iter('C507'):
                    obj = membe.find('E2005')
                    if obj.text == '9':
                        date = membe.find('E2380')
                        date = datetime.strptime(date.text, '%Y%m%d%H%M%S')
                        #date = str(date).replace('-', '')
                        #date = str(date).replace(':', '')
                        date = str(date).replace(' ', 'T')
                        print(date)
            f.write(
                '<document><dateIncoming>' + date + '</dateIncoming><useDefaultDocumentTime>true</useDefaultDocumentTime><accountToCode>5.01</accountToCode><revenueAccountCode>4.01</revenueAccountCode>')

            for member in root.iter('NAD'):                                     # Город Адрес Кто поставщик
                # Перебор вторичных тегов
                obj = member.find('E3035')
                #print('obj.text = ', obj.text)
                if obj.text == str('BY'):                                       # Покупатель
                    gorod = member.find('E3164')
                    city = gorod.text
                    for mem in member.iter('C080'):
                        organizes = mem.find('E3036')
                        if organizes.text != None:
                            print('Организация заказчик -', organizes.text)
                            organiz = organizes.text
                            numzakaz = ' '
                            if 'АГРОТОРГ' in str(organizes.text):
                                f.write('<counteragentId>6132fc69-99fe-4024-b78e-fe57728093c7</counteragentId><conceptionId>73661650-2e32-4ac3-aa5a-84fbeb10400a</conceptionId><conceptionCode>5</conceptionCode>')
                                print('агроторг')
                            if 'ТХ Сибирский Гигант' in str(organizes.text):
                                f.write('<counteragentId>31a6291f-d075-466b-addd-4a89b8015768</counteragentId><conceptionId>73661650-2e32-4ac3-aa5a-84fbeb10400a</conceptionId><conceptionCode>5</conceptionCode>')
                                print('СибГига')
                            if 'АШАН' in str(organizes.text):
                                f.write('<counteragentId>ea45070b-58e8-44b1-b539-2b8bc14ee3f7</counteragentId><conceptionId>73661650-2e32-4ac3-aa5a-84fbeb10400a</conceptionId><conceptionCode>5</conceptionCode>')
                                print('АШАН')
                            if 'РОЗНИЦА К-1' in str(organizes.text):
                                f.write('<counteragentId>f7b734a3-12ca-4cdc-afa4-c0d03c17a02f</counteragentId><conceptionId>73661650-2e32-4ac3-aa5a-84fbeb10400a</conceptionId><conceptionCode>5</conceptionCode>')
                                print('Розница К-1')
                                for member in root.iter('BGM'):
                                    for membe in member.iter('C106'):
                                        nzak = membe.find('E1004')
                                        numzakaz = 'Заказ № ' + nzak.text
                if obj.text == str('DP'):                                       # Место доставки
                    obj = member.find('E3164')
                    print('Город места доставки -', obj.text)
                    goroddost = obj.text
                    for mem in member.iter('C059'):
                        obj = mem.find('E3042')
                        if obj.text != None:
                            print('Адрес места доставки -', obj.text)
                            adressdost = obj.text

                    for mem in member.iter('C080'):
                        obj = mem.find('E3036')
                        if obj.text != None:
                            orgdost = obj.text
                    for remember in root.iter('RFF'):
                        for remembe in remember.iter('C506'):
                            obj = remembe.find('E1153')
                            inn = remembe.find('E1154')
                            if obj.text == str('FC'):
                                print('ИНН -', inn.text)
                                memeinn = inn.text
                            if obj.text == str('XA'):
                                memekpp = inn.text

                    indexdot = member.find('E3251')
                    indexdost = indexdot.text

            for member in root.iter('SG3'):
                for membe in member.iter('RFF'):
                    for memb in membe.iter('C506'):
                        zxc = memb.find('E1153')
                        if zxc.text == str('FC'):
                            izn = memb.find('E1154')
                            inn = izn.text
                        if zxc.text == str('XA'):
                            kmb = memb.find('E1154')
                            kpp = kmb.text
            
            print(orgdost)
            if 'Пятерочка' in str(orgdost):
                f.write('<comment>TEST ' + organiz + ' ' + str(indexdost) + ' ' + goroddost + ' ' + str(adressdost) + ' №' + str(orgdost).split('-')[0] + '</comment><items>')
                            if 'Горожанка' in str(orgdost):
                f.write('<comment>TEST ' + organiz + ' ' + str(indexdost) + ' ' + goroddost + ' ' + str(adressdost) + ' Универсам Горожанка ')
                f.write('ИНН ' + str(memeinn) + ' КПП ' + str(memekpp) + '</comment><items>')
            if "РОЗНИЦА" in str(orgdost):
                f.write('<comment>TEST ' + organiz + '№' + str(orgdost).split('МАГАЗИН')[1] + ' ' + goroddost.split(' ')[1] + ' ' + goroddost.split(' ')[0] + ' ' + str(adressdost) + ' ' + numzakaz + '</comment><items>')
    
            if 'Мегас' in str(orgdost):
                f.write('<comment>TEST ' + organiz + ' ' + str(indexdost) + '-' + orgdost.split('-')[0] + ' №' +
                        orgdost.split('-')[1] + str(adressdost))
                f.write(' ИНН ' + str(memeinn) + ' КПП ' + str(memekpp) + '</comment><items>')
            if 'Гигант' in str(orgdost):
                f.write('<comment>TEST ' + organiz + ' ' + str(indexdost) + ' ' + str(adressdost))
                f.write(' ИНН ' + str(memeinn) + ' КПП ' + str(memekpp) + '</comment><items>')
            print('organizes.text', organizes.text)
            print ('organiz', str(organiz))
            print('indexdost', str(indexdost))
            print('orgdost', str(orgdost))
            print('adressdost', str(adressdost))
            print('memeinn', str(memeinn))
            print('memekpp', str(memekpp))
            for member in root.iter('SG28'):  # Номенклатура Товар
                for membe in member.iter('LIN'):
                    for memb in membe.iter('C212'):
                        obj = memb.find('E7140')
                        obz = obj.text
                        if obz in '231554':
                            obz = '4634444082597'
                    if obz != None:
                        print('Штрих-код продукта -', obz)
                        prodsorttree = ET.parse('prodsort.xml')
                        prodsortroot = prodsorttree.getroot()
                        for drmnbss in prodsortroot.iter('nomenklatures'):
                            for drmnbs in prodsortroot.iter('product'):
                                barcode = drmnbs.find('barcode')
                                if barcode != None:
                                    if obz == barcode.text:
                                        idprod = drmnbs.find('id')
                                        f.write('<item><productId>' + str(idprod.text) + '</productId>')
                                        f.write('<storeId>2220505d-8a16-4952-b8bd-ace558e71548</storeId>')
                                        for ndssum in member.iter('SG32'):
                                            for ndssu in ndssum.iter('PRI'):
                                                for ndss in ndssu.iter('C509'):
                                                    obj = ndss.find('E5125')
                                                    s = ndss.find('E5118')
                                                    if (obj.text == str('AAA')) and (s.text != None):
                                                        sumwithnds = float(s.text)*1.2
                                                        print('price -', s.text)
                                                        f.write('<price>' + str(sumwithnds) + '</price>')
                                                        price = float(sumwithnds)
                                        for kolvo in member.iter('QTY'):  # Заказанное количество номенклатуры
                                            for kolv in kolvo.iter('C186'):
                                                obj = kolv.find('E6063')
                                                if obj.text == str('21'):
                                                    obj = kolv.find('E6060')
                                                    f.write('<amount>' + obj.text + '</amount>')  #есть
                                                    print('Заказанное количество -', obj.text)
                                                    sumz = price * float(obj.text)
                                                    f.write('<sum>' + str(sumz) + '</sum><vatPercent>20</vatPercent><discountSum>0</discountSum></item>')
                                                amount = obj.text
                                        #sumz = price*float(obj.text)
                                        for summa in member.iter('SG32'):
                                            for summ in summa.iter('PRI'):
                                                for sum in summ.iter('C509'):
                                                    obj = sum.find('E5125')
                                                    s = sum.find('E5118')
                                                    #if (obj.text == str('AAA')) and (s.text != None):
                                                        #f.write('<sum>' + str(int(s.text) * int(price)) + '</sum><vatPercent>20</vatPercent></item>') #
            f.write('</items></document>')
            f.close()
            xml_file = "outgoinginvoicedto.xml"
            headers = {'Content-Type': 'application/xml; charset=ISO-8859-5'}
            with open(xml_file, encoding='ISO-8859-5') as data:
                print('data', data)
                r = requests.post(urlserv + '/api/documents/import/outgoingInvoice?key=' + key, headers=headers, data=data)
                f = open('logs.txt', 'a', encoding='utf-8')
                f.write(r.text + '\n')
                f.close()
                #print(r.text)
            winsound.Beep(500, 500)
        
    else:  
        print('Новых файлов не найдено')
        
    r = requests.get(urlserv + '/api/logout?key=' + key)
    print(r.text)
    time.sleep(10)
        
