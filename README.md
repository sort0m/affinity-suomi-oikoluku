# Suomen oikoluku Affinityyn (Voikko)

Tämä työkalu tarkistaa valittujen tekstikehysten suomenkielisen tekstin Voikolla
Affinityssä. Se näyttää korjausehdotukset ja tekee hyväksytyt korjaukset
asiakirjaan. Tarkistus käynnistyy vain, kun ajat Affinity-skriptin; se ei muuta
Affinityn omaa oikeinkirjoituksen tarkistusta.
Ohjelman nimi on **Affinity-oikoluku**; se käyttää Voikko-kirjastoa ja sanastoa.

## Lataa ja ota käyttöön Windowsissa

Valmis [Windows x64 -paketti 1.7](https://github.com/sort0m/affinity-suomi-oikoluku/releases/download/v1.7/Affinity-suomi-ilman-Python-asennusta-1.7.zip)
sisältää ohjelman ja sen tarvitsemat Voikko-tiedostot. Python-asennusta ei
tarvita. Työkalu on testattu Affinity 3.3.3:ssa; se tarvitsee Affinityn
skriptituen.

Lataa ohjelma yllä olevasta paketista. GitHubin Code-valikon ZIP sisältää
repositorion lähdetiedostot.

1. Lataa ZIP ja pura **koko sisältö** pysyvään kansioon, esimerkiksi Asiakirjat-
   kansioon. Säilytä `Affinity-oikoluku.exe` ja `_internal` samassa puretussa kansiossa.
2. Käynnistä `Affinity-oikoluku.exe`. Se luo omaan kansioonsa `Tarkista-suomi.js`-tiedoston.
3. Lisää syntynyt `Tarkista-suomi.js` Affinityn **Scripts Libraryyn** alla
   olevilla ohjeilla.
4. Valitse Affinityssä tekstikehys ja aja **Tarkista suomi (Voikko 1.6)**.

## Skriptin asentaminen Affinityyn

1. Avaa `Affinity-oikoluku.exe`-ohjelman viereen syntynyt **Tarkista-suomi.js** Muistiossa.
   Valitse koko sisältö näppäimillä **Ctrl+A** ja kopioi se **Ctrl+C**.
2. Avaa Affinityssä **Scripts Library** -paneeli. Jos se ei näy, valitse
   **Window > Scripting > Scripts Library**. Avaa paneelin oikean yläkulman
   valikko ja valitse **New Script**.
3. Napsauta tyhjää koodialuetta **Script Editor** -ikkunassa ja liitä kopioitu
   koodi näppäimillä **Ctrl+V**. Koodin alussa näkyy `version: 1.6.0`.
4. Paina **Ctrl+S** tai valitse editorin **Save As**. Anna nimeksi esimerkiksi
   **Tarkista suomi (Voikko 1.6)**, valitse kategoriaksi **Suosikit** ja paina
   **Save**. Skripti näkyy nyt Scripts Libraryn Suosikit-ryhmässä.
5. Avaa Script Editorin rataskuvake ja varmista, että **Script permissions >
   Network** on valittuna.
   Skripti ottaa yhteyden vain oman koneen osoitteeseen `127.0.0.1:17655`.

**Import Scripts** -valikko on Affinityn `.afscripts`-paketeille. Se ei avaa
`Tarkista-suomi.js`-tiedostoa. Jos kirjastossa on vanhoja Voikko-versioita,
valitse jatkossa nimellä **Tarkista suomi (Voikko 1.6)** tallennettu skripti.
Luotu JS-tiedosto sisältää tämän asennuksen paikallisen avaimen. Älä julkaise
tai lähetä sitä muille.

Voit pysäyttää ohjelman ilmaisinalueen kuvakkeesta tai paketin
`Pysayta-Affinity-oikoluku.cmd`-tiedostolla. Tarkemmat ohjeet ovat ZIPin
`LUE-ENSIN.txt`-tiedostossa.

**Lisää sanastoon** tallentaa käsiteltävän sanan pysyvästi käyttäjäsanastoon.
Tarkistin ei huomauta siitä enää myöhemmilläkään käynnistyskerroilla.

Ohjelma käyttää vain oman koneen osoitetta `127.0.0.1:17655`. Tarkistettavaa
tekstiä ei lähetetä verkkopalveluun. Tämä on sanojen oikolukua, ei
kielioppitarkistus.

Paketissa on lisäksi vapaaehtoinen `fi_FI/hyph_fi_FI.dic`-tavutustiedosto.
Tavutuksen oma projekti ja asennusohje ovat repositoriossa
[affinity-suomi-tavutus](https://github.com/sort0m/affinity-suomi-tavutus).
Oikoluku toimii ilman tavutustiedoston asentamista.

## Lähdekoodi ja rakentaminen

`voikko/affinity-voikko.js` on Affinity-skriptin lähde. Käynnistys luo siitä
asennuskohtaisen `Tarkista-suomi.js`-tiedoston. Python-palvelu on `voikko`-
kansiossa; Windows-ohjelman rakentaja on `tools/build_portable.py`.

Lähdekoodiversio tarvitsee 64-bittisen Pythonin (3.9 tai uudempi). Sen voi
käynnistää `Kaynnista-Affinity-oikoluku.cmd`-tiedostolla; ensimmäinen käynnistys lataa
Voikon kirjaston ja sanaston Voikon ylläpitäjän palvelimelta. Valmiin ZIPin
käyttö ei tee tätä latausta.

Windows-paketin rakentaminen lähdekoodista:

```text
python -m pip install pyinstaller==6.19.0
python voikko/setup.py
python tools/build_portable.py
```

Rakentaja tuottaa `Affinity-suomi-ilman-Python-asennusta-1.7.zip`-tiedoston.
Testit: `python -m unittest discover -s tests -v` ja
`node --test tests/test_voikko_script.cjs`.

`voikko/runtime/`, `voikko/Tarkista-suomi.js`, puretun ohjelman `data/`
ja puretun ohjelman `Tarkista-suomi.js` ovat asennuskohtaisia. Älä julkaise
niitä. Tässä repositoriossa oleva valmis ZIP on rakennettu ennen ensimmäistä
käynnistystä, eikä se sisällä näitä tiedostoja.

## Lisenssit ja lähteet

Tämän projektin lisenssi on [GNU GPL 3](LICENSE). [Lisenssi- ja
lähdekoodiluettelo](LISENSSIT-JA-LAHTEET.md) kertoo jokaisen pakettiin
sisältyvän pääosan alkuperän, lisenssin ja lähdekoodin sijainnin.
Valmiissa ZIPissä ovat myös käytettyjen Voikko-kirjaston ja sanaston
vastaavat lähdekoodipaketit. Tavutustiedoston pohja on
[Mika Vainion projektista](https://github.com/MikaVainio/AffinityPublisherFISpelling).
