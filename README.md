# Suomen oikoluku Affinityyn (Voikko)

Tämä työkalu tarkistaa valittujen tekstikehysten suomenkielisen tekstin Voikolla
Affinityssä. Se näyttää korjausehdotukset ja tekee hyväksytyt korjaukset
asiakirjaan. Tarkistus käynnistyy vain, kun ajat Affinity-skriptin; se ei muuta
Affinityn omaa oikeinkirjoituksen tarkistusta.
Ohjelman nimi on **Affinity-oikoluku**; se käyttää Voikko-kirjastoa ja sanastoa.

## Käyttö valmiilla EXE-paketilla Windowsissa

Valmis ohjelma on GitHubin [Releases-osiossa](https://github.com/sort0m/affinity-suomi-oikoluku/releases):
avaa julkaisu **v1.7** ja lataa **Assets**-kohdasta
[`Affinity-suomi-ilman-Python-asennusta-1.7.zip`](https://github.com/sort0m/affinity-suomi-oikoluku/releases/download/v1.7/Affinity-suomi-ilman-Python-asennusta-1.7.zip).
`Affinity-oikoluku.exe` on tämän ZIPin sisällä. Paketti sisältää myös tarvittavat
Voikko-tiedostot, joten Python-asennusta ei tarvita. Työkalu on testattu
Affinity 3.3.3:ssa; se tarvitsee Affinityn skriptituen.

GitHubin **Code > Download ZIP** lataa lähdekoodin, jossa EXEä ei ole.

1. Lataa ZIP ja pura **koko sisältö** pysyvään kansioon, esimerkiksi Asiakirjat-
   kansioon. Säilytä `Affinity-oikoluku.exe` ja `_internal` samassa puretussa kansiossa.
2. Käynnistä `Affinity-oikoluku.exe`. Se luo omaan kansioonsa `Tarkista-suomi.js`-tiedoston.
3. Lisää syntynyt `Tarkista-suomi.js` Affinityn **Scripts Libraryyn** alla
   olevilla ohjeilla.
4. Valitse Affinityssä tekstikehys ja aja **Tarkista suomi (Voikko 1.6)**.

## Käyttö lähdekoodista ilman EXEä

Lataa lähdekoodi GitHubin **Code > Download ZIP** -valinnalla tai kloonaa
repositorio. Tarvitset 64-bittisen Pythonin (3.9 tai uudempi).

1. Pura lähdekoodin ZIP ja avaa purettu kansio.
2. Kaksoisnapsauta `Kaynnista-Affinity-oikoluku.cmd`-tiedostoa. Ensimmäinen
   käynnistys lataa Voikon kirjaston ja sanaston Voikon ylläpitäjän palvelimelta.
3. Avaa käynnistyksen luoma `voikko/Tarkista-suomi.js` ja asenna se Affinityyn
   seuraavan osion ohjeella.
4. Valitse Affinityssä tekstikehys ja aja **Tarkista suomi (Voikko 1.6)**.

Lähdekoodista käynnistetty ohjelma pysäytetään
`Pysayta-Affinity-oikoluku.cmd`-tiedostolla.

## Jos Windows tai virustorjunta estää EXE:n käynnistyksen

Version 1.7 `Affinity-oikoluku.exe` ei ole digitaalisesti allekirjoitettu.

- **SmartScreen: Windows protected your PC.** Windows voi varoittaa
  tuntemattomasta sovelluksesta, jolla ei vielä ole riittävää latausmainetta.
  Lataa paketti tämän projektin GitHubin Releases-sivulta. SmartScreen voi
  tarjota **More info > Run anyway** -valinnan; käytä sitä vain, jos luotat
  lataamaasi julkaisuun. Työ- tai koulukoneen käytäntö voi estää jatkamisen.
- **Virustorjunta nimeää uhan tai siirtää tiedoston karanteeniin.** Ilmoita
  projektin ylläpitäjälle virustorjunnan nimi, koko hälytysteksti tai uhkan
  nimi, estetty tiedosto ja ohjelmapaketin versio. Havaintoa ei voi päätellä
  vääräksi hälytykseksi pelkän eston perusteella. Älä poista virustorjuntaa
  käytöstä tai lisää koko ohjelmakansiota poikkeuksiin ongelman ratkaisemiseksi.

[Microsoftin SmartScreen-ohje](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)
kertoo mainevaroituksista. Epäilty väärä Microsoft Defender -havainto
voidaan lähettää [Microsoftin analyysiin](https://www.microsoft.com/en-us/wdsi/filesubmission).
Allekirjoittaminen voi vähentää mainevaroituksia, mutta ei takaa niiden poistumista.

## Skriptin asentaminen Affinityyn

1. Avaa käynnistyksen luoma **Tarkista-suomi.js** Muistiossa. EXE-paketissa
   tiedosto on `Affinity-oikoluku.exe`-ohjelman vieressä, lähdekoodiversiossa
   `voikko`-kansiossa. Valitse koko sisältö näppäimillä **Ctrl+A** ja kopioi
   se **Ctrl+C**.
2. Avaa Affinityssä **Scripts Library** -paneeli. Jos se ei näy, valitse
   **Window > Scripting > Scripts Library**. Avaa paneelin oikean yläkulman
   valikko ja valitse **New Script**.
3. Napsauta tyhjää koodialuetta **Script Editor** -ikkunassa ja liitä kopioitu
   koodi näppäimillä **Ctrl+V**. Koodin alussa näkyy `version: 1.6.0`.
4. Tallenna skripti **Ctrl+S**-näppäimillä tai valitsemalla editorin **Save As**.
   Anna nimeksi esimerkiksi **Tarkista suomi (Voikko 1.6)**, valitse kategoriaksi
   **Default** ja paina **Save**. Skripti näkyy Scripts Libraryn Default-kategoriassa.
5. Avaa Script Editorin rataskuvake ja salli **Script permissions > Network**.
   Jos skriptin suoritus estyy virheeseen **Permission denied**, tarkista tämä
   asetus ja salli Network-oikeus. Skripti ottaa yhteyden vain oman koneen
   osoitteeseen `127.0.0.1:17655`.

**Import Scripts** -valikko on Affinityn `.afscripts`-paketeille. Se ei avaa
`Tarkista-suomi.js`-tiedostoa. Jos kirjastossa on vanhoja Voikko-versioita,
valitse jatkossa nimellä **Tarkista suomi (Voikko 1.6)** tallennettu skripti.
Luotu JS-tiedosto sisältää tämän asennuksen paikallisen avaimen. Älä julkaise
tai lähetä sitä muille.

EXE-paketin ohjelman voi pysäyttää ilmaisinalueen kuvakkeesta tai paketin
`Pysayta-Affinity-oikoluku.cmd`-tiedostolla. Paketin tarkemmat ohjeet ovat
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

Valmiin Releases-ZIPin käyttö ei lataa Voikko-tiedostoja verkosta.

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
niitä. Releases-osioon ladattava valmis ZIP on rakennettu ennen ensimmäistä
käynnistystä, eikä se sisällä näitä tiedostoja.

## Lisenssit ja lähteet

Tämän projektin lisenssi on [GNU GPL 3](LICENSE). [Lisenssi- ja
lähdekoodiluettelo](LISENSSIT-JA-LAHTEET.md) kertoo jokaisen pakettiin
sisältyvän pääosan alkuperän, lisenssin ja lähdekoodin sijainnin.
Valmiissa ZIPissä ovat myös käytettyjen Voikko-kirjaston ja sanaston
vastaavat lähdekoodipaketit. Tavutustiedoston pohja on
[Mika Vainion projektista](https://github.com/MikaVainio/AffinityPublisherFISpelling).
